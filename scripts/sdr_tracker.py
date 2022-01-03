# -*- coding: utf-8 -*-
"""
Created on Fri Dec  3 10:30:41 2021

@author: LucaPicci
"""

from scripts import config, utils, imf
import pandas as pd
import numpy as np
import pandas as pd
import country_converter as coco
from typing import Optional


# ============================================================================
# Map Template
# ============================================================================

def __geometry_df() -> pd.DataFrame:
    """
    return a dataframe with iso_code and flourish geometries
    """
    # Read in the geometries
    g = pd.read_json(config.paths.glossaries + r'/flourish_geometries_world.json')

    return (g
          .rename(columns={g.columns[0]:'flourish_geom',g.columns[1]:'iso_code'})
          .iloc[1:]
          .drop_duplicates(subset='iso_code', keep='first')
          .filter(['iso_code', 'flourish_geom'], axis=1)
          .reset_index(drop=True)
          )



def _flourish_map_df(slice_on_column: Optional[str] = None,
                     slice_by_values: Optional[list] = None) -> pd.DataFrame:
    """
    creates a fourish map dataframe template
    with country name(s) and geometries

        slice_on_column: specify the column to slice
        slice_by_values: specify the values to slice by
    """
    df = pd.merge(__geometry_df(), utils.country_df(),
                  how='left', on='iso_code')

    if (slice_on_column is not None) & (slice_by_values is not None):
        df = df[df[slice_on_column].isin(slice_by_values)]
    elif (slice_on_column is None) & (slice_by_values is not None):
        raise ValueError('Both parameters must be None or not None')
    elif (slice_on_column is not None) & (slice_by_values is not None):
        raise ValueError('Both parameters must be None or not None')
    else:
        pass

    return df


def africa_map_template() -> None:
    """
    Creates template for a flourish map of Africa
    with country name and geometry
        output as dataframe saved to glossaries
    """
    template = (_flourish_map_df(slice_on_column='continent',
                                 slice_by_values=['Africa'])
                .drop(columns='continent'))
    template.to_csv(f'{config.paths.glossaries}/map_template.csv',
                    index=False)


# ============================================================================
# Get SDR Holdings and allocation from IMF
# ============================================================================

def __clean_holdings(df: pd.DataFrame, title):
    '''cleans a dataframe for holding/allocation indicator'''
    df['REF_AREA'] = coco.convert(df['REF_AREA'])
    df = df[['TIME_PERIOD', 'OBS_VALUE', 'REF_AREA']]
    date = df.TIME_PERIOD.unique()[0]
    df = df.pivot(index='REF_AREA', columns='TIME_PERIOD', values='OBS_VALUE')
    df = df.reset_index(drop=False)
    df.rename(columns={'REF_AREA': 'iso_code', f'{date}': title}, inplace=True)
    df[f'{title}_date'] = date
    df[title] = pd.to_numeric(df[title])

    return df


def _get_holdings(indicator, title, year_month: Optional[str] = None):
    '''
    retrieves holdings/allocation indicator from the IMF
        year_month - specify year and month to pull 
                    If none, the latest date will be taken
        title - specify the title of the indicator (used as column title)
        indicator - code of IMF indicator
    '''

    africa = utils.country_df(columns=['ISO3', 'ISO2', 'continent'])
    africa = africa[africa.continent == 'Africa']
    africa.loc[africa.iso_code == 'NAM', 'ISO2'] = 'NA'
    africa = africa.dropna(subset=['ISO2'])

    df = imf.get_imf_indicator(country_list=list(africa.ISO2),
                               database='IFS',
                               frequency='M',
                               indicator=indicator,
                               start_period = '2021-08')

    if year_month is None:
        df = df.loc[df.TIME_PERIOD == df.TIME_PERIOD.max()]
    else:
        df = df.loc[df.TIME_PERIOD == year_month]
    df = __clean_holdings(df, title)

    return df


def add_holdings_allocation(df: pd.DataFrame) -> pd.DataFrame:
    """Adds holdings and allocations to the dataframe"""
    cumulative_allocation_sdr = _get_holdings('HSA_XDR', 'sdr_allocation_sdr_millions')
    df = pd.merge(df, cumulative_allocation_sdr, how='left', on='iso_code')

    cumulative_allocation_usd = _get_holdings('HSA_USD', 'sdr_allocation_usd_millions')
    df = pd.merge(df, cumulative_allocation_usd, how='left', on='iso_code')

    sdr_holding_sdr = _get_holdings('RAFASDR_XDR', 'sdr_holdings_sdr_millions')
    df = pd.merge(df, sdr_holding_sdr, how='left', on='iso_code')

    sdr_holding_usd = _get_holdings('RAFASDR_USD', 'sdr_holdings_usd_millions')
    df = pd.merge(df, sdr_holding_usd, how='left', on='iso_code')
    
    #% GDP columns
    df = utils.add_pct_gdp(df, columns=['sdr_allocation_usd_millions',
                                        'sdr_holdings_usd_millions'],
                           gdp_year=2021, weo_year=2021, weo_release=2)
    df.rename(columns = {'sdr_allocation_usd_millions_pct_gdp': 'sdr_allocation_pct_gdp',
                         'sdr_holdings_usd_millions_pct_gdp': 'sdr_holdings_pct_gdp'},
              inplace=True)
    

    return df


# ============================================================================
# Map Build
# ============================================================================

def read_sheet(grid_number: int) -> pd.DataFrame:
    """ Reads a google sheet to a dataframe"""
    
    url = ('https://docs.google.com/spreadsheets/d/e/2PACX-1vQZWRGU2EljGEXRFhjGYLq8s2YnxMGQsk3aNfC3I'
           '_-yuFPJaec7aSZCUxPnTe3hlOW4o4JtBtPLFbhu/pub?'f'gid={grid_number}&single=true&output=csv')
    try:
        return pd.read_csv(url)
    except:
        raise ConnectionError('Could not read sheet')




def _add_source_html(sdr_df: pd.DataFrame, sources: pd.DataFrame) -> pd.DataFrame:
    """
    creates an html string for sources and adds it to a dataframe
    """
    sdr_df['source_html'] = np.nan
    for iso in sources.iso_code.unique():
        if len(sources[sources.iso_code == iso]) > 0:
            iso_string = '<p><strong>References</strong></p><br>'
            for i in sources[sources.iso_code == iso].index:
                source = sources.loc[i, 'sources']
                link = sources.loc[i, 'link']
                iso_string += f'<p><a href="{link}" target="_blank">{source}</a></p>'
            sdr_df.loc[sdr_df.iso_code == iso, 'source_html'] = iso_string

    return sdr_df


def _add_sdr_table(df: pd.DataFrame) -> pd.DataFrame:
    """Creates an HTML string for SDR holdings and allocation"""

    df['sdr_table'] = np.nan
    for i in df.index:
        allocation_aug_usd = round((df.loc[i, 'sdrs_allocation_aug_23_usd']), 2)
        allocation_aug_sdr = round((df.loc[i, 'sdrs_allocation_aug_23_sdr']), 2)
        allocation_aug_gdp = round(df.loc[i, 'sdrs_allocation_aug_23_pct_gdp'], 2)
        allocation_aug_html = f'<tr><td>SDR allocations on August 23, 2021</td><td>{allocation_aug_usd}</td><td>{allocation_aug_sdr}</td><td>{allocation_aug_gdp}</td></tr>'
        
        allocation_usd = round(df.loc[i, 'sdr_allocation_usd_millions'], 2)
        allocation_sdr = round(df.loc[i, 'sdr_allocation_sdr_millions'], 2)
        allocation_date = df.loc[i, 'sdr_allocation_usd_millions_date']
        allocation_gdp = round(df.loc[i, 'sdr_allocation_pct_gdp'], 2)
        allocation_html = f'<tr><td>SDR allocations as of {allocation_date}</td><td>{allocation_usd}</td><td>{allocation_sdr}</td><td>{allocation_gdp}</td></tr>'
        
        holdings_usd = round(df.loc[i, 'sdr_holdings_usd_millions'], 2)
        holdings_sdr = round(df.loc[i, 'sdr_holdings_sdr_millions'], 2)
        holdings_date = df.loc[i, 'sdr_holdings_sdr_millions_date']
        holdings_gdp = round(df.loc[i, 'sdr_holdings_pct_gdp'], 2)
        holding_html = f'<tr><td>SDR holdings as of {holdings_date}</td><td>{holdings_usd}</td><td>{holdings_sdr}</td><td>{holdings_gdp}</td></tr>'

        table = f'<table><tr><th></th><th>USD millions</th><th>SDR millions</th><th>SDR as % of GDP</th></tr>{allocation_aug_html}{allocation_html}{holding_html} </table>'
        df.loc[i, 'sdr_table'] = table

    return df

def _add_popup_html(df: pd.DataFrame) -> pd.DataFrame:
    """Creates an HTML string for popups"""
    
    df['popup_html'] = np.nan
    for i in df.index:
        allocation = round(df.loc[i, 'sdr_allocation_usd_millions'], 2)
        holding = round(df.loc[i, 'sdr_holdings_usd_millions'], 2)
        date = df.loc[i, 'sdr_holdings_sdr_millions_date']
        
        popup = f'<p>SDR allocations: {allocation} USD millions</p><p>SDR holdings: {holding} USD millions</p><p> as of {date}</p>'
        df.loc[i, 'popup_html'] = popup
        
    return df
        

@utils.time_script
def create_sdr_map() -> None:
    """
    creates a csv for flourish map
    """
    #get files
    map_template = pd.read_csv(f'{config.paths.glossaries}/map_template.csv')
    sdr_df = read_sheet(0)
    sources_df = read_sheet(1174650744)

    #merge sdr from google with map template
    df = pd.merge(map_template, sdr_df, how='left', on='iso_code')
    df['sdrs_allocation_aug_23_usd'] = utils.clean_numeric_column(df['sdrs_allocation_aug_23_usd'])/1000000
    df['sdrs_allocation_aug_23_sdr'] = utils.clean_numeric_column(df['sdrs_allocation_aug_23_sdr'])/1000000
    df = df.dropna(subset=['country'])
    
    #add pct_gdp columns
    df = utils.add_pct_gdp(df, columns=['sdrs_allocation_aug_23_usd'],
                           gdp_year=2021, weo_year=2021, weo_release=2)
    df.rename(columns = {'sdrs_allocation_aug_23_usd_pct_gdp': 'sdrs_allocation_aug_23_pct_gdp'},
              inplace=True)
    
    #add holdings and allocation
    df = add_holdings_allocation(df)
    
    #add html for popups and panels
    df = _add_sdr_table(df)
    df = _add_source_html(df, sources_df)
    df = _add_popup_html(df)
    
    #export
    df = df[['iso_code', 'flourish_geom', 'region', 'country', 'text', 
             'sdr_holdings_pct_gdp', 'sdr_holdings_sdr_millions',
             'sdr_allocation_sdr_millions',
             'sdr_allocation_pct_gdp', 'sdr_table', 'source_html', 'popup_html']]
    df.to_csv(f'{config.paths.output}/sdr.csv',
              index=False)
    print('successfully created map')

if __name__ == '__main__':
    
    # create map template for Africa
    africa_map_template()

    # create flourish csv
    create_sdr_map()
    
