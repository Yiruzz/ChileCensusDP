import pandas as pd
import numpy as np

from geographic_tree import GeographicTree

class TopDown:
    '''Represents the top-down approach to implement disclosure control for a tree structured data.
    
    The objective is to add noise to the data using differential privacy inspired in the TopDown algorithm used in 2020 USA census.
    '''
    def __init__(self):
        '''Constructor of the TopDown class.'''
        self.tree = None
        self.data_handler = None
    
    def set_data(self, data: pd.DataFrame):
        '''Setter of the data into the TopDown class.
        
        Args:
            data (pd.DataFrame): The data to be loaded.
        '''
        self.data = data
    
    def set_tree(self, tree: GeographicTree):
        '''Sets the tree into the TopDown class.
        
        Args:
            tree (GeographicTree): The tree to be loaded.
        '''
        self.tree = tree
    
