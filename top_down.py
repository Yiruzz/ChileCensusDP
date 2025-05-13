import pandas as pd
from itertools import product
import numpy as np
import time
import gurobipy as gp

from config import DATA_PATH, GEO_COLUMNS, QUERIES, MECHANISM, PRIVACY_PARAMETERS, OUTPUT_PATH, OUTPUT_FILE
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
            privacy_budgets (list): The privacy parameters for each level in the tree.
            optimizer (OptimizationModel): The optimization model used for estimation.
        '''
        self.data = None
        self.geo_tree = None

        self.permutation = None

        self.noise_mechanism = None
        self.sensitivity = None
        self.privacy_budgets = PRIVACY_PARAMETERS

        self.optimizer = OptimizationModel()
    
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
        
        # Sort by the columns to ensure a consistent order
        self.permutation.sort_values(by=columns, inplace=True)
        self.permutation.reset_index(drop=True, inplace=True)

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
        self.geo_tree.construct_tree(0, self.data, self.permutation)
        #Edit Constraint
        self.geo_tree.constraints = [lambda x: x.sum() == self.data.shape[0]]
        
        time2 = time.time()
        print(f'Finished constructing the tree in {time2-time1} seconds.\n')

    def measurement_phase(self) -> None:
        '''Measurement phase of the TopDown algorithm.
        
        It applies noise to the contingency vector of the geographic tree using the specified noise generation mechanism.
        It considers the privacy parameters (rhos/epsilon) defined in the configuration for each level.
        '''
        print(f'Measurement phase...')
        self.set_mechanism(MECHANISM)

        print(f'Applying noise using {MECHANISM} mechanism with privacy parameters {self.privacy_budgets} ...')
        time1 = time.time()
        self.apply_noise(self.noise_mechanism, self.privacy_budgets)
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
        print(f'Running estimation for root node...')
        time1 = time.time()
        self.root_estimation()
        time2 = time.time()
        print(f'Finished estimating the solution for root node in {time2-time1} seconds.\n')

        print(f'Running estimation for children nodes recursively...')
        time1 = time.time()
        self.recursive_estimation(self.geo_tree)
        time2 = time.time()
        print(f'Finished estimating the solution for children nodes in {time2-time1} seconds.\n')

    def root_estimation(self) -> None:
        '''Estimates the contingency vector for the root node of the geographic tree.'''

        x_tilde = self.optimizer.non_negative_real_estimation(self.geo_tree.contingency_vector, self.geo_tree.id, self.geo_tree.constraints)
        self.geo_tree.contingency_vector = self.optimizer.rounding_estimation(x_tilde, self.geo_tree.id, self.geo_tree.constraints)    

    def recursive_estimation(self, node: GeographicTree) -> None:
        '''Recursively estimates the contingency vector for the children nodes of the geographic tree.'''
        
        if not node.children: return # Base case

        childs_contingency_vectors = [child.contingency_vector for child in node.children]
        joint_contingency_vector = np.concatenate(childs_contingency_vectors)

        # Construct the new constraints for the joint contingency vector
        constraints = []
        vectors_length = self.permutation.shape[0]
        start = 0
        for child in node.children:
            end = start + vectors_length
            for constraint in child.constraints:
                # NOTE: We need to use default arguments to avoid late binding issues in lambda functions.
                constraints.append(lambda x, s=start, e=end, c=constraint: c(x[s:e]))

            start = end
        
        # Add constraints for consistency of the values of different child nodes
        for index in range(vectors_length):
            constraints.append(lambda joint_vector, s=index, value=node.contingency_vector[index]: 
                               joint_vector[s::vectors_length].sum() == value)
        
        # Estimate the solution for the joint contingency vector
        x_tilde = self.optimizer.non_negative_real_estimation(joint_contingency_vector, node.id, constraints)
        joint_solution = self.optimizer.rounding_estimation(x_tilde, node.id, constraints)
        
        # Split the joint solution into the contingency vectors for each child node
        start = 0
        for child in node.children:
            end = start + vectors_length
            child.contingency_vector = joint_solution[start:end]
            start = end

        # Recursively call the function for each child node
        for child in node.children:
            self.recursive_estimation(child)

    def construct_microdata(self) -> pd.DataFrame:
        '''Constructs the microdata from the contingency vector of the geographic tree.
        
        Returns:
            pd.DataFrame: The constructed microdata.
        '''
        print(f'Constructing microdata from the contingency vector...')
        time1 = time.time()
        # Recursively construct the microdata from the contingency vector of the geographic tree
        microdata_dict = self.recursive_construct_microdata(self.geo_tree, 0)
        time2 = time.time()
        print(f'Finished constructing microdata in {time2-time1} seconds.\n')

        print(f'Writing microdata to {OUTPUT_PATH+OUTPUT_FILE} ...')
        time1 = time.time()
        # Convert the dictionary to a DataFrame and return
        noisy_df = pd.DataFrame(microdata_dict)
        noisy_df.to_csv(OUTPUT_PATH+OUTPUT_FILE, index=False, sep=';')
        time2 = time.time()
        print(f'Finished writing microdata in {time2-time1} seconds.\n')
        print(f'Process finished :)\n')
        return noisy_df

    def recursive_construct_microdata(self, node: GeographicTree, current_tree_level: int) -> pd.DataFrame:

        '''Recursively calls to construct a microdata of all leaves of the tree.
        
        Args:
            node (GeographicTree): The current node of the tree.
            geo_info_list (list): The list of geographic information to be added to the microdata.
        Returns:
            pd.DataFrame: The constructed microdata.
        '''
        microdata_dict = None
        # Base case: if the node is a leaf, construct the microdata for that node
        if not node.children:
            # Create a Diccionary to store the microdata for the current node
            microdata_dict = {col: [] for col in GEO_COLUMNS+QUERIES}
            current_index = 0
            for index, row in self.permutation.iterrows():
                for col in QUERIES:
                    # Add the value of the row[col] node.contingency_vector[index] times to the dictionary
                    microdata_dict[col].extend(np.repeat(row[col], node.contingency_vector[index]))
            current_index += 1
            # Add the geographic information for the current node
            for key, val in node.geographic_values.items():
                microdata_dict[key] = list(np.repeat(val, len(microdata_dict[QUERIES[0]])))
        # Recursive case: if the node has children
        else:
            microdata_dict = {}
            for child in node.children:
                # Recursively call the function for each child node
                child_microdata = self.recursive_construct_microdata(child, current_tree_level + 1)
                # Concatenate the microdata from the child node to the current microdata
                for key in child_microdata.keys():
                    if key in microdata_dict:
                        microdata_dict[key].extend(child_microdata[key])
                    else:
                        microdata_dict[key] = child_microdata[key]
                                
        return microdata_dict
    
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

    def check_correctness(self) -> None:
        '''Checks the correctness of the tree structure considering that its childs sums up to the parent node.
        '''
        if self.geo_tree is not None:
            print(f'Checking correctness of the tree...')
            time1 = time.time()
            self.check_correctness_node(self.geo_tree)
            time2 = time.time()
            print(f'Finished checking correctness in {time2-time1} seconds.\n')


    def check_correctness_node(self, node) -> None:
        '''Checks that the sum of the values of the current node are equal to the sum of the values of its children.
        '''
        if node.children:
            # Check if the sum of the contingency vectors of the children nodes is equal to the parent node's contingency vector
            node_sum = np.sum(node.contingency_vector)
            children_sum = 0
            for child in node.children:
                children_sum += np.sum(child.contingency_vector)

            if node_sum != children_sum:            
                print(f'Error: The sum of the contingency vectors of the children nodes is not equal to the parent node\'s contingency vector.')
                print(f'Parent node contingency vector: {node.contingency_vector}')
                return
            else:
                for child in node.children:
                    self.check_correctness_node(child)

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
