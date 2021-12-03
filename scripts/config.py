# -*- coding: utf-8 -*-
"""
Created on Fri Dec  3 10:17:41 2021

@author: LucaPicci
"""

import os

class Paths:
    def __init__(self, project_dir):
        self.project_dir = project_dir
    
    @property
    def scripts(self):
        return os.path.join(self.project_dir, 'scripts')
    
    @property
    def glossaries(self):
        return os.path.join(self.project_dir, 'scripts', 'glossaries')

    
paths = Paths(os.path.dirname(os.path.dirname(__file__)))