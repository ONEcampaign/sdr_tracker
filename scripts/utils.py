from scripts import config, imf
import weo
import pandas as pd
from typing import Optional
import country_converter as coco
import time

def add_pct_gdp(df:pd.DataFrame,
                columns:list,
                gdp_year:int,
                weo_year: int,
                weo_release: int):
    """
    adds column(s) to a dataframe with a value as a pct of GDP
    """

    gdp_df = imf.get_gdp(gdp_year, weo_year, weo_release)
    df = pd.merge(df, gdp_df, on='iso_code', how='left')
    
    for column in columns:
        df[f'{column}_pct_gdp'] = (df[column]/(df['gdp']/1000000))*100
    df.drop(columns='gdp', inplace=True)

    return df


def clean_numeric_column(column:pd.Series):
    """
    """

    column = column.str.replace(',','')
    column = pd.to_numeric(column)

    return column



def country_df(columns: Optional['list'] = ['ISO3', 'continent'],
               keep_default_na=False) -> pd.DataFrame:
    """
    creates a dataFrame for world country names, codes, regions etc.
        columns:
            default ['ISO3', 'continent']
            additional names available:
            'name_short', 'name_official', 'ISO2','ISOnumeric','UNcode', 'FAOcode', 'GBDcode',
            'UNregion', 'EXIO1','EXIO2', 'EXIO3', 'WIOD', 'Eora', 'MESSAGE',
            'IMAGE', 'REMIND', 'OECD','EU', 'EU28', 'EU27', 'EU27_2007', 'EU25',
            'EU15', 'EU12', 'EEA','Schengen', 'EURO', 'UN', 'UNmember',
            'obsolete', 'Cecilia2050', 'BRIC','APEC', 'BASIC', 'CIS',
            'G7', 'G20', 'IEA', 'regex'
    """

    df = (pd.read_csv(coco.COUNTRY_DATA_FILE, sep='\t')[columns]
          .rename(columns={'ISO3': 'iso_code', 'name_short': 'country'}))

    return df

def time_script(func):
    '''Decorator to time script'''
    
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        func()
        end = time.perf_counter()
        elapsed = round((end-start)/60, 2)
        print(f'Time elapsed: {elapsed} min')
        
    return wrapper
    
    
    
    
    