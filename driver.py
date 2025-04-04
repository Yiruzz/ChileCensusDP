import pandas as pd
import numpy as np

from geographic_tree import GeographicTree
from top_down import TopDown
from data_handler import DataHandler

def construct_childs(node: GeographicTree, geo_labels: list, df: pd.DataFrame, data_handler: DataHandler) -> None:
    '''Constructs the childs of a node in the geographic tree based on the provided labels and dataframe.
    
    Args:
        node (GeographicTree): The node to construct the childs for.
        geo_labels (list): The labels for the geographic locations.
        df (pd.DataFrame): The dataframe containing the data.
        data_handler (DataHandler): The data handler object.
    '''
    if geo_labels:
        location_ids = df[geo_labels[0]].unique()

        for location_id in location_ids:
            # Filter the dataframe for the current location ID
            filtered_df = df[df[geo_labels[0]] == location_id]
            
            # Create a new child node with the filtered data
            child_node = GeographicTree(location_id)

            # Construct the contingency vector for the child node
            child_node.contingency_vector = data_handler.construct_contingency_vector(filtered_df)

            # Recursively construct childs for the child node
            construct_childs(child_node, geo_labels[1:], filtered_df, data_handler)
            
            # Add the child node to the current node
            node.add_child(child_node)
        
def main():
    '''Main function to run the TopDown algorithm.'''

    data_handler = DataHandler()

    # Load the data
    columns_to_keep = ['REGION', 'PROVINCIA', 'COMUNA', 'DC', 'AREA', 'ZC_LOC', 'ID_ZONA_LOC', 'P08', 'P09']
    geo_data = columns_to_keep[:6]

    data_handler.load_data('data/csv-personas-censo-2017/microdato_censo2017-personas/Microdato_Censo2017-Personas.csv', columns_to_read=columns_to_keep, sep=';')
   
    top_down = TopDown()

    # Load the tree
    tree = GeographicTree(0)
    
    # Construct the permutations of the contingency vector
    data_handler.compute_permutations(columns_to_keep[6+1:])

    # Construct the geographic tree
    construct_childs(tree, geo_data, data_handler.data, data_handler)
    
    # Construct the contingency vector for the root node
    tree.contingency_vector = data_handler.construct_contingency_vector(data_handler.data)
    
    # Set the data and tree
    top_down.set_data(data_handler.data)
    top_down.set_tree(tree)
    
    # Run the TopDown algorithm
    #top_down.run()

if __name__ == "__main__":
    main()