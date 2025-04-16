import gurobipy as gp
import numpy as np

class OptimizationModel:
    '''Represents an optimization model for a specific optimization problem of the geographic Tree using Gurobi.'''

    def __init__(self):
        self.model = None

    def non_negative_real_estimation(self, contingency_vector, id_node, constraints=None):
        '''Non-negative estimation of the contingency vector.
        
        This method creates a Gurobi model to estimate the contingency vector using non-negative constraints.
        '''
        self.model = gp.Model(f'NonNegativeRealEstimation. NodeID: {id_node}')
        n = len(contingency_vector)
        
        # Decision variables
        x = self.model.addMVar(shape=n, lb=0.0, name="x")

        # NOTE: The auxiliary variables are not necessary if we want to use another metric for distance. (Minimum squares)
        # Auxiliary variables for absolute differences
        abs_diff = self.model.addMVar(shape=n, lb=0.0, name="abs_diff")

        # Add constraints to define abs_diff as |x[i] - contingency_vector[i]|
        self.model.addConstrs((abs_diff[i] >= x[i] - contingency_vector[i] for i in range(n)), name="AbsDiffPos")
        self.model.addConstrs((abs_diff[i] >= contingency_vector[i] - x[i] for i in range(n)), name="AbsDiffNeg")

        # Objective function: minimize the sum of absolute differences
        self.model.setObjective(gp.quicksum(abs_diff), gp.GRB.MINIMIZE)

        # Real value constraints
        for i, constraint in enumerate(constraints):
                self.model.addConstr(constraint(x), name=f"GivenConstraint_{i}")
        
        # Run the model
        self.model.optimize()
        return x.X

    
    def rounding_estimation(self, x_solution, id_node, constraints=None):
        '''Rounding estimation of the contingency vector.
        
        This method creates a Gurobi model to estimate the non negative discrete contingency vector.
        '''
        self.model = gp.Model(f'RoundingEstimation. NodeID: {id_node}')
        
        n = len(x_solution)
        
        # Rounding problem
        x_floor = np.floor(x_solution)
        residual_round = x_solution - x_floor
        
        y = self.model.addMVar(shape=n, vtype=gp.GRB.BINARY, name="y")

        # Auxiliary variables for absolute differences
        abs_diff = self.model.addMVar(shape=n, lb=0.0, name="abs_diff")

        # Restriction: abs_diff = |residual_round - y|
        self.model.addConstr(abs_diff >= residual_round - y)
        self.model.addConstr(abs_diff >= y - residual_round)

        self.model.setObjective(gp.quicksum(abs_diff), gp.GRB.MINIMIZE)

        x_rounded = x_floor + y

        # Real value constraints
        for i, constraint in enumerate(constraints):
                self.model.addConstr(constraint(x_rounded), name=f"GivenConstraint_{i}")
        
        # Run the model
        self.model.optimize()
        return x_floor + y.X

