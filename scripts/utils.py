from scripts import imf

import pandas as pd
from typing import Optional
import country_converter as coco
import time


def add_pct_gdp(
    df: pd.DataFrame, columns: list, gdp_year: int, weo_year: int, weo_release: int
):
    """
    adds column(s) to a dataframe with a value as a pct of GDP
    """
    # download GDP data using WEO package
    gdp_df = imf.get_gdp(gdp_year, weo_year, weo_release)

    # merge GDP data with provided df
    df = pd.merge(df, gdp_df, on="iso_code", how="left")

    for column in columns:
        # Divide GDP by a million and multiply by 100 to get a percentage
        df[f"{column}_pct_gdp"] = 100 * df[column] / (df["gdp"] / 1e6)

    df.drop(columns="gdp", inplace=True)

    return df


def clean_numeric_column(column: pd.Series) -> pd.Series:

    column = column.str.replace(",", "")

    return pd.to_numeric(column)


def country_df(columns: Optional[list] = None) -> pd.DataFrame:
    """
    creates a dataFrame for world country names, codes, regions etc.
        columns:
            default ['ISO3', 'continent']
            additional names available:
            'name_short', 'name_official', 'ISO2','ISOnumeric','UNcode', 'FAOcode','GBDcode',
            'UNregion', 'EXIO1','EXIO2', 'EXIO3', 'WIOD', 'Eora', 'MESSAGE',
            'IMAGE', 'REMIND', 'OECD','EU', 'EU28', 'EU27', 'EU27_2007', 'EU25',
            'EU15', 'EU12', 'EEA','Schengen', 'EURO', 'UN', 'UNmember',
            'obsolete', 'Cecilia2050', 'BRIC','APEC', 'BASIC', 'CIS',
            'G7', 'G20', 'IEA', 'regex'
    """
    if columns is None:
        columns = ["ISO3", "continent"]

    return pd.read_csv(coco.COUNTRY_DATA_FILE, sep="\t", usecols=columns).rename(
        columns={"ISO3": "iso_code", "name_short": "country"}
    )


def time_script(func):
    """Decorator to time script"""

    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        func()
        end = time.perf_counter()
        elapsed = round((end - start) / 60, 2)
        print(f"Time elapsed: {elapsed} min")

    return wrapper


def africa_list(code_type: str = "ISO3"):
    """Return list of African countries"""

    df = (
        country_df(columns=["ISO3", "ISO2", "continent"])
        .loc[lambda d: d.continent == "Africa"]
        .fillna("NA")
        .dropna(subset=["ISO2"])
        .drop_duplicates("ISO2")
    )
    if code_type == "ISO3":
        return df.iso_code.tolist()
    elif code_type == "ISO2":
        return df.ISO2.tolist()
