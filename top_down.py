import pandas as pd
from itertools import product
import numpy as np
import time

from config import DATA_PATH, GEO_COLUMNS, QUERIES, MECHANISM, RHOS
from geographic_tree import GeographicTree

from discretegauss import sample_dgauss, sample_dlaplace

class TopDown:
    '''Represents the top-down approach to implement disclosure control for a tree structured data.
    
    The objective is to add noise to the data using differential privacy inspired in the TopDown algorithm used in 2020 USA census.
    '''
    def __init__(self):
        '''Constructor of the TopDown class.
        
        Attributes:
            data (pd.DataFrame): The data to be processed.
            geo_tree (GeographicTree): The geographic tree structure.
            permutation (pd.DataFrame): The permutations of the columns for the contingency vector.
            noise_mechanism (function): The noise generation function. (Discrete Gaussian or Laplace)
            rhos (list): The privacy parameters for each level in the tree.
        '''
        self.data = None
        self.geo_tree = None

        self.permutation = None

        self.noise_mechanism = None
        self.rhos = RHOS
    
    def compute_permutation(self, columns: list) -> None:
        '''Computes the permutations of the given columns.
        
        Args:
            columns (list): The columns to be permuted.
        '''
        # Get unique values for each column
        unique_values = [self.data[col].unique() for col in columns]

        # Generate all possible combinations (Cartesian product)
        self.permutation = pd.DataFrame(
            list(product(*unique_values)), 
            columns=columns)

    def init_routine(self) -> None:
        '''Initialization the routine for the TopDown class.
        
        This method is used to set up the initial parameters for the TopDown algorithm.
        '''
        # Load the data
        time1 = time.time()
        print(f'Loading data from {DATA_PATH} with columns {GEO_COLUMNS+QUERIES} ...')
        self.data = pd.read_csv(DATA_PATH, sep=';', usecols=GEO_COLUMNS+QUERIES)
        time2 = time.time()
        print(f'Data loaded in {time2 - time1} seconds.')
        print(f'Data loaded with {self.data.shape[0]} rows and {self.data.shape[1]} columns.\n')

        print(f'Computing permutations for columns {QUERIES} ...')
        time1 = time.time()
        self.compute_permutation(QUERIES)
        time2 = time.time()
        print(f'Permutations computed with {self.permutation.shape[0]} rows and {self.permutation.shape[1]} columns in {time2-time1} seconds.\n')

        print(f'Constructing Tree...')
        time1 = time.time()
        self.geo_tree = GeographicTree(0)
        # Initialize the contingency vector for the root node
        self.geo_tree.contingency_vector = self.geo_tree.construct_contingency_vector(self.data, self.permutation)
        self.geo_tree.construct_tree(GEO_COLUMNS, self.data, self.permutation)
        time2 = time.time()
        print(f'Finished constructing the tree in {time2-time1} seconds.\n')
    
        self.set_mechanism(MECHANISM)

        print(f'Count before noise: {sum(self.geo_tree.contingency_vector)}')
        print(f'Applying noise using {MECHANISM} mechanism with rhos {self.rhos} ...')
        time1 = time.time()
        self.apply_noise(self.noise_mechanism, self.rhos)
        time2 = time.time()
        print(f'Noise applied in {time2-time1} seconds.\n')
        print(f'Count after noise: {sum(self.geo_tree.contingency_vector)}')


    def set_mechanism(self, mechanism: str) -> None:
        '''Sets the noise generation mechanism.
        
        Args:
            mechanism (str): The noise generation mechanism to be used.
        '''
        if mechanism == 'discrete_gaussian':
            self.noise_mechanism = self.discrete_gaussian
        elif mechanism == 'discrete_laplace':
            self.noise_mechanism = self.discrete_laplace

    def apply_noise(self, mechanism, rhos: float) -> None:
        '''Applies noise to the contingency vector using the specified mechanism.
        
        Args:
            mechanism (function): The noise generation function.
            rho (float): The privacy parameter.
        '''
        if self.geo_tree is not None:
            self.geo_tree.apply_noise(mechanism, rhos)
    
    def discrete_gaussian(self, contingency_vector: np.array, rho: float) -> None:
        '''Applies discrete Gaussian noise to the contingency vector.
        
        Args:
            contingency_vector (np.array): The contingency vector to be modified.
            rho (float): The privacy parameter.
        
        Returns:
            np.array: The modified contingency vector with added noise.
        '''
        for i in range(len(contingency_vector)):
            contingency_vector[i] += sample_dgauss(rho)
    
    def discrete_laplace(self, contingency_vector: np.array, rho: float) -> None:
        '''Applies Laplace noise to the contingency vector.
        
        Args:
            contingency_vector (np.array): The contingency vector to be modified.
            rho (float): The privacy parameter.
        
        Returns:
            np.array: The modified contingency vector with added noise.
        '''
        for i in range(len(contingency_vector)):
            contingency_vector[i] += sample_dlaplace(rho)
