# -*- coding: utf-8 -*-
"""
Created on Fri Dec  3 10:30:41 2021

@author: LucaPicci
"""

from scripts import config, utils, imf
import pandas as pd
import numpy as np

import country_converter as coco
from typing import Optional


# ============================================================================
# Map Template
# ============================================================================


def __geometry_df() -> pd.DataFrame:
    """
    return a dataframe with iso_code, flourish geometries, and continent
    """
    # Read in the geometries
    g = pd.read_json(config.paths.glossaries + r"/flourish_geometries_world.json")

    # Load a dataframe with continent information
    continents = utils.country_df()

    # Create a dataframe with iso_code and geometry
    return (
        g.rename(columns={g.columns[0]: "flourish_geom", g.columns[1]: "iso_code"})
        .iloc[1:]
        .drop_duplicates(subset="iso_code", keep="first")
        .merge(continents, on="iso_code")
        .filter(["iso_code", "flourish_geom", "continent"], axis=1)
        .reset_index(drop=True)
    )


def create_africa_map_template() -> None:
    """
    Creates template for a flourish map of Africa
    with country name and geometry output as dataframe saved to glossaries
    """
    __geometry_df().loc[lambda d: d.continent == "Africa"].drop(
        "continent", axis=1
    ).to_csv(f"{config.paths.glossaries}/map_template.csv", index=False)


# ============================================================================
# Get SDR Holdings and allocation from IMF
# ============================================================================


def __clean_holdings(df: pd.DataFrame, title: str):
    """cleans a dataframe for holding/allocation indicator"""

    return (
        df.assign(iso_code=lambda d: coco.convert(d.REF_AREA))
        .filter(["TIME_PERIOD", "OBS_VALUE", "iso_code"], axis=1)
        .rename(columns={f"OBS_VALUE": title, "TIME_PERIOD": f"{title}_date",})
        .astype({f"{title}": "float64"})
        .round({title: 2})
    )


def _get_holdings(
    indicator: str, title: str, year_month: Optional[str] = None
) -> pd.DataFrame:
    """
    retrieves holdings/allocation indicator from the IMF year_month - specify year and
     month to pull If none, the latest date will be taken
        title - specify the title of the indicator (used as column title)
        indicator - code of IMF indicator
    """

    df = imf.get_imf_indicator(
        country_list=utils.africa_list("ISO2"),
        database="IFS",
        frequency="M",
        indicator=indicator,
        start_period="2021-08",
    )

    if year_month is None:
        df = df.loc[df.TIME_PERIOD == df.TIME_PERIOD.max()]
    else:
        df = df.loc[df.TIME_PERIOD == year_month]

    return df.pipe(__clean_holdings, title)


def add_holdings_allocation(df: pd.DataFrame) -> pd.DataFrame:
    """Adds holdings and allocations to the dataframe"""

    # Indicators
    cumulative_allocation_sdr = _get_holdings("HSA_XDR", "sdr_allocation_sdr_millions")
    cumulative_allocation_usd = _get_holdings("HSA_USD", "sdr_allocation_usd_millions")
    sdr_holding_sdr = _get_holdings("RAFASDR_XDR", "sdr_holdings_sdr_millions")
    sdr_holding_usd = _get_holdings("RAFASDR_USD", "sdr_holdings_usd_millions")

    # Merge indicators to passed dataframe
    for indicator in [
        cumulative_allocation_usd,
        cumulative_allocation_sdr,
        sdr_holding_sdr,
        sdr_holding_usd,
    ]:
        df = pd.merge(df, indicator, how="left", on=["iso_code"])

    # % GDP columns
    df = utils.add_pct_gdp(
        df,
        columns=["sdr_allocation_usd_millions", "sdr_holdings_usd_millions"],
        gdp_year=2021,
        weo_year=2021,
        weo_release=2,
    )
    df.rename(
        columns={
            "sdr_allocation_usd_millions_pct_gdp": "sdr_allocation_pct_gdp",
            "sdr_holdings_usd_millions_pct_gdp": "sdr_holdings_pct_gdp",
        },
        inplace=True,
    )

    return df


# ============================================================================
# Map Build
# ============================================================================


def read_sheet(grid_number: int) -> pd.DataFrame:
    """ Reads a google sheet to a dataframe"""

    url = (
        "https://docs.google.com/spreadsheets/d/e/2PACX-1vQZWRGU2EljGEXRFhjGYLq8s2Yn"
        "xMGQsk3aNfC3I_-yuFPJaec7aSZCUxPnTe3hlOW4o4JtBtPLFbhu/pub?"
        f"gid={grid_number}&single=true&output=csv"
    )
    try:
        return pd.read_csv(url)
    except ConnectionError:
        raise ConnectionError("Could not read sheet")


def _add_source_html(sdr_df: pd.DataFrame, sources: pd.DataFrame) -> pd.DataFrame:
    """
    creates an html string for sources and adds it to a dataframe
    """
    sdr_df["source_html"] = np.nan
    for iso in sources.iso_code.unique():
        if len(sources[sources.iso_code == iso]) > 0:
            iso_string = "<p><strong>References</strong></p><br>"
            for i in sources[sources.iso_code == iso].index:
                source = sources.loc[i, "sources"]
                link = sources.loc[i, "link"]
                iso_string += f'<p><a href="{link}" target="_blank">{source}</a></p>'
            sdr_df.loc[sdr_df.iso_code == iso, "source_html"] = iso_string

    return sdr_df


def _add_sdr_table(df: pd.DataFrame) -> pd.DataFrame:
    """Creates an HTML string for SDR holdings and allocation"""

    df["sdr_table"] = np.nan
    for i in df.index:
        # August allocations
        allocation_aug_usd = df.loc[i, "sdrs_allocation_aug_23_usd"]
        allocation_aug_sdr = df.loc[i, "sdrs_allocation_aug_23_sdr"]
        allocation_aug_gdp = df.loc[i, "sdrs_allocation_aug_23_pct_gdp"]

        allocation_aug_html = (
            f"<tr><td>SDR allocations on August 23, 2021</td>"
            f"<td>{allocation_aug_usd}</td><td>{allocation_aug_sdr}"
            f"</td><td>{allocation_aug_gdp}</td></tr>"
        )

        # Current allocations
        allocation_usd = df.loc[i, "sdr_allocation_usd_millions"]
        allocation_sdr = df.loc[i, "sdr_allocation_sdr_millions"]
        allocation_date = df.loc[i, "sdr_allocation_usd_millions_date"]
        allocation_gdp = df.loc[i, "sdr_allocation_pct_gdp"]

        allocation_html = (
            f"<tr><td>SDR allocations as of {allocation_date}</td>"
            f"<td>{allocation_usd}</td><td>{allocation_sdr}</td>"
            f"<td>{allocation_gdp}</td></tr>"
        )

        # Current holdings
        holdings_usd = df.loc[i, "sdr_holdings_usd_millions"]
        holdings_sdr = df.loc[i, "sdr_holdings_sdr_millions"]
        holdings_date = df.loc[i, "sdr_holdings_sdr_millions_date"]
        holdings_gdp = df.loc[i, "sdr_holdings_pct_gdp"]

        holding_html = (
            f"<tr><td>SDR holdings as of {holdings_date}</td>"
            f"<td>{holdings_usd}</td><td>{holdings_sdr}</td>"
            f"<td>{holdings_gdp}</td></tr>"
        )

        # SDR holdings Table
        table = (
            f"<table><tr><th></th><th>USD millions</th>"
            f"<th>SDR millions</th><th>SDR as % of GDP</th>"
            f"</tr>{allocation_aug_html}{allocation_html}{holding_html} </table>"
        )

        df.loc[i, "sdr_table"] = table

    return df


def _add_popup_html(df: pd.DataFrame) -> pd.DataFrame:
    """Creates an HTML string for popups"""

    df["popup_html"] = np.nan

    for i in df.index:
        allocation = df.loc[i, "sdr_allocation_usd_millions"]
        holding = df.loc[i, "sdr_holdings_usd_millions"]
        date = df.loc[i, "sdr_holdings_sdr_millions_date"]

        popup = (
            f"<p>SDR allocations: {allocation} USD millions</p>"
            f"<p>SDR holdings: {holding} USD millions</p>"
            f"<p> as of {date}</p>"
        )

        df.loc[i, "popup_html"] = popup

    return df


@utils.time_script
def create_sdr_map() -> None:
    """
    creates a csv for flourish map
    """
    # get files
    map_template = pd.read_csv(f"{config.paths.glossaries}/map_template.csv")
    sdr_df = read_sheet(0)
    sources_df = read_sheet(1174650744)

    # merge sdr from google with map template
    df = pd.merge(map_template, sdr_df, how="left", on="iso_code")

    # Clean DF
    df["sdrs_allocation_aug_23_usd"] = (
        utils.clean_numeric_column(df["sdrs_allocation_aug_23_usd"]) / 1e6
    )
    df["sdrs_allocation_aug_23_sdr"] = (
        utils.clean_numeric_column(df["sdrs_allocation_aug_23_sdr"]) / 1e6
    )
    df = df.dropna(subset=["country"])

    # add pct_gdp columns
    df = utils.add_pct_gdp(
        df,
        columns=["sdrs_allocation_aug_23_usd"],
        gdp_year=2021,
        weo_year=2021,
        weo_release=2,
    )
    df.rename(
        columns={
            "sdrs_allocation_aug_23_usd_pct_gdp": "sdrs_allocation_aug_23_pct_gdp"
        },
        inplace=True,
    )

    # add holdings and allocation
    df = add_holdings_allocation(df)

    # add html for popups and panels
    df = _add_sdr_table(df)
    df = _add_source_html(df, sources_df)
    df = _add_popup_html(df)

    # export
    df = df[
        [
            "iso_code",
            "flourish_geom",
            "region",
            "country",
            "text",
            "sdrs_allocation_aug_23_sdr",
            "sdrs_allocation_aug_23_usd",
            "sdrs_allocation_aug_23_pct_gdp",
            "sdr_holdings_pct_gdp",
            "sdr_holdings_sdr_millions",
            "sdr_allocation_sdr_millions",
            "sdr_allocation_pct_gdp",
            "sdr_table",
            "source_html",
            "popup_html",
        ]
    ]
    df.to_csv(f"{config.paths.output}/sdr.csv", index=False)
    print("successfully created map")
    return df


if __name__ == "__main__":
    pass
    # create map template for Africa
    create_africa_map_template()

    # create flourish csv
    create_sdr_map()
