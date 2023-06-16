"""RST"""

import pandas as pd
import country_converter as coco

from scripts import config



url = 'https://docs.google.com/spreadsheets/d/e/2PACX-1vTqLJGWURadUrQeZ-' \
      'p5iV8ONLptaYjbNVNmzPGpmZhLw0zyCWwuhfu-m1020sxrjkCi11Vm_wFBQ1i6/pub?' \
      'gid=1296770218&single=true&output=csv'

df = pd.read_csv(url)
for country in df.country.unique():
    (df.loc[df['country'] == country]
    .to_csv(config.Paths.output / 'rst_timeline' /
            f'{coco.convert(country, to="ISO3")}.csv', index=False)
    )



