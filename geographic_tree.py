import numpy as np
import pandas as pd

from config import QUERIES, GEO_CONSTRAINTS

class GeographicTree:
    '''Represents a tree structure for geographic data. Each node can have multiple children.'''
    def __init__(self, id):
        '''Constructor of the GeographicTree class.
        
        Args:
            id (int): The ID of the geographic entity represented by this node.
        
        Attributes:
            id (int): The ID of the geographic entity.
            children (list): A list of child nodes.
            contingency_table (np.array): The contingency table associated with this node.
            constraints (list): The constraints associated with this node.
        '''
        self.id = id
        self.children = []
        self.contingency_vector = None

        self.comparative_vector = None
        self.TVD = None

        self.constraints = None

    def add_child(self, child):
        '''Adds a child node to the current node.'''
        self.children.append(child)

    def construct_contingency_vector(self, df: pd.DataFrame, permutation) -> np.array:
        '''Constructs the contingency vector for the permutation saved.
        
        Args:
            df (pd.DataFrame): The dataframe to calculate the contingency vector.
            permutation (pd.DataFrame): A dataframe that have all the possible combinations of the columns unique values.
               
        Returns:                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                
            np.array: The contingency vector.
        '''
        # Group the data by the permutation columns and count occurrences
        grouped = df.groupby(QUERIES).size().reset_index(name='frequency')

        # Merge to get frequencies that are not present in the given data.
        merged = pd.merge(permutation, grouped, how='left', on=QUERIES).fillna(0)

        # Pivot vector to create the contingency vector
        contingency_vector = pd.pivot_table(
            merged,
            index=QUERIES[:-1], 
            columns=QUERIES[-1], 
            values='frequency', 
            fill_value=0, 
            aggfunc=lambda x: x)
        
        # Return the contingency vector as a numpy array
        return contingency_vector.to_numpy(dtype=int).flatten()
    
    def construct_tree(self, geo_labels: list, df: pd.DataFrame, permutation: pd.DataFrame) -> None:
        '''Constructs the geographic tree based on the provided labels and dataframe.
        
        Args:
            geo_labels (list): The labels for the geographic locations.
            df (pd.DataFrame): The dataframe containing the data.
            permutation (pd.DataFrame): A dataframe that have all the possible combinations of the columns unique values.
        '''
        if geo_labels:
            location_ids = df[geo_labels[0]].unique()

            for location_id in location_ids:
                # Filter the dataframe for the current location ID
                filtered_df = df[df[geo_labels[0]] == location_id]
                
                # Create a new child node with the filtered data
                child_node = GeographicTree(location_id)

                # Add edit constraints for the child node       
                child_node.constraints = [(lambda array, value=filtered_df.shape[0]: constraint(array, value)) for constraint in GEO_CONSTRAINTS[geo_labels[0]]]

                # Construct the contingency vector for the child node
                child_node.contingency_vector = self.construct_contingency_vector(filtered_df, permutation)

                # Recursively construct childs for the child node
                child_node.construct_tree(geo_labels[1:], filtered_df, permutation)
                
                # Add the child node to the current node
                self.add_child(child_node)

    def apply_noise(self, mechanism, rhos: float) -> None:
        '''Applies noise to the contingency vector using the specified mechanism. Also calls the same method for all child nodes.
        
        Args:
            mechanism (function): The noise generation function.
            rho (float): The privacy parameter.
        '''
        if self.contingency_vector is not None and rhos:
            mechanism(self.contingency_vector, rhos[0])
        
        for child in self.children:
            child.apply_noise(mechanism, rhos[1:])

    def count_nodes(self) -> int:
        '''Counts the number of nodes in the tree.
        
        Returns:
            int: The number of nodes in the tree.
        '''
        count = 1
        for child in self.children:
            count += child.count_nodes()
        return count
    
    def compare_vectors(self) -> float:
        '''Compares the contingency vector with the comparative vector. It uses Total Variation Distance (TVD) to measure the difference.
        
        Returns:
            float: The Total Variation Distance (TVD) between the contingency vector and the comparative vector.
        '''
        total_tvd = 0.0

        if self.contingency_vector is not None and self.comparative_vector is not None:
            # Normalize the vectors to represent probability distributions
            contingency_sum = np.sum(self.contingency_vector)
            comparative_sum = np.sum(self.comparative_vector)
            p = self.contingency_vector / contingency_sum
            q = self.comparative_vector / comparative_sum

            # Compute the Total Variation Distance for the current node
            tvd = 0.5 * np.sum(np.abs(p - q))
            self.TVD = tvd

        # # Recursively compute TVD for child nodes
        # for child in self.children:
        #     total_tvd += child.compare_vectors()
    
    def copy_to_comparative_vector(self) -> None:
        '''Copies the contingency vector to the comparative vector. It also calls the same method for all child nodes.'''
        if self.contingency_vector is not None:
            self.comparative_vector = np.copy(self.contingency_vector)
        
        for child in self.children:
            child.copy_to_comparative_vector()
