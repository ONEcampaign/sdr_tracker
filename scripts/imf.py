# -*- coding: utf-8 -*-
"""
Created on Fri Dec 17 11:40:41 2021

@author: LucaPicci
"""

import requests
from typing import Optional, Union
import pandas as pd
from scripts import config
import weo

# ============================================================================
# WEO tools
# ============================================================================


def _download_weo(year: int,
                  release: int) -> None:
    """Downloads WEO as a csv to glossaries folder as "weo_month_year.csv"""

    try:
        weo.download(year=year,
                     release=release,
                     directory=config.paths.glossaries,
                     filename=f"weo_{year}_{release}.csv")
    except:
        raise ConnectionError('Could not download weo data')


def _clean_weo(df: pd.DataFrame) -> pd.DataFrame:
    """cleans and formats weo dataframe"""

    columns = names = {'ISO': 'iso_code',
                       'WEO Subject Code': 'indicator',
                       'Subject Descriptor': 'indicator_name',
                       'Units': 'units',
                       'Scale': 'scale'}
    cols_to_drop = ['WEO Country Code', 'Country',
                    'Subject Notes', 'Country/Series-specific Notes',
                    'Estimates Start After']
    df = (df
          .drop(cols_to_drop, axis=1)
          .rename(columns=columns)
          .melt(id_vars=names.values(), var_name='year', value_name='value')
          )
    df.value = df.value.map(lambda x: (str(x)
                                       .strip()
                                       .replace(',', '')
                                       .replace('--', '')
                                       ))
    df.year = pd.to_numeric(df.year)
    df.value = pd.to_numeric(df.value, errors='coerce')

    return df


def get_gdp(gdp_year:int,
            weo_year: int,
            weo_release: int) -> pd.DataFrame:
    """
    Retrieves gdp value for a specific year
    """

    _download_weo(year=weo_year, release=weo_release)
    df = weo.WEO(f"{config.paths.glossaries}/weo_{weo_year}_{weo_release}.csv").df
    df = _clean_weo(df)
    df = df[(df.indicator == 'NGDPD')&(df.year == gdp_year)][['iso_code', 'value']]
    df.value = df.value*1000000000
    df.rename(columns = {'value':'gdp'}, inplace=True)

    return df


# ============================================================================
# API tools
# ============================================================================

def __create_url(database:str,
                 frequency:Optional[str]='A',
                 country:Optional[str]=None,
                 sector:Optional[str]=None,
                 units:Optional[str]=None,
                 indicator:Optional[str]=None,
                 start_period:Optional[str] = None,
                 end_period:Optional[str] = None) -> str:
    ''' 
    creates a url to query the IMF api using the CompactData method
        country_list: list of iso2 codes
    '''

    base_url = "http://dataservices.imf.org/REST/SDMX_JSON.svc/CompactData/"
    
    key = f'{database}/{frequency}'
    #add countries
    if country is not None:
        key = key + '.' + country 
    #add sector
    if sector is not None:
        key = key + '.' + sector 
    #add unit
    if units is not None:
        key = key + '.' + units
    #add indicator
    if indicator is not None:
        key = key + '.' + indicator
    #add time
    if (start_period is not None)&(end_period is not None):
        date_range = f'?startPeriod={str(start_period)}&endPeriod={str(end_period)}'
        key = key + date_range
    elif (start_period is not None)&(end_period is None):
        date_range = f'?startPeriod={str(start_period)}'
        key = key + date_range
    elif (start_period is None)&(end_period is not None):
        date_range = f'?endPeriod={str(end_period)}'
        key = key + date_range
    
    return base_url+key

def __query_imf(url:str) -> dict:
    '''queries the imf api and returns a json response'''
    counter = 0
    while counter<15:
        try:
            response = requests.get(url).json()
            response = response['CompactData']['DataSet']['Series']
            return response
        except:
            counter += 1
            
    print(f'Could not get: {url}')
        

def _imf_to_df(json:list) -> pd.DataFrame:
    ''' '''
    
    columns = list(json.keys())
    columns.remove('Obs')
    
    df = pd.json_normalize(json, 'Obs', columns)
    df.columns = df.columns.str.replace('@', '')
    
    return df

def get_imf_indicator(country_list:list,
                      database:str,
                      frequency:Optional[str]='A',
                      sector:Optional[str]=None,
                      units:Optional[str]=None,
                      indicator:Optional[str]=None,
                      start_period:Optional[str] = None,
                      end_period:Optional[str] = None
                      ) -> None:
    '''pipeline to download IMF data'''
    
    query_list = []
    
    for country in country_list:
        url = (__create_url(database, frequency, country, 
                                       sector, units, indicator, 
                                       start_period, end_period))
        query_list.append(url)
        
    
    df = pd.DataFrame()
    for url in query_list:
        try:
            query_df = _imf_to_df(__query_imf(url))
            df = pd.concat([df, query_df], ignore_index = True)
        except:
            pass
                           
    
    return df












