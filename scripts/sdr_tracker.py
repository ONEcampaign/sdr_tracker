# -*- coding: utf-8 -*-
"""
Created on Fri Dec  3 10:30:41 2021

@author: LucaPicci
"""

from scripts import config, utils
import pandas as pd
import numpy as np


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



def create_sdr() -> None:
    """
    creates a csv for flourish map
    """
    map_template = pd.read_csv(f'{config.paths.glossaries}/map_template.csv')
    sdr_df = read_sheet(0)
    sources_df = read_sheet(1174650744)

    df = pd.merge(map_template, sdr_df, how='left', on='iso_code')
    df = _add_source_html(df, sources_df)

    df['sdrs_received_usd'] = utils.clean_numeric_column(df['sdrs_received_usd'])

    df = utils.add_pct_gdp(df, columns=['sdrs_received_usd'],
                           gdp_year=2021, weo_year=2021, weo_release=2)

    df.to_csv(f'{config.paths.output}/sdr.csv',
              index=False)

    return df



if __name__ == '__main__':

    # create map template for Africa
    #map_template.africa_map_template()

    # create flourish csv
    create_sdr()
    print('successfully created map')