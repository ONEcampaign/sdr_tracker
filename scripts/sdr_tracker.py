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
    g = pd.read_json(config.paths.glossaries + r'/flourish_geometries_world.json')
    g.columns = ['geo', 'iso_code']
    g = g.iloc[1:]
    g = g.drop_duplicates(subset=['iso_code'], keep='first')
    g = g.set_index('iso_code').T.to_dict('records')[0]
    df = (pd.DataFrame({'iso_code': g.keys()})
          .assign(flourish_geom=lambda d: d.iso_code.map(g)))

    return df

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
#HSA_XDR - SDR allocation
#HSA_USD
#RAFASDR_XDR - SDR Holding

def _clean_holdings(df:pd.DataFrame, indicator, title):
    ''' '''
    df['REF_AREA'] = coco.convert(df['REF_AREA'])
    df = df[['TIME_PERIOD', 'OBS_VALUE', 'REF_AREA']]
    df = df.pivot(index='REF_AREA', columns = 'TIME_PERIOD', values = 'OBS_VALUE')
    df.columns = df.columns + f'_{title}'
    df = df.reset_index(drop=False)
    df.rename(columns = {'REF_AREA':'iso_code'}, inplace=True)
    
    return df

def get_holdings(indicator, title, year_month:Optional[str] = None):
    ''' '''
    
    africa = utils.country_df(columns = ['ISO3', 'ISO2', 'continent'])
    africa = africa[africa.continent == 'Africa']
    africa.loc[africa.iso_code == 'NAM', 'ISO2'] = 'NA'
    africa = africa.dropna(subset = ['ISO2'])
    
    df = imf.get_imf_indicator(country_list = list(africa.ISO2),
                          database = 'IFS',
                          frequency = 'M',
                          indicator = indicator)
    
    if year_month is None:
        df = df.loc[df.TIME_PERIOD == df.TIME_PERIOD.max()]
    else:
        df = df.loc[df.TIME_PERIOD == year_month]
        
    df = _clean_holdings(df, indicator, title)
    
        
    return df


    





# ============================================================================
# Map Build
# ============================================================================

def read_sheet(grid_number: int) -> pd.DataFrame:
    """
    """
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
            iso_string = '<p><strong>Sources</strong></p>'
            for i in sources[sources.iso_code == iso].index:
                source = sources.loc[i, 'sources']
                link = sources.loc[i, 'link']
                iso_string += f'<p><a href="{link}" target="_blank">{source}</a></p>'
            sdr_df.loc[sdr_df.iso_code == iso, 'source_html'] = iso_string

    return sdr_df


def popup_html(sdr_df:pd.DataFrame) -> pd.DataFrame:
    """
    """
    pass




def create_sdr_map() -> None:
    """
    creates a csv for flourish map
    """
    map_template = pd.read_csv(f'{config.paths.glossaries}/map_template.csv')
    sdr_df = read_sheet(0)
    sources_df = read_sheet(1174650744)

    df = pd.merge(map_template, sdr_df, how='left', on='iso_code')
    df = _add_source_html(df, sources_df)

    df['sdrs_allocation_aug_23_usd'] = utils.clean_numeric_column(df['sdrs_allocation_aug_23_usd'])


    df = utils.add_pct_gdp(df, columns=['sdrs_allocation_aug_23_usd'],
                           gdp_year=2021, weo_year=2021, weo_release=2)
    
    
    #add holdings
    cumulative_allocation_sdr = get_holdings('HSA_XDR', 'sdr_allocation_sdr_millions')
    df = pd.merge(df, cumulative_allocation_sdr, how='left', on = 'iso_code')
    
    cumulative_allocation_usd = get_holdings('HSA_USD', 'sdr_allocation_usd_millions')
    df = pd.merge(df, cumulative_allocation_usd, how='left', on = 'iso_code')
    
    sdr_holding_sdr = get_holdings('RAFASDR_XDR', 'sdr_holdings_sdr_millions')
    df = pd.merge(df, sdr_holding_sdr, how='left', on = 'iso_code')
    
    sdr_holding_usd = get_holdings('RAFASDR_USD', 'sdr_holdings_usd_millions')
    df = pd.merge(df, sdr_holding_usd, how='left', on = 'iso_code')
    
    
   
    
    df.to_csv(f'{config.paths.output}/sdr.csv',
              index=False)






    
    
    




if __name__ == '__main__':
    pass

    # create map template for Africa
    africa_map_template()

    # create flourish csv
    create_sdr_map()
    print('successfully created map')