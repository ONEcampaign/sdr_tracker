"""RST"""

import pandas as pd
import country_converter as coco
from csv import writer
from datetime import datetime

from scripts import config


def _read_rst_data(grid: int) -> pd.DataFrame:
    """Reads RST data from Google Sheets"""

    URL = (
        "https://docs.google.com/spreadsheets/d/e/2PACX-1vTqLJGWURadUrQeZ-"
        "p5iV8ONLptaYjbNVNmzPGpmZhLw0zyCWwuhfu-m1020sxrjkCi11Vm_wFBQ1i6/pub?"
        f"gid={grid}&single=true&output=csv"
    )

    return pd.read_csv(URL)


def update_rst_timeline_charts():
    """Update RST timeline charts"""

    df = _read_rst_data(1296770218)
    for country in df.country.unique():
        (
            df.loc[df["country"] == country].to_csv(
                config.Paths.output
                / "rst_timeline"
                / f'{coco.convert(country, to="ISO3")}.csv',
                index=False,
            )
        )


if __name__ == "__main__":
    update_rst_timeline_charts()
    with open(config.Paths.output / "rst_updates.csv", "a+", newline="") as write_obj:
        # Create a writer object from csv module
        csv_writer = writer(write_obj)
        # Add contents of list as last row in the csv file
        csv_writer.writerow([datetime.today()])
