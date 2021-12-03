# -*- coding: utf-8 -*-
"""
Created on Fri Dec  3 10:30:41 2021

@author: LucaPicci
"""

from scripts import config
import pandas as pd

def get_world_geometries() -> dict:
    '''
    return a disctionary for flourish geometries
        keys: iso3 codes
        values: geometries
    '''
    g = pd.read_json(config.paths.glossaries+r'/flourish_geometries_world.json')
    g.columns = ['geo','iso_code']
    g =g.iloc[1:]
    g = g.drop_duplicates(subset=['iso_code'], keep='first')

    return g.set_index('iso_code').T.to_dict('records')[0]

