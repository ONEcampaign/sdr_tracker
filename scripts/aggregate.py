import pandas as pd
from scripts import utils
import country_converter as coco


def _get_df(url: str, date: str) -> pd.DataFrame:

    df = pd.read_csv(url, delimiter="/t", engine="python").loc[3:]
    df = df["SDR Allocations and Holdings"].str.split("\t", expand=True)
    df.columns = ["country", "holdings", "allocations"]
    df["holdings"] = utils.clean_numeric_column(df["holdings"])
    df["allocations"] = utils.clean_numeric_column(df["allocations"])
    df["iso_code"] = coco.convert(df.country)
    df.drop(columns="country", inplace=True)
    df = df[df.iso_code != "not found"].reset_index(drop=True)
    df.rename(columns = {'holdings':f'holdings_{date}',
                          'allocations': f'allocations_{date}'}, inplace=True)
    df.drop(columns = f'allocations_{date}')

    return df


def _add_usd(df: pd.DataFrame, columns: list) -> pd.DataFrame:
    """Converts sdr holdings and allocations to USD in new columns"""

    exch_df = utils.read_sheet(116752025)
    exch = exch_df.loc[exch_df.indicator == "usd_exchange_rate", "value"].values[0]

    for column in columns:
        df[f"{column}_usd"] = round(df[column] / exch, 2)
        df = df.rename(columns={column: f"{column}_sdr"})

    return df



aug_url = 'https://www.imf.org/external/np/fin/tad/extsdr2.aspx?date1key=2021-08-31&tsvflag=Y'
dec_url = 'https://www.imf.org/external/np/fin/tad/extsdr2.aspx?date1key=2021-12-31&tsvflag=Y'
july_url = 'https://www.imf.org/external/np/fin/tad/extsdr2.aspx?date1key=2021-07-31&tsvflag=Y'




aug = _get_df(url = aug_url, date='aug')
aug = _add_usd(aug, columns=["holdings_aug"])
aug.to_csv(r"C:\Users\LucaPicci\OneDrive - THE ONE CAMPAIGN\Desktop\aug.csv", index=False)

dec = _get_df(url = dec_url, date='dec')
dec = _add_usd(dec, columns=["holdings_dec"])
dec.to_csv(r"C:\Users\LucaPicci\OneDrive - THE ONE CAMPAIGN\Desktop\dec.csv", index=False)

july = _get_df(url = july_url, date='july')
july = _add_usd(july, columns=["holdings_july"])
july.to_csv(r"C:\Users\LucaPicci\OneDrive - THE ONE CAMPAIGN\Desktop\july.csv", index=False)