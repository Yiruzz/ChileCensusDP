import pandas as pd
from itertools import product
import numpy as np
import time
import gurobipy as gp

from config import DATA_PATH, GEO_COLUMNS, QUERIES, MECHANISM, RHOS
from geographic_tree import GeographicTree
from optimizer import OptimizationModel

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
        self.sensitivity = None
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

    def measurement_phase(self) -> None:
        '''Measurement phase of the TopDown algorithm.
        
        It applies noise to the contingency vector of the geographic tree using the specified noise generation mechanism.
        It considers the privacy parameters (rhos/epsilon) defined in the configuration for each level.
        '''
        print(f'Measurement phase...')
        self.set_mechanism(MECHANISM)

        print(f'Applying noise using {MECHANISM} mechanism with privacy parameters {self.rhos} ...')
        time1 = time.time()
        self.apply_noise(self.noise_mechanism, self.rhos)
        time2 = time.time()
        print(f'Noise applied in {time2-time1} seconds.\n')

    def estimation_phase(self) -> None:
        '''Estimation phase of the TopDown algorithm.
        
        It creates the optimization model to estimate the contingency vector using Gurobi.
        The problem is divided in 2 optimization subproblems:
            1. Non-negative estimation of the contingency vector. (Constraints problem)
            2. Non-negative discrete estimation of the previous result. (Rounding problem)
        '''
        print(f'Estimation phase...')
        self.root_estimation()
        self.recursive_estimation()
    
    def root_estimation(self) -> None:
        '''Estimates the contingency vector for the root node of the geographic tree.'''
        print(f'Estimating solution for root node...')
        time1 = time.time()
        
        model = gp.Model("NonNegativeRealEstimationRoot")
        vector_length = len(self.geo_tree.contingency_vector)

        # Desicion variables
        x = model.addMVar(shape=vector_length, lb=0.0, name="x")
        
        # Auxiliary variables for absolute differences
        # NOTE: If we want to use minimum square as the objetive function, auxiliar variables are not necessary.
        abs_diff = model.addMVar(shape=vector_length, lb=0.0, name="abs_diff")
        # Add constraints to define abs_diff as |x[i] - contingency_vector[i]|
        model.addConstrs((abs_diff[i] >= x[i] - self.geo_tree.contingency_vector[i] for i in range(vector_length)), name="AbsDiffPos")
        model.addConstrs((abs_diff[i] >= self.geo_tree.contingency_vector[i] - x[i] for i in range(vector_length)), name="AbsDiffNeg")
        
        # Objective function: minimize the sum of absolute differences
        model.setObjective(abs_diff.sum(), gp.GRB.MINIMIZE)

        # Real value constraint
        model.addConstr(x.sum() == self.data.shape[0], name="EqualityConstraints")

        # Run the model
        model.optimize()
        x_solution = x.X
        
        # Rounding problem
        x_floor = np.floor(x_solution)
        residual_round = x_solution - x_floor
        model = gp.Model("RoundingEstimationRoot")

        y = model.addMVar(shape=vector_length, vtype=gp.GRB.BINARY, name="y")

        # Auxiliary variables for absolute differences
        abs_diff = model.addMVar(shape=vector_length, lb=0.0, name="abs_diff")

        # Restriction: abs_diff = |residual_round - y|
        model.addConstr(abs_diff >= residual_round - y)
        model.addConstr(abs_diff >= y - residual_round)

        model.setObjective(gp.quicksum(abs_diff), gp.GRB.MINIMIZE)

        x_rounded = x_floor + y

        model.addConstr(x_rounded.sum() == self.data.shape[0], name="EqualityConstraints")

        model.optimize()
        solution = x_floor + y.X

        self.geo_tree.contingency_vector = solution
        time2 = time.time()
        print(f'Finished estimating the solution for root node in {time2-time1} seconds.\n')
        print(f'Estimated solution for root node: {solution}.\n')

    def recursive_estimation(self) -> None:
        '''Recursively estimates the contingency vector for the children nodes of the geographic tree.'''
        print(f'Running estimation for children nodes recursively...')
        time1 = time.time()



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
    
    def discrete_laplace(self, contingency_vector: np.array, epsilon: float) -> None:
        '''Applies Laplace noise to the contingency vector.
        
        Args:
            contingency_vector (np.array): The contingency vector to be modified.
            rho (float): The privacy parameter.
        
        Returns:
            np.array: The modified contingency vector with added noise.
        '''
        # TODO: Refactor to generalize the sensitivity
        for i in range(len(contingency_vector)):
            contingency_vector[i] += sample_dlaplace(1/epsilon)
