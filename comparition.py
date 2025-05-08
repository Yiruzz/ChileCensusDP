from top_down import TopDown
import numpy as np
from utility import tvd

def main():
    init_data = TopDown()
    init_data.init_routine()

    out_data = TopDown()
    out_data.init_routine('C:/Users/artur/Desktop/Memoria/ChileCensusDP/data/out/personas_noisy_microdata_P08P09.csv')

    # Compare the trees
    tvd_by_level = compare_trees_by_tvd(init_data.geo_tree, out_data.geo_tree)

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