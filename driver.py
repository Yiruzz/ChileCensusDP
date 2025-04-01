import pandas as pd
import numpy as np

from geographic_tree import GeographicTree
from top_down import TopDown

def construct_childs(node: GeographicTree, geo_labels: list, df: pd.DataFrame) -> None:
    '''Constructs the childs of a node in the geographic tree based on the provided labels and dataframe.
    
    Args:
        node (GeographicTree): The node to construct the childs for.
        geo_labels (list): The labels for the geographic locations.
        df (pd.DataFrame): The dataframe containing the data.
    '''

    if geo_labels:
        location_ids = df[geo_labels[0]].unique()
    else: return

    for location_id in location_ids:
        # Filter the dataframe for the current location ID
        filtered_df = df[df[geo_labels[0]] == location_id]
        
        # Create a new child node with the filtered data
        child_node = GeographicTree(location_id)

        # Construct the contingency table for the child node
        

        # Recursively construct childs for the child node
        construct_childs(child_node, geo_labels[1:], filtered_df)
        
        # Add the child node to the current node
        node.add_child(child_node)

def main():
    '''Main function to run the TopDown algorithm.'''

    # Load the data
    columns_to_keep = ['REGION', 'PROVINCIA', 'COMUNA', 'DC', 'AREA', 'ZC_LOC', 'ID_ZONA_LOC', 'P08', 'P09']
    data = pd.read_csv('data/csv-personas-censo-2017/microdato_censo2017-personas/Microdato_Censo2017-Personas.csv', sep=';', usecols=columns_to_keep)
    
    geo_data = columns_to_keep[:6]
   
    top_down = TopDown()

    # Load the tree
    tree = GeographicTree(0)
    
    # Construct the contingency_table for the root node
    tree.set_contingency_table([data.shape[0]])
    
    construct_childs(tree, geo_data, data)

    # Create an instance of TopDown
    print(top_down.construct_contingency_table(data, ['P08', 'P09']))
    
    # Set the data and tree
    top_down.set_data(data)
    top_down.set_tree(tree)
    
    # Run the TopDown algorithm
    #top_down.run()

if __name__ == "__main__":
    main()