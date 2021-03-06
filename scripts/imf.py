# -*- coding: utf-8 -*-
"""
Created on Fri Dec 17 11:40:41 2021

@author: LucaPicci
"""

import requests
from typing import Optional
import pandas as pd
from scripts import config
import weo

# ============================================================================
# WEO tools
# ============================================================================


def _download_weo(year: int, release: int) -> None:
    """Downloads WEO as a csv to glossaries folder as "weo_month_year.csv"""

    try:
        weo.download(
            year=year,
            release=release,
            directory=config.paths.glossaries,
            filename=f"weo_{year}_{release}.csv",
        )
    except ConnectionError:
        raise ConnectionError("Could not download weo data")


def _clean_weo(df: pd.DataFrame) -> pd.DataFrame:
    """cleans and formats weo dataframe"""

    columns = names = {
        "ISO": "iso_code",
        "WEO Subject Code": "indicator",
        "Subject Descriptor": "indicator_name",
        "Units": "units",
        "Scale": "scale",
    }
    cols_to_drop = [
        "WEO Country Code",
        "Country",
        "Subject Notes",
        "Country/Series-specific Notes",
        "Estimates Start After",
    ]
    df = (
        df.drop(cols_to_drop, axis=1)
        .rename(columns=columns)
        .melt(id_vars=names.values(), var_name="year", value_name="value")
    )
    df.value = df.value.map(
        lambda x: (str(x).strip().replace(",", "").replace("--", ""))
    )
    df.year = pd.to_numeric(df.year)
    df.value = pd.to_numeric(df.value, errors="coerce")

    return df


def get_gdp(gdp_year: int, weo_year: int, weo_release: int) -> pd.DataFrame:
    """
    Retrieves gdp value for a specific year
    """

    _download_weo(year=weo_year, release=weo_release)
    df = weo.WEO(f"{config.paths.glossaries}/weo_{weo_year}_{weo_release}.csv").df
    df = _clean_weo(df)
    df = df[(df.indicator == "NGDPD") & (df.year == gdp_year)][["iso_code", "value"]]
    df.value = df.value * 1e9
    df.rename(columns={"value": "gdp"}, inplace=True)

    return df
