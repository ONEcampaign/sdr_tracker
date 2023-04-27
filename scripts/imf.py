# -*- coding: utf-8 -*-
"""
Created on Fri Dec 17 11:40:41 2021

@author: LucaPicci
"""

import requests
from typing import Optional
import pandas as pd
from scripts import config
from bblocks import set_bblocks_data_path, WorldEconomicOutlook

set_bblocks_data_path(config.Paths.raw_data)
# ============================================================================
# WEO tools
# ============================================================================


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


def get_gdp(gdp_year: int) -> pd.DataFrame:
    """
    Retrieves gdp value for a specific year
    """
    weo = WorldEconomicOutlook()
    weo.load_data("NGDPD")

    return (
        weo.get_data()
        .assign(year=lambda d: d.year.dt.year, value=lambda d: d.value * 1e9)
        .query(f"year == {gdp_year}")
        .rename(columns={"value": "gdp"})
    )
