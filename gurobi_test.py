import gurobipy as gp
from geographic_tree import GeographicTree
import numpy as np


class OptimizationModel:
    def __init__(self):
        self.geo_tree = self.init_tree()
        # Initialize the optimization model
        self.equality_constraints = []
        self.inequality_constraints = []
    
    def init_tree(self):
        # root node
        u_de_chile = GeographicTree(0)
        u_de_chile.contingency_vector = np.array([35, 17])

        # children nodes
        fcfm = GeographicTree(1)
        fcfm.contingency_vector = np.array([22, 9])

        fdm = GeographicTree(2)
        fdm.contingency_vector = np.array([8, 8])

        # grandchildren nodes
        dcc = GeographicTree(3)
        dcc.contingency_vector = np.array([16, 8])

        dii = GeographicTree(4)
        dii.contingency_vector = np.array([5, 2])

        medi = GeographicTree(5)
        medi.contingency_vector = np.array([10, 6])

        obstetricia = GeographicTree(6)
        obstetricia.contingency_vector = np.array([1, 1])

        # Construct the tree
        u_de_chile.add_child(fcfm)
        u_de_chile.add_child(fdm)

        fcfm.add_child(dcc)
        fcfm.add_child(dii)
        fdm.add_child(medi)
        fdm.add_child(obstetricia)

        return u_de_chile