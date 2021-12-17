import pandas as pd
from scripts import config
import country_converter as coco
from typing import Optional

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


def __country_df(columns: Optional['list'] = ['ISO3', 'continent']) -> pd.DataFrame:
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


def _flourish_map_df(slice_on_column: Optional[str] = None,
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
