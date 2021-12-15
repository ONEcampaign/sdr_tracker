# -*- coding: utf-8 -*-
"""
Created on Fri Dec  3 10:30:41 2021

@author: LucaPicci
"""

from scripts import config
import pandas as pd
import country_converter as coco
from typing import Optional


# ==============================================================================
# Flourish map dataframe template
# ==============================================================================

def _get_world_geometries() -> dict:
    """
    return a disctionary for flourish geometries
        keys: iso3 codes
        values: geometries
    """
    g = pd.read_json(config.paths.glossaries + r'/flourish_geometries_world.json')
    g.columns = ['geo', 'iso_code']
    g = g.iloc[1:]
    g = g.drop_duplicates(subset=['iso_code'], keep='first')

    return g.set_index('iso_code').T.to_dict('records')[0]


def _get_country_df(columns: Optional['list'] = ['ISO3', 'name_short', 'continent']) -> pd.DataFrame:
    """
    creates a dictionary for world country names, codes, regions etc.

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

    country_df = (pd.read_csv(coco.COUNTRY_DATA_FILE, sep='\t')[columns]
                  .rename(columns={'ISO3': 'iso_code'}))

    return country_df


def get_flourish_map_df(slice_on_column: Optional[str] = None,
                        slice_by_values: Optional[list] = None) -> pd.DataFrame:
    """
    creates a fourish map dataframe template
    with country name(s) and geometries

        slice_on_column: specify the column to slice
        slice_by_values: specify the values to slice by

    """

    geometries = _get_world_geometries()
    country_df = _get_country_df()

    df = (pd.DataFrame({'iso_code': geometries.keys()})
          .assign(flourish_geom=lambda d: d.iso_code.map(geometries)))
    df = pd.merge(df, country_df, on='iso_code', how='left')

    if (slice_on_column is not None) & (slice_by_values is not None):
        df = df[df[slice_on_column].isin(slice_by_values)]
    elif (slice_on_column is None) & (slice_by_values is not None):
        raise ValueError('Both parameters must be None or not None')
    elif (slice_on_column is not None) & (slice_by_values is not None):
        raise ValueError('Both parameters must be None or not None')
    else:
        pass

    return df



if __name__ == '__main__':
    df = get_flourish_map_df(slice_on_column='continent',
                             slice_by_values=['Africa'])
    df.to_csv(f'{config.paths.output}/map_template.csv',
              index=False)
