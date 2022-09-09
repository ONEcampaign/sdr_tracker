import json
import os

import gspread
import pandas as pd
from bblocks.import_tools.imf import latest_sdr_exchange
from oauth2client.service_account import ServiceAccountCredentials

# Load key as json object
KEY: json = json.loads(os.environ["SHEETS_API"])

WORKBOOK_KEY: str = "1fIZkFJ686FrPmogt0iDlTv3aV75VyO1-MfEow2cgaFg"
WORKSHEET_KEY: int = 0
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
CREDENTIALS = ServiceAccountCredentials.from_json_keyfile_dict(
    keyfile_dict=KEY, scopes=SCOPES
)


def _authenticate() -> gspread.client.Client:
    """Authenticate with Google Sheets API"""

    return gspread.authorize(CREDENTIALS)


def _get_workbook(
    authenticated_client: gspread.client.Client, workbook_key: str
) -> gspread.Spreadsheet:
    """Get workbook from Google Sheets API"""

    return authenticated_client.open_by_key(key=workbook_key)


def _get_worksheet(
    workbook: gspread.Spreadsheet, worksheet_key: int
) -> gspread.Worksheet:
    """Get worksheet from Google Sheets API"""

    return workbook.get_worksheet_by_id(id=worksheet_key)


def df2gsheet(df: pd.DataFrame, worksheet_obj: gspread.Worksheet) -> None:
    """Write dataframe to Google Sheets API"""

    columns = [str(col).replace("\n", "").strip() for col in df.columns]
    values = df.fillna("").values.tolist()

    worksheet_obj.update([columns] + values)


def get_latest_exchange() -> pd.DataFrame:
    """Returns the latest exchange rate of the SDR"""
    usd_exchange = latest_sdr_exchange(currency="USD")

    return (
        pd.DataFrame(
            {
                "indicator": ["usd_exchange_rate"],
                "value": [usd_exchange["value"]],
                "date": [usd_exchange["date"]],
            }
        )
        .astype({"date": "datetime64[ns]"})
        .assign(date=lambda d: d.date.dt.strftime("%Y-%m-%d"))
    )


def upload_exchange() -> None:
    data = get_latest_exchange()
    auth = _authenticate()
    wb = _get_workbook(auth, WORKBOOK_KEY)
    sheet = _get_worksheet(wb, WORKSHEET_KEY)

    # Upload data
    df2gsheet(data, sheet)
