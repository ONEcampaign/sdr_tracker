# -*- coding: utf-8 -*-
"""
Created on Fri Dec  3 10:30:41 2021

@author: LucaPicci
"""

from scripts import config
import pandas as pd
import country_converter as coco
from typing import Optional
import numpy as np


# ==============================================================================
# Flourish map dataframe template
# ==============================================================================

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

def __country_df(columns: Optional['list'] = ['ISO3', 'name_short', 'continent']) -> pd.DataFrame:
    """
    creates a dataFrame for world country names, codes, regions etc.
        columns:
            default ['ISO3', 'name_short', 'continent']
            additional names available:
            'name_official', 'ISO2','ISOnumeric','UNcode', 'FAOcode', 'GBDcode',
            'UNregion', 'EXIO1','EXIO2', 'EXIO3', 'WIOD', 'Eora', 'MESSAGE',
            'IMAGE', 'REMIND', 'OECD','EU', 'EU28', 'EU27', 'EU27_2007', 'EU25',
            'EU15', 'EU12', 'EEA','Schengen', 'EURO', 'UN', 'UNmember',
            'obsolete', 'Cecilia2050', 'BRIC','APEC', 'BASIC', 'CIS',
            'G7', 'G20', 'IEA', 'regex'
    """

    df = (pd.read_csv(coco.COUNTRY_DATA_FILE, sep='\t')[columns]
          .rename(columns={'ISO3': 'iso_code'}))

    return df

def flourish_map_df(slice_on_column: Optional[str] = None,
                    slice_by_values: Optional[list] = None) -> pd.DataFrame:
    """
    creates a fourish map dataframe template
    with country name(s) and geometries

        slice_on_column: specify the column to slice
        slice_by_values: specify the values to slice by
    """
    df = pd.merge(__geometry_df(), __country_df(),
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

# ==============================================================================
# SDR Map Build
# ==============================================================================

def _add_source_html(sdr_df:pd.DataFrame, sources:pd.DataFrame) -> pd.DataFrame:
    """
    creates an html string for sources and adds it to a dataframe
    """
    sdr_df['sources'] = np.nan
    for iso in sources.iso_code.unique():
        if len(sources[sources.iso_code == iso])>0:
            iso_string = '<p><strong>Sources</strong></p>'
            for i in sources[sources.iso_code == iso].index:
                source = sources.loc[i, 'sources']
                link = sources.loc[i, 'link']
                iso_string += f'<p><a href="{link}" target="_blank">{source}</a></p>'
            sdr_df.loc[sdr_df.iso_code == iso, 'sources'] = iso_string

    return sdr_df

def create_sdr(map_template:pd.DataFrame,
               sdr_df:pd.DataFrame,
               sources_df:pd.DataFrame) -> pd.DataFrame:
    """
    creates a csv for flourish map
    """
    df = pd.merge(map_template, sdr_df, how='left', on='iso_code')
    df = _add_source_html(df, sources_df)

    return df





if __name__ == '__main__':

    # create map template for Africa
    template = flourish_map_df(slice_on_column='continent',
                               slice_by_values=['Africa'])
    template.to_csv(f'{config.paths.glossaries}/map_template.csv',
                    index=False)

    # create flourish csv
    map_template = pd.read_csv(f'{config.paths.glossaries}/map_template.csv')
    sdr_df = pd.read_csv(f'{config.paths.glossaries}/sdr.csv')
    sources_df = pd.read_csv(f'{config.paths.glossaries}/sources.csv')

    df = create_sdr(map_template, sdr_df, sources_df)
    df.to_csv(f'{config.paths.output}/sdr.csv',
              index=False)
