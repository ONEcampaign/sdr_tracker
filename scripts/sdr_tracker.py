# -*- coding: utf-8 -*-
"""
Created on Fri Dec  3 10:30:41 2021

@author: LucaPicci
"""

import numpy as np
import pandas as pd
from bblocks import set_bblocks_data_path

from scripts import config, download_sdr, utils
import datetime

set_bblocks_data_path(config.Paths.raw_data)


# ============================================================================
# Map Template
# ============================================================================


def __geometry_df() -> pd.DataFrame:
    """
    return a dataframe with iso_code, flourish geometries, and continent
    """
    # Read in the geometries
    g = pd.read_json(config.Paths.glossaries / "flourish_geometries_world.json")

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
    ).to_csv(f"{config.Paths.glossaries}/map_template.csv", index=False)


# ============================================================================
# Map Build
# ============================================================================


def __sources(df, source_df, i) -> str:
    """Creates an HTML string for references or returns null if no sources are listed"""

    iso_code = df.loc[i, "iso_code"]
    if len(source_df[source_df.iso_code == iso_code]) > 0:
        sources = "<br><p><strong>References</strong></p><br>"
        for indx in source_df[source_df.iso_code == iso_code].index:
            source_name = source_df.loc[indx, "sources"]
            source_link = source_df.loc[indx, "link"]
            sources += (
                f'<p><a href="{source_link}" target="_blank">{source_name}</a></p>'
            )
    else:
        sources = np.nan

    return sources


def __sdr_table(df: pd.DataFrame, i: int) -> str:
    """Creates an HTML string for SDR holdings and allocation"""

    # August allocations
    allocation_aug_usd = df.loc[i, "sdrs_allocation_aug_23_usd"]
    allocation_aug_sdr = df.loc[i, "sdrs_allocation_aug_23_sdr"]
    allocation_aug_gdp = df.loc[i, "sdrs_allocation_aug_23_pct_gdp"]

    allocation_aug_html = (
        f'<tr><td style="text-align:left"><strong>SDR allocations</strong>'
        f"<sup>1</sup><br><i>on 23 August 2021</i></td>"
        f'<td style="text-align:center">{allocation_aug_usd}</td>'
        f'<td style="text-align:center">{allocation_aug_sdr}'
        f'</td><td style="text-align:center">{allocation_aug_gdp}</td></tr>'
    )

    # Cumulative allocations
    allocation_usd = df.loc[i, "allocations_usd"]
    allocation_sdr = df.loc[i, "allocations_sdr"]
    allocation_date = df.loc[i, "date"]
    allocation_gdp = df.loc[i, "allocations_pct_gdp"]

    allocation_html = (
        f'<tr><td style="text-align:left"><strong>Cumulative SDR allocations</strong>'
        f"<sup>2</sup><br><i>as of {allocation_date}</i></td>"
        f'<td style="text-align:center">{allocation_usd}</td>'
        f'<td style="text-align:center">{allocation_sdr}</td>'
        f'<td style="text-align:center">{allocation_gdp}</td></tr>'
    )

    # Current holdings
    holdings_usd = df.loc[i, "holdings_usd"]
    holdings_sdr = df.loc[i, "holdings_sdr"]
    holdings_date = df.loc[i, "date"]
    holdings_gdp = df.loc[i, "holdings_pct_gdp"]

    holding_html = (
        f'<tr><td style="text-align:left"><strong>Current SDR holdings</strong>'
        f"<br><i>as of {holdings_date}</i></td>"
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
        "<br><p><i><sup>1</sup>USD values for 23 August 2021 are calculated using the exchange "
        "rate from 23 August"
        " - 1 USD: 0.705 SDRs</i></p>"
        "<p><i><sup>2</sup>Cumulative SDR allocations are"
        " the total amount of SDRs the country has received from the IMF over the years;"
        " it includes SDRs from the August 2021 allocation and three prior allocations</i></p>"
    )
    return table


def __null_message(df: pd.DataFrame, column: str) -> pd.DataFrame:
    """Fixes text for popup and panel for countries where there is no data available"""

    message = "<br><p>No data available</p>"
    condition = (
        df.text.isna()
        & df.sdrs_allocation_aug_23_sdr.isna()
        & df.holdings_sdr.isna()
        & df.allocations_sdr.isna()
    )
    df.loc[condition, column] = message

    return df


def __country_name(df: pd.DataFrame, column: str) -> pd.DataFrame:
    """Adds country name to the beginning of the html string"""

    for i in df.index:
        country = df.loc[i, "country"]
        html = df.loc[i, column]
        df.loc[
            i, column
        ] = f'<h1 style="text-align:center"><strong>{country}</strong></h1>{html}'

    return df


def _add_panel_html(df: pd.DataFrame) -> pd.DataFrame:
    """Creates the HTML code for the panel"""

    sources_df = utils.read_sheet(1174650744)
    df["panel_html"] = np.nan

    for i in df.index:
        holdings_pct_allocation = df.loc[i, "holdings_pct_allocation"]
        holdings_pct_allocation_date = df.loc[i, "date"]
        pct_used_text = (
            '<br><p style="text-align:left;"><strong>SDR holdings</strong>: &emsp;&emsp;&emsp;'
            f"<strong>{holdings_pct_allocation} % of cumulative allocations</strong></p>"
            f'<p style="text-align:left;"><i>as of {holdings_pct_allocation_date}</i></p><br>'
        )

        text = df.loc[i, "text"]
        table = __sdr_table(df, i)
        sources = __sources(df, sources_df, i)

        panel = f"<br>{pct_used_text}{table}"
        if text is not np.nan:
            panel = f"<br>{text}" + panel
        if sources is not np.nan:
            panel = panel + f"<br>{sources}"

        df.loc[i, "panel_html"] = panel

    df = __null_message(df, "panel_html")
    df = __country_name(df, "panel_html")

    return df


def _add_popup_html(df: pd.DataFrame) -> pd.DataFrame:
    """Creates an HTML string for popups"""

    df["popup_html"] = np.nan
    for i in df.index:
        holdings_pct_allocation = df.loc[i, "holdings_pct_allocation"]
        holdings_pct_allocation_date = df.loc[i, "date"]
        aug_allocation = df.loc[i, "sdrs_allocation_aug_23_usd"]
        text = df.loc[i, "text"]
        popup = (
            '<br><p style="text-align:left;"><strong>SDR holdings</strong>: '
            "&emsp;&emsp;&emsp;&emsp;"
            f"<strong>{holdings_pct_allocation} % of cumulative allocations</strong></p>"
            f'<p style="text-align:left;"><i>as of {holdings_pct_allocation_date}</i></p><br>'
            '<br><p style="text-align:left;">SDR allocation: &emsp;&emsp;&emsp;'
            f"{aug_allocation} USD millions</p>"
            '<p style="text-align:left;"><i>on 23 August 2021</i></p><br>'
        )
        if text is not np.nan:
            popup += f"<p>{text}</p><br>"
        popup += f'<p style="text-align:center;"><strong>Click for more information</strong><p>'
        df.loc[i, "popup_html"] = popup
    df = __null_message(df, "popup_html")
    df = __country_name(df, "popup_html")

    return df


def create_sdr_map() -> None:
    """creates a csv for flourish map"""

    # get files
    map_template = pd.read_csv(f"{config.Paths.glossaries}/map_template.csv")
    df = utils.read_sheet(0)

    # merge sdr from google with map template and clean
    df = pd.merge(map_template, df, how="left", on="iso_code")
    df["sdrs_allocation_aug_23_usd"] = utils.clean_numeric_column(
        df["sdrs_allocation_aug_23_usd"]
    )
    df["sdrs_allocation_aug_23_sdr"] = utils.clean_numeric_column(
        df["sdrs_allocation_aug_23_sdr"]
    )
    df = df.dropna(subset=["country"])

    # add holdings and allocation
    current_year = datetime.datetime.now().year
    latest_sdr = download_sdr.get_latest_sdr(current_year)
    df = pd.merge(df, latest_sdr, on="iso_code", how="left")

    # add pct_gdp columns
    df = utils.add_pct_gdp(
        df,
        columns=["sdrs_allocation_aug_23_usd", "holdings_usd", "allocations_usd"],
        gdp_year=current_year,
    )

    # add html for popups and panels
    df = _add_panel_html(df)
    df = _add_popup_html(df)

    # export
    df.to_csv(f"{config.Paths.output}/sdr.csv", index=False)
