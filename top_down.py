import pandas as pd
from itertools import product
import numpy as np
import time
from collections import deque

from geographic_tree import GeographicTree
from optimizer import OptimizationModel

from utils import manhattan_distance, euclidean_distance, tvd, cosine_similarity
from discretegauss import sample_dgauss, sample_dlaplace

class TopDown:
    '''Represents the top-down approach to implement disclosure control for a tree structured data.
    
    The objective is to add noise to the data using differential privacy inspired in the TopDown algorithm used in 2020 USA census.
    '''
    def __init__(self):
        '''Constructor of the TopDown class.
        
        Attributes:
            data (pd.DataFrame): The data to be processed.
            processed_data (pd.DataFrame): The processed data to be used in the TopDown algorithm if necessary.
            geo_tree (GeographicTree): The geographic tree structure.

            permutation (pd.DataFrame): The permutations of the columns for the contingency vector.

            noise_mechanism (function): The noise generation function. (Discrete Gaussian or Laplace)
            privacy_budgets (list): The privacy parameters for each level in the tree.

            geo_columns (list): The geographic columns used to build the geographic tree.
            queries_columns (list): The query columns to be answered.
            geo_constraints (dict): The geographic constraints for each level in the tree.
            root_constraints (list): The constraints for the root node of the geographic tree.

            output_path (str): The path where the output file will be saved. Default is 'topdown_output.csv'.

            optimizer (OptimizationModel): The optimization model used for estimation.

            distance_metric (str): The distance metric to be used for analysis (manhattan, euclidean, cosine, or None).
        '''
        self.data = None
        self.processed_data = None
        self.geo_tree = None

        self.permutation = None

        self.noise_mechanism = None
        self.privacy_budgets = None

        self.geo_columns = None
        self.queries_columns = None
        self.geo_constraints = None
        self.root_constraints = None

        self.output_path = 'topdown_output.csv'

        self.optimizer = OptimizationModel()

        self.distance_metric = None
    
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

        print(f'Computing permutations for columns {self.queries_columns} ...')
        time1 = time.time()
        self.compute_permutation(self.queries_columns)
        time2 = time.time()
        print(f'Permutations computed with {self.permutation.shape[0]} rows and {self.permutation.shape[1]} columns in {time2-time1} seconds.\n')

        print(f'Constructing Tree...')
        time1 = time.time()
        self.geo_tree = GeographicTree(0, self.geo_constraints, self.distance_metric)
        # Initialize the contingency vector for the root node
        self.geo_tree.contingency_vector = self.geo_tree.construct_contingency_vector(self.data, self.permutation, self.queries_columns)
        self.geo_tree.construct_tree(0, self.data, self.permutation, self.geo_columns, self.queries_columns, self.geo_constraints)
        #Edit Constraint
        if self.root_constraints is not None:
            self.geo_tree.constraints = [(lambda array, value=self.data.shape[0]: constraint(array, value)) for constraint in self.root_constraints]
        time2 = time.time()
        print(f'Finished constructing the tree in {time2-time1} seconds.\n')

    def measurement_phase(self) -> None:
        '''Measurement phase of the TopDown algorithm.
        
        It applies noise to the contingency vector of the geographic tree using the specified noise generation mechanism.
        It considers the privacy parameters (rhos/epsilon) defined in the configuration for each level.
        '''
        if self.distance_metric: self.geo_tree.copy_to_comparative_vector()
        print(f'Measurement phase...')

        print(f'Applying noise using {self.noise_mechanism} privacy parameters {self.privacy_budgets} ...')
        time1 = time.time()
        self.apply_noise(self.geo_tree, self.noise_mechanism, self.privacy_budgets)
        time2 = time.time()
        print(f'Noise applied in {time2-time1} seconds.\n')
        if self.distance_metric: print(f'Distance metric {self.distance_metric} for the noisy contingency vector by levels:\n{self.compare_vectors()}\n')

    def estimation_phase(self) -> None:
        '''Estimation phase of the TopDown algorithm.
        
        It creates the optimization model to estimate the contingency vector using Gurobi.
        The problem is divided in 2 optimization subproblems:
            1. Non-negative estimation of the contingency vector. (Constraints problem)
            2. Non-negative discrete estimation of the previous result. (Rounding problem)
        '''
        if self.distance_metric: self.geo_tree.copy_to_comparative_vector()
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
        if self.distance_metric: print(f'Distance metric {self.distance_metric} for the estimation phase by levels:\n{self.compare_vectors()}\n')

    def root_estimation(self) -> None:
        '''Estimates the contingency vector for the root node of the geographic tree.'''

        x_tilde = self.optimizer.non_negative_real_estimation(self.geo_tree.contingency_vector, self.geo_tree.id, self.geo_tree.constraints)
        self.geo_tree.contingency_vector = self.optimizer.rounding_estimation(x_tilde, self.geo_tree.id, self.geo_tree.constraints)    

    def recursive_estimation(self, node: GeographicTree) -> None:
        '''Recursively estimates the contingency vector for the children nodes of the geographic tree.'''
        
        level = len(node.geographic_values.keys())
        queue = deque([(node, level)])
        time1 = time.time()
        if self.processed_data is None: print(f'Running estimation for {self.geo_columns[level]}...', end=' ')
        while queue:
            node, current_level = queue.popleft()
            if self.processed_data is None and level != current_level:
                print(round(time.time() - time1, 4), 'seconds.')
                level = current_level
                if current_level < len(self.geo_columns):
                    print(f'Running estimation for {self.geo_columns[current_level]}...', end=' ')
                    time1 = time.time()

            if not node.children: continue # Skip nodes without children
            
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

            # Add each child node to the queue for further processing
            for child in node.children:
                queue.append((child, current_level + 1))

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

        print(f'Writing microdata to {self.output_path} ...')
        time1 = time.time()
        # Convert the dictionary to a DataFrame and return
        noisy_df = pd.DataFrame(microdata_dict)
        noisy_df.to_csv(self.output_path, index=False, sep=';')
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
            microdata_dict = {col: [] for col in self.geo_columns+self.queries_columns}
            current_index = 0
            for index, row in self.permutation.iterrows():
                for col in self.queries_columns:
                    # Add the value of the row[col] node.contingency_vector[index] times to the dictionary
                    microdata_dict[col].extend(np.repeat(row[col], node.contingency_vector[index]))
            current_index += 1
            # Add the geographic information for the current node
            for key, val in node.geographic_values.items():
                microdata_dict[key] = list(np.repeat(val, len(microdata_dict[self.queries_columns[0]])))
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

    def apply_noise(self, node: GeographicTree, mechanism, privacy_parameters: list) -> None:
        '''Applies noise to the tree contingency vectors using the specified mechanism.
        
        Args:
            mechanism (function): The noise generation function.
            privacy_parameters (list): The privacy parameters for each level.
        '''
        if node is not None:
            node.apply_noise(mechanism, privacy_parameters)

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

    def compare_vectors(self) -> dict:
        '''Compares the contingency vector with the comparative vector at each level of the tree. 
        It uses the given distance metric to measure the difference.
        
        Returns:
            dict: A dictionary with the distance metric for each level of the tree.
        '''
        match self.distance_metric:
            case 'manhattan':
                distance_function = manhattan_distance
            case 'euclidean':
                distance_function = euclidean_distance
            case 'tvd':
                distance_function = tvd
            case 'cosine':
                distance_function = cosine_similarity
            case _:
                raise ValueError(f'Unknown distance metric: {self.distance_metric}, choose from manhattan, euclidean, tvd or None.')
        self.geo_tree.compute_distance_metric(distance_function)
        return self.geo_tree.get_distance_metric_by_level()
    
    def run(self) -> pd.DataFrame:
        '''Runs the TopDown alogorithm
        
        Returns:
            pd.DataFrame: The final dataframe with the DP-data.
        '''
        if self.processed_data is not None:
            print(f'Running TopDown algorithm with processed data...\n')
            return self.resume_run()
        else:
            print(f'Running TopDown alogorithm from scratch...\n')
            self.init_routine()
            self.measurement_phase()
            self.estimation_phase()
            return self.construct_microdata()
    
    def load_state(self) -> None:
        '''Loads the state of a previous run of the TopDown algorithm from a file.'''
        self.compute_permutation(self.queries_columns)
        self.geo_tree = GeographicTree(0)
        self.geo_tree.contingency_vector = self.geo_tree.construct_contingency_vector(self.processed_data, self.permutation, self.queries_columns)
        self.geo_tree.construct_tree(0, self.processed_data, self.permutation, self.geo_columns, self.queries_columns, self.geo_constraints)

    def extend_tree(self) -> tuple[list, int]:
        '''Extends the tree to include the new data.
        
        Returns:
            list (int, list(GeographicTree)): A list of tuples where each tuple contains the level and a list of nodes at that level.
            int: The level of the last level processed in a previous run of the algorithm.
        '''
        level_nodes, last_processed_level = self.geo_tree.extend_tree(self.data, self.permutation, self.geo_columns, self.queries_columns, self.geo_constraints)
        self.data = None
        return level_nodes, last_processed_level

    def resume_measurement_phase(self, level_nodes, last_processed_level) -> None:
        '''Resumes the measurement phase of the TopDown algorithm from a previous state.
        
        It adds noise to the contingency vector of the new geographic nodes added to the tree.

        Args:
            level_nodes (list): A list of tuples where each tuple contains the level and a list of nodes at that level.
            last_processed_level (int): The level of the last level processed in a previous run of the algorithm.
        '''
        _, nodes_to_noisify = level_nodes[last_processed_level+1]
        privacy_parameters_to_use = self.privacy_budgets[last_processed_level+1:]

        for node in nodes_to_noisify:
            self.apply_noise(node, self.noise_mechanism, privacy_parameters_to_use)

    def resume_estimation_phase(self, level_nodes, last_processed_level) -> None:
        '''Resumes the estimation phase of the TopDown algorithm from a previous state.
        
        It estimates the contingency vector of the new geographic nodes added to the tree.

        Args:
            level_nodes (list): A list of tuples where each tuple contains the level and a list of nodes at that level.
            last_processed_level (int): The level of the last level processed in a previous run of the algorithm.
        '''
        _, nodes_to_estimate = level_nodes[last_processed_level]
        for node in nodes_to_estimate:
            self.recursive_estimation(node)

    def resume_run(self) -> pd.DataFrame:
        '''Resumes the run of the TopDown algorithm from a previous state.
        
        Returns:
            pd.DataFrame: The final dataframe with the DP-data.
        '''
        time1 = time.time()
        print(f'Recovering state from previous run considering processed data...')
        self.load_state()
        print(f'Finished recovering state in {time.time()-time1} seconds.\n')

        time1 = time.time()
        print(f'Extending the tree with new data until reaching {self.geo_columns[-1]} granularity...')
        level_nodes, last_processed_level = self.extend_tree()
        print(f'Finished extending the tree in {time.time()-time1} seconds.\n')

        time1 = time.time()
        print(f'Running measurement phase for the new data...')
        self.resume_measurement_phase(level_nodes, last_processed_level)
        print(f'Finished measurement phase in {time.time()-time1} seconds.\n')

        time1 = time.time()
        print(f'Running estimation phase for the new data...')
        print(f'Starting at level of {self.geo_columns[last_processed_level]}...')
        self.resume_estimation_phase(level_nodes, last_processed_level)
        print(f'Finished estimation phase in {time.time()-time1} seconds.\n')
        
        return self.construct_microdata()


    def set_privacy_parameters(self, privacy_parameters: list) -> None:
        '''Sets the privacy parameters for the TopDown algorithm.
        
        Args:
            privacy_parameters (list): The privacy parameters to be used.
        '''
        self.privacy_budgets = privacy_parameters

    def set_geo_columns(self, geo_columns: list) -> None:
        '''Sets the geographic columns for the TopDown algorithm.
        
        Args:
            geo_columns (list): The geographic columns to be used.
        '''
        self.geo_columns = geo_columns

    def set_queries(self, queries: list) -> None:
        '''Sets the query columns for the TopDown algorithm.
        
        Args:
            queries (list): The query columns to be used.
        '''
        self.queries_columns = queries

    def set_geo_constraints(self, geo_constraints: dict) -> None:
        '''Sets the geographic constraints for the TopDown algorithm.
        
        Args:
            geo_constraints (dict): The geographic constraints to be used.
        '''
        self.geo_constraints = geo_constraints
    
    def set_root_constraints(self, root_constraints: list) -> None:
        '''Sets the root constraints for the TopDown algorithm.
        
        Args:
            root_constraints (list): The root constraints to be used.
        '''
        self.root_constraints = root_constraints

    def set_distance_metric(self, distance_metric: str) -> None:
        '''Sets the distance metric for the TopDown algorithm.
        
        Args:
            distance_metric (str): The distance metric to be used (manhattan, euclidean, cosine, or None).
        '''
        self.distance_metric = distance_metric

    def read_data(self, data_path: str, sep=',') -> None:
        '''Sets the data for the TopDown algorithm.
        
        Args:
            data_path (str): The path to the data file in csv to be processed.
            sep (str): The separator used in the csv file. Default is ','.
        '''
        if not self.queries_columns:
            raise ValueError("Queries columns must be set before loading data.")
        if not self.geo_columns:
            raise ValueError("Geographic columns must be set before loading data.")
        
        print(f'Loading data from {data_path} with columns {self.geo_columns+self.queries_columns} ...')
        time1 = time.time()
        self.data = pd.read_csv(data_path, usecols=self.geo_columns+self.queries_columns, sep=sep)
        time2 = time.time()
        print(f'Data loaded in {time2 - time1} seconds.')
        print(f'Data loaded with {self.data.shape[0]} rows and {self.data.shape[1]} columns.\n')

    def read_processed_data(self, data_path: str, sep=',') -> None:
        '''Reads the processed data from a file.
        
        Args:
            data_path (str): The path to the processed data file.
            sep (str): The separator used in the csv file. Default is ','.
        '''
        if not self.queries_columns:
            raise ValueError("Queries columns must be set before loading data.")
        if not self.geo_columns:
            raise ValueError("Geographic columns must be set before loading data.")
        
        print(f'Reading processed data from {data_path} ...')
        time1 = time.time()
        self.processed_data = pd.read_csv(data_path, sep=sep)
        time2 = time.time()
        print(f'Processed data loaded in {time2 - time1} seconds.')
        print(f'Processed data loaded with {self.data.shape[0]} rows and {self.data.shape[1]} columns.\n')
    
    def set_output_path(self, output_path: str) -> None:
        '''Sets the output path for the TopDown algorithm.
        
        Args:
            output_path (str): The path where the output file will be saved.
        '''
        self.output_path = output_path
