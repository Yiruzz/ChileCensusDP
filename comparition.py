from top_down import TopDown
import numpy as np
from utils import tvd

def main():

    GEO_COLUMNS = ['REGION', 'PROVINCIA', 'COMUNA', 'DC', 'ZC_LOC']
    PROCESS_UNTIL = 'COMUNA'
    GEO_COLUMNS_TO_USE = GEO_COLUMNS[:GEO_COLUMNS.index(PROCESS_UNTIL) + 1]
    QUERIES = ['P08', 'P09'] # Sex and Age

    DATA_PATH = 'data/csv-personas-censo-2017/microdato_censo2017-personas/Microdato_Censo2017-Personas.csv'
    DATA_PATH_PROCESSED = 'data/out/personas_noisy_microdata_COMUNA_P08_P09.csv'

    real_data = TopDown()
    real_data.set_geo_columns(GEO_COLUMNS_TO_USE)
    real_data.set_queries(QUERIES)
    real_data.read_data(DATA_PATH, sep=';')
    real_data.init_routine()

    noisy_data = TopDown()
    noisy_data.set_geo_columns(GEO_COLUMNS_TO_USE)
    noisy_data.set_queries(QUERIES)
    noisy_data.read_data(DATA_PATH_PROCESSED, sep=';')
    noisy_data.init_routine()

    # Compare the trees
    tvd_by_level = compare_trees_by_tvd(real_data.geo_tree, noisy_data.geo_tree)

    # Print the results
    print("TVD by level:")
    for level, tvd in tvd_by_level.items():
        print(f"Level {level}: Mean TVD = {tvd:.4f}")

def compare_trees_by_tvd(tree1, tree2) -> dict:
    '''Compares two trees using Total Variation Distance (TVD) per tree level.
    
    Args:
        tree1 (GeographicTree): The first tree to compare.
        tree2 (GeographicTree): The second tree to compare.
    
    Returns:
        dict: A dictionary where keys are levels and values are the mean TVD for that level.
    '''
    tvd_by_level = {}

    # Iterate over levels of both trees
    for (level1, nodes1), (level2, nodes2) in zip(tree1.iterate_by_levels(), tree2.iterate_by_levels()):
        if level1 != level2:
            raise ValueError(f"Tree levels do not match: {level1} != {level2}")

        # Compute TVD for corresponding nodes
        tvds = []
        for node1, node2 in zip(nodes1, nodes2):
            if node1.contingency_vector is not None and node2.contingency_vector is not None:
                node_tvd = tvd(node1.contingency_vector, node2.contingency_vector)
                tvds.append(node_tvd)

        # Compute the mean TVD for this level
        if tvds:
            tvd_by_level[level1] = np.mean(tvds)

    return tvd_by_level

if __name__ == "__main__":
    main()