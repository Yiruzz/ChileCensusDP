from collections import deque
import numpy as np
import pandas as pd
from collections import deque


class GeographicTree:
    '''Represents a tree structure for geographic data. Each node can have multiple children.'''
    def __init__(self, id, constraints=None, distance_metric=None):
        '''Constructor of the GeographicTree class.
        
        Args:
            id (int): The ID of the geographic entity represented by this node.
        
        Attributes:
            id (int): The ID of the geographic entity.
            labels (dict): A map with the values of the geographic entity that represents this node.
            children (list): A list of child nodes.
            contingency_table (np.array): The contingency table associated with this node.
            constraints (list): The constraints associated with this node.

            comparative_vector (np.array): The comparative vector associated with this node.
            distance_metric (float): The distance metric associated with this node.
        '''
        self.id = id
        self.geographic_values = {}
        self.children = []
        self.contingency_vector = None

        self.constraints = constraints

        # NOTE: These are only used when a distance metric is defined in config.py
        self.comparative_vector = None
        self.distance_metric = distance_metric

    def add_child(self, child):
        '''Adds a child node to the current node.'''
        self.children.append(child)

    def construct_contingency_vector(self, df: pd.DataFrame, permutation, queries: list) -> np.array:
        '''Constructs the contingency vector for the permutation saved.
        
        Args:
            df (pd.DataFrame): The dataframe to calculate the contingency vector.
            permutation (pd.DataFrame): A dataframe that have all the possible combinations of the columns unique values.
               
        Returns:                                                                                     
            np.array: The contingency vector.
        '''
        # Group the data by the permutation columns and count occurrences
        grouped = df.groupby(queries).size().reset_index(name='frequency')

        # Merge to get frequencies that are not present in the given data.
        merged = pd.merge(permutation, grouped, how='left', on=queries).fillna(0)

        # Pivot vector to create the contingency vector
        contingency_vector = pd.pivot_table(
            merged,
            index=queries[:-1], 
            columns=queries[-1], 
            values='frequency', 
            fill_value=0, 
            aggfunc=lambda x: x)
        
        # Return the contingency vector as a numpy array
        return contingency_vector.to_numpy(dtype=int).flatten()
    
    def construct_tree(self, current_level: int, df: pd.DataFrame, permutation: pd.DataFrame, geo_columns: list, queries: list, constraints_dict: dict) -> None:
        '''Constructs the geographic tree based on the provided labels and dataframe.
        
        Args:
            current_level (int): The current level of the geographic hierarchy being processed.
            df (pd.DataFrame): The dataframe containing the data.
            permutation (pd.DataFrame): A dataframe that have all the possible combinations of the columns unique values.
            queries (list): A list of queries to be answered.
            geo_columns (list): A list of geographic columns to be used for constructing the tree.
            constraints_dict (dict): A dictionary containing the edit constraints for each geographic column.
        '''
        last_geo_column_index = 0
        for i in geo_columns:
            if i not in df.columns:
                break
            last_geo_column_index += 1
        
        present_geo_columns = geo_columns[:last_geo_column_index]

        if current_level < len(present_geo_columns):
            location_ids = df[present_geo_columns[current_level]].unique()

            for location_id in location_ids:
                # Filter the dataframe for the current location ID
                filtered_df = df[df[present_geo_columns[current_level]] == location_id]
                
                # Create a new child node with the filtered data
                child_node = GeographicTree(location_id)
                for geo_label in present_geo_columns[:current_level+1]:
                    # Set the geographic values for the child node
                    child_node.geographic_values[geo_label] = filtered_df[geo_label].unique()[0]

                # Add edit constraints for the child node       
                child_node.constraints = [(lambda array, value=filtered_df.shape[0]: constraint(array, value)) for constraint in constraints_dict[present_geo_columns[current_level]]]

                # Construct the contingency vector for the child node
                child_node.contingency_vector = self.construct_contingency_vector(filtered_df, permutation, queries)

                # Recursively construct childs for the child node
                child_node.construct_tree(current_level+1, filtered_df, permutation, geo_columns, queries, constraints_dict)
                
                # Add the child node to the current node
                self.add_child(child_node)

    def apply_noise(self, mechanism, rhos: list) -> None:
        '''Applies noise to all the contingency vectors of the tree with the specified mechanism.
        
        The iteration is done in a breath-first manner, starting from the root node and going down by levels of the tree.

        Args:
            mechanism (function): The noise generation function.
            rho (list): A list containing the privacy parameters for each level of the tree.
        '''
        # BFS
        queue = deque([(self, 0)])   
        while queue:
            node, current_level = queue.popleft()

            # Apply noise to the contingency vector of the current node
            if node.contingency_vector is not None:
                mechanism(node.contingency_vector, rhos[current_level])

            # Add the children of the current node to the queue
            for child in node.children:
                queue.append((child, current_level + 1))

    def count_nodes(self) -> int:
        '''Counts the number of nodes in the tree.
        
        Returns:
            int: The number of nodes in the tree.
        '''
        count = 1
        for child in self.children:
            count += child.count_nodes()
        return count
        
    def copy_to_comparative_vector(self) -> None:
        '''Copies the contingency vector to the comparative vector. It also calls the same method for all child nodes.'''
        if self.contingency_vector is not None:
            self.comparative_vector = np.copy(self.contingency_vector)
        
        for child in self.children:
            child.copy_to_comparative_vector()

    def iterate_by_levels(self):
        '''Iterates over the tree level by level and yields nodes at each level.
        
        Returns:
            generator: A generator that yields tuples of (level, list of nodes at that level).
        '''
        queue = deque([(self, 0)])  # Start with the root node and level 0
        current_level = 0
        level_nodes = []

        while queue:
            node, level = queue.popleft()

            # If we move to a new level, yield the nodes from the previous level
            if level != current_level:
                yield current_level, level_nodes
                current_level = level
                level_nodes = []

            # Add the current node to the current level
            level_nodes.append(node)

            # Add the children of the current node to the queue
            for child in node.children:
                queue.append((child, level + 1))

        # Yield the last level
        if level_nodes:
            yield current_level, level_nodes

    def compute_distance_metric(self, distance_function) -> None:
        '''Computes the distance metric for the node and its children.
        
        Args:
            distance_metric (function): The distance metric function to be applied.
        '''
        if self.comparative_vector is not None:
            self.distance_metric = distance_function(self.contingency_vector, self.comparative_vector)
        
        for child in self.children:
            child.compute_distance_metric(distance_function)

    def get_distance_metric_by_level(self) -> dict:
        '''Returns the mean distance metric for each level of the tree.
        
        Returns:
            dict: A dictionary where keys are levels and values are their corresponding mean of that metric values.
        '''
        metric_by_level = {}

        for level, nodes in self.iterate_by_levels():
            metrics = [node.distance_metric for node in nodes if node.distance_metric is not None]
            if metrics:
                metric_by_level[level] = np.mean(metrics)

        return metric_by_level

    def extend_tree(self, raw_data: pd.DataFrame, permutation: pd.DataFrame, geo_columns: list, constraints_dict: dict) -> tuple[list, int]:
        '''Extends the tree with the raw data and the permutation.
        
        Args:
            raw_data (pd.DataFrame): The raw data to be used for extending the tree.
            permutation (pd.DataFrame): A dataframe that have all the possible combinations of the columns unique values.

        Returns:
            list (int, list(GeographicTree)): A list of tuples where each tuple contains the level and a list of nodes at that level.
            int: The level of the last level processed in a previous run of the algorithm.
        '''
        level_nodes = list(self.iterate_by_levels())
        last_processed_level, last_processed_nodes = level_nodes[-1]
        new_level = last_processed_level
        
        # Case no new nodes to process
        if last_processed_level >= len(geo_columns):
            raise ValueError("The tree has already been fully processed. Consider incrementing the level of granularity")
        
        # Iterate over the new geographic labels to process to create new nodes
        for label_to_process in geo_columns[last_processed_level:]:
            new_childs = []
            for processed_node in last_processed_nodes:
                # Filter the raw data using the dictionary of the processed node
                for key, value in processed_node.geographic_values.items():
                    filtered_df = raw_data[raw_data[key] == value]
            
                for location_id in filtered_df[label_to_process].unique():
                    # Filter the raw data for the current location ID
                    filtered_df = filtered_df[filtered_df[label_to_process] == location_id]
                    
                    # Create a new child node with the filtered data
                    child_node = GeographicTree(location_id)
                    child_node.geographic_values = processed_node.geographic_values.copy()
                    child_node.geographic_values[label_to_process] = location_id

                    # Add edit constraints for the child node       
                    child_node.constraints = [(lambda array, value=filtered_df.shape[0]: constraint(array, value)) for constraint in constraints_dict[label_to_process]]

                    # Construct the contingency vector for the child node
                    child_node.contingency_vector = self.construct_contingency_vector(filtered_df, permutation)

                    # Add the child node to the current node
                    processed_node.add_child(child_node)

                    # Add the child node to the list of new childs
                    new_childs.append(child_node)

        
            last_processed_nodes = new_childs.copy()
            new_level += 1
            level_nodes.append((new_level, last_processed_nodes))

        return level_nodes, last_processed_level

