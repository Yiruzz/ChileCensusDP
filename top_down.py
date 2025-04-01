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
        self.data = None
    
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
    
    def construct_contingency_table(self, df: pd.DataFrame, columns: list) -> np.array:
        '''Constructs the contingency table for the given dataframe and columns.
        
        Args:
            df (pd.DataFrame): The dataframe to be used.
            columns (list): The columns to be used for the contingency table.
        
        Returns:
            np.array: The contingency table.
        '''
        contingency_table = [df.shape[0]] # Total number of persons
        grouped = df.groupby(columns).size().reset_index(name='frequency')
        contingency_table = pd.pivot_table(grouped, index=columns[:-1], columns=columns[-1], values='frequency', fill_value=0, aggfunc=lambda x: x)
        print(contingency_table)
        return contingency_table.to_numpy(dtype=int)
