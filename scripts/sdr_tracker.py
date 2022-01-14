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


def __clean_holdings_allocation(df: pd.DataFrame, title: str):
    """cleans a dataframe for holding/allocation indicator"""

    # change date format
    df.TIME_PERIOD = pd.to_datetime(df.TIME_PERIOD)
    df.TIME_PERIOD = df.TIME_PERIOD.dt.strftime('%b %Y')

    return (
        df.assign(iso_code=lambda d: coco.convert(d.REF_AREA))
        .filter(["TIME_PERIOD", "OBS_VALUE", "iso_code"], axis=1)
        .rename(columns={f"OBS_VALUE": title, "TIME_PERIOD": f"{title}_date"})
        .astype({f"{title}": "float64"})
        .round({title: 2})
    )


def _get_holdings_allocation(
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
        df = df.loc[df.TIME_PERIOD == df.TIME_PERIOD.max()].reset_index(drop=True)
    else:
        df = df.loc[df.TIME_PERIOD == year_month].reset_index(drop=True)

    return df.pipe(__clean_holdings_allocation, title)


def add_holdings_allocation(df: pd.DataFrame) -> pd.DataFrame:
    """Adds holdings and allocations to the dataframe"""

    # Indicators
    cumulative_allocation_sdr = _get_holdings_allocation("HSA_XDR", "sdr_allocation_sdr_millions")
    cumulative_allocation_usd = _get_holdings_allocation("HSA_USD", "sdr_allocation_usd_millions")
    sdr_holding_sdr = _get_holdings_allocation("RAFASDR_XDR", "sdr_holdings_sdr_millions")
    sdr_holding_usd = _get_holdings_allocation("RAFASDR_USD", "sdr_holdings_usd_millions")

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
    """Reads a google sheet to a dataframe"""

    url = (
        "https://docs.google.com/spreadsheets/d/e/2PACX-1vQZWRGU2EljGEXRFhjGYLq8s2Yn"
        "xMGQsk3aNfC3I_-yuFPJaec7aSZCUxPnTe3hlOW4o4JtBtPLFbhu/pub?"
        f"gid={grid_number}&single=true&output=csv"
    )
    try:
        return pd.read_csv(url)
    except ConnectionError:
        raise ConnectionError("Could not read sheet")


def __sources(df, source_df, i) -> str:
    """Creates an HTML string for references or returns null if no sources are listed"""

    iso_code = df.loc[i, 'iso_code']
    if len(source_df[source_df.iso_code == iso_code]) > 0:
        sources = "<br><p><strong>References</strong></p><br>"
        for indx in source_df[source_df.iso_code == iso_code].index:
            source_name = source_df.loc[indx, "sources"]
            source_link = source_df.loc[indx, "link"]
            sources += f'<p><a href="{source_link}" target="_blank">{source_name}</a></p>'
    else:
        sources = np.nan

    return sources


def __sdr_table(df: pd.DataFrame, i:int) -> str:
    """Creates an HTML string for SDR holdings and allocation"""

    # August allocations
    allocation_aug_usd = df.loc[i, "sdrs_allocation_aug_23_usd"]
    allocation_aug_sdr = df.loc[i, "sdrs_allocation_aug_23_sdr"]
    allocation_aug_gdp = df.loc[i, "sdrs_allocation_aug_23_pct_gdp"]

    allocation_aug_html = (
        f'<tr><td style="text-align:left"><strong>SDR allocations</strong>'
        f'<sup>1</sup><br><i>on August 23, 2021</i></td>'
        f'<td style="text-align:center">{allocation_aug_usd}</td>'
        f'<td style="text-align:center">{allocation_aug_sdr}'
        f'</td><td style="text-align:center">{allocation_aug_gdp}</td></tr>'
    )

    # Cumulative allocations
    allocation_usd = df.loc[i, "sdr_allocation_usd_millions"]
    allocation_sdr = df.loc[i, "sdr_allocation_sdr_millions"]
    allocation_date = df.loc[i, "sdr_allocation_usd_millions_date"]
    allocation_gdp = df.loc[i, "sdr_allocation_pct_gdp"]

    allocation_html = (
        f'<tr><td style="text-align:left"><strong>Cumulative SDR allocations</strong>'
        f'<sup>2</sup><br><i>as of {allocation_date}</i></td>'
        f'<td style="text-align:center">{allocation_usd}</td>'
        f'<td style="text-align:center">{allocation_sdr}</td>'
        f'<td style="text-align:center">{allocation_gdp}</td></tr>'
    )

    # Current holdings
    holdings_usd = df.loc[i, "sdr_holdings_usd_millions"]
    holdings_sdr = df.loc[i, "sdr_holdings_sdr_millions"]
    holdings_date = df.loc[i, "sdr_holdings_sdr_millions_date"]
    holdings_gdp = df.loc[i, "sdr_holdings_pct_gdp"]

    holding_html = (
        f'<tr><td style="text-align:left"><strong>Current SDR holdings</strong>'
        f'<br><i>as of {holdings_date}</i></td>'
        f'<td style="text-align:center">{holdings_usd}</td>'
        f'<td style="text-align:center">{holdings_sdr}</td>'
        f'<td style="text-align:center">{holdings_gdp}</td></tr>'
    )

    # SDR holdings Table
    table = (
        f'<br><table><tr><th></th><th style="text-align:center">USD millions</th>'
        f'<th style="text-align:center">SDR millions</th>'
        f'<th style="text-align:center">SDR as % of GDP</th>'
        f"</tr>{allocation_aug_html}{allocation_html}{holding_html} </table>"
        "<br><p><i><sup>1</sup>SDR values for August 23, 2021 calculated using exchange rate from August 23"
        " - 1 USD: 0.705 SDRs</i></p>"
        "<p><i><sup>2</sup>Cumulative SDR allocations are" 
        " the total amount of SDRs the country has received from the IMF over the years;"
        " it includes SDRs from the August 2021 allocation and three prior allocations</i></p>"
    )
    return table


def __null_message(df: pd.DataFrame, column:str) -> pd.DataFrame:
    """Fixes text for popup and panel for countries where there is no data available"""

    message = "<br><p>No data available</p>"
    condition = (
            df.text.isna()
            & df.sdrs_allocation_aug_23_sdr.isna()
            & df.sdr_holdings_sdr_millions.isna()
            & df.sdr_allocation_sdr_millions.isna()
    )
    df.loc[condition, column] = message

    return df


def __country_name(df:pd.DataFrame, column:str) -> pd.DataFrame:
    """Adds country name to the beginning of the html string"""

    for i in df.index:
        country = df.loc[i, 'country']
        html = df.loc[i, column]
        df.loc[i, column] = f'<h1 style="text-align:center"><strong>{country}</strong></h1>{html}'

    return df


def _add_panel_html(df: pd.DataFrame) -> pd.DataFrame:
    """Creates the HTML code for the panel"""

    sources_df = read_sheet(1174650744)
    df['panel_html'] = np.nan

    for i in df.index:
        text = df.loc[i, "text"]
        table = __sdr_table(df, i)
        sources = __sources(df, sources_df, i)
        panel = f'<br>{table}'
        if text is not np.nan:
            panel = f'<br>{text}'+panel
        if sources is not np.nan:
            panel = panel + f'<br>{sources}'

        df.loc[i, 'panel_html'] = panel

    df = __null_message(df, 'panel_html')
    df = __country_name(df, 'panel_html')

    return df


def _add_popup_html(df: pd.DataFrame) -> pd.DataFrame:
    """Creates an HTML string for popups"""

    df["popup_html"] = np.nan
    for i in df.index:
        aug_allocation = df.loc[i, "sdrs_allocation_aug_23_usd"]
        text = df.loc[i, "text"]
        popup = (
            '<br><p style="text-align:left;">SDR allocation: &emsp;&emsp;'
            f'{aug_allocation} USD millions</p>'
            #f'<span style="float:right;">{aug_allocation} USD millions</span></p>'
            '<p style="text-align:left;"><i>on August 23, 2021</i></p><br>'
        )
        if text is not np.nan:
            popup += f'<p>{text}</p><br>'
        popup += f'<p style="text-align:center;"><strong>Click for more information</strong><p>'
        df.loc[i, "popup_html"] = popup
    df = __null_message(df, 'popup_html')
    df = __country_name(df, 'popup_html')

    return df


@utils.time_script
def create_sdr_map() -> None:
    """creates a csv for flourish map"""

    # get files
    map_template = pd.read_csv(f"{config.paths.glossaries}/map_template.csv")
    sdr_df = read_sheet(0)
    #sources_df = read_sheet(1174650744)

    # merge sdr from google with map template
    df = pd.merge(map_template, sdr_df, how="left", on="iso_code")

    # Clean DF
    df["sdrs_allocation_aug_23_usd"] = round(
        utils.clean_numeric_column(df["sdrs_allocation_aug_23_usd"]) / 1e6, 2
    )
    df["sdrs_allocation_aug_23_sdr"] = round(
        utils.clean_numeric_column(df["sdrs_allocation_aug_23_sdr"]) / 1e6, 2
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

    df = _add_panel_html(df)
    df = _add_popup_html(df)

    # export
    df = df[
        [
            "iso_code",
            "flourish_geom",
            "region",
            "country",
            #"text",
            #"sdrs_allocation_aug_23_sdr",
            "sdrs_allocation_aug_23_usd",
            #"sdrs_allocation_aug_23_pct_gdp",
            #"sdr_holdings_pct_gdp",
           # "sdr_holdings_sdr_millions",
            #"sdr_allocation_sdr_millions",
            #"sdr_allocation_pct_gdp",
            "popup_html",
            "panel_html"
        ]
    ]
    df.to_csv(f"{config.paths.output}/sdr.csv", index=False)
    print("successfully created map")


if __name__ == "__main__":
    pass
    # create map template for Africa
    create_africa_map_template()

    # create flourish csv
    create_sdr_map()
