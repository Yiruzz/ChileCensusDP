import pandas as pd
import numpy as np
import itertools

class DataHandler:
    '''Handles the data loading and processing for the TopDown algorithm.
    '''
    def __init__(self):
        '''Constructor of the DataHandler class.'''
        self.data = None
        self.permutation = None
        self.permutation_columns = None
    
    def load_data(self, file_path: str, columns_to_read=None, sep=';') -> None:
        '''Loads the data from a CSV file.
        
        Args:
            file_path (str): The path to the CSV file.
        '''
        self.data = pd.read_csv(file_path, sep=sep, usecols=columns_to_read)

    def compute_permutations(self, columns: list) -> None:
        '''Computes the permutations of the given columns.
        
        Args:
            columns (list): The columns to be permuted.
        '''
        # Get unique values for each column
        unique_values = [self.data[col].unique() for col in columns]

        # Generate all possible combinations (Cartesian product)
        self.permutation = pd.DataFrame(
            list(itertools.product(*unique_values)), 
            columns=columns)
        
        self.permutation_columns = columns
        
    def construct_contingency_table(self, df: pd.DataFrame) -> np.array:
        '''Constructs the contingency table for the permutation saved.
        
        Returns:                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                
            np.array: The contingency table.
        '''
        # Group the data by the permutation columns and count occurrences
        grouped = df.groupby(self.permutation_columns).size().reset_index(name='frequency')

        # Merge to get frequencies that are not present in the given data.
        merged = pd.merge(self.permutation, grouped, how='left', on=self.permutation_columns).fillna(0)

        # Pivot table to create the contingency table
        contingency_table = pd.pivot_table(
            merged,
            index=self.permutation_columns[:-1], 
            columns=self.permutation_columns[-1], 
            values='frequency', 
            fill_value=0, 
            aggfunc=lambda x: x)
        
        # Return the contingency table as a numpy array
        return contingency_table.to_numpy(dtype=int)