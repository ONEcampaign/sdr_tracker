import pandas as pd
from scripts import utils
import requests
import country_converter as coco
from bs4 import BeautifulSoup
from datetime import datetime


def _find_latest_release(year: int) -> dict:
    """
    Finds the latest SDR announcement
    Returns a dictionary with date of announcement and url to the announcement page

    parameters:
        year: int   Specify the year. the url contains a year in the tail. Likely this will change to
                    2022 once January SDRs are released
    """

    base_url = f"https://www.imf.org/external/np/fin/tad/extsdr3.aspx?dateyear={year}"

    content = requests.get(base_url).content
    soup = BeautifulSoup(content, "html.parser")
    table = soup.find_all("table")[4].find_all("a")

    url = f"https://www.imf.org/external/np/fin/tad/{table[0].get('href')}"
    date = datetime.strptime(table[0].text, "%B %d, %Y").strftime("%d %B %Y")

    return {
        "date": date,
        "url": url,
    }


def _get_tsv_url(url: str) -> str:
    """retrieves the url for the tsv file"""

    content = requests.get(url).content
    soup = BeautifulSoup(content, "html.parser")
    href = soup.find_all("a", text="TSV")[0].get("href")

    return f"https://www.imf.org/external/np/fin/tad/{href}"


def _get_df(url: str, date: str) -> pd.DataFrame:
    """
    Returns a cleaned dataframe for the latest SDR release

    Parameters:
        url: str    tsv url
        date: str   the date of the release
    """

    df = pd.read_csv(url, delimiter="/t", engine="python").loc[3:]
    df = df["SDR Allocations and Holdings"].str.split("\t", expand=True)
    df.columns = ["country", "holdings", "allocations"]
    df["holdings"] = utils.clean_numeric_column(df["holdings"])
    df["allocations"] = utils.clean_numeric_column(df["allocations"])
    df["iso_code"] = coco.convert(df.country)
    df["date"] = date
    df.drop(columns="country", inplace=True)
    df = df[df.iso_code != "not found"].reset_index(drop=True)

    return df


def _add_usd(df: pd.DataFrame, columns: list) -> pd.DataFrame:
    """Converts sdr holdings and allocations to USD in new columns"""

    exch_df = utils.read_sheet(116752025)
    exch = exch_df.loc[exch_df.indicator == "usd_exchange_rate", "value"].values[0]

    for column in columns:
        df[f"{column}_usd"] = round(df[column] / exch, 2)
        df = df.rename(columns={column: f"{column}_sdr"})

    return df


def _add_pct_used(df: pd.DataFrame) -> pd.DataFrame:
    """
    Creates a new calculated column for SDRs used as a % of allocations
    pct_used = 100*(sdr_allocations - sdr_holdings)/sdr_allocations
    """

    df['holdings_pct_allocation'] = round(100 * (df.holdings/df.allocations), 2)

    return df


def get_latest_sdr(year: int):
    """
    Returns a dataframe with the latest SDR values
    Columns in dataframe: ['country', 'holdings', 'allocations', 'iso_code', 'date']

    Parameters:
        year: int   Specify the year. the url contains a year in the tail. Likely this will change to
                    2022 once January SDRs are released
    """

    latest_release = _find_latest_release(year)
    tsv_url = _get_tsv_url(latest_release["url"])
    df = _get_df(url=tsv_url, date=latest_release["date"])
    df = _add_pct_used(df)
    df = _add_usd(df, columns=["holdings", "allocations"])

    return df
