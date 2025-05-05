import gurobipy as gp
import numpy as np

from config import OUTPUT_PATH

class OptimizationModel:
    '''Represents an optimization model for a specific optimization problem of the geographic Tree using Gurobi.'''

    def __init__(self):
        self.model = None

    def non_negative_real_estimation(self, contingency_vector, id_node, constraints=None):
        '''Non-negative estimation of the contingency vector.
        
        This method creates a Gurobi model to estimate the contingency vector using non-negative constraints.
        '''
        self.model = gp.Model(f'NonNegativeRealEstimation. NodeID: {id_node}')
        self.model.setParam('OutputFlag', 0)  # Suppress Gurobi output

        n = len(contingency_vector)
        
        # Decision variables
        x = self.model.addMVar(shape=n, lb=0.0, name="x")

        # Objective function: minimize the sum of squared differences (L2 norm squared)
        self.model.setObjective(gp.quicksum((x[i] - contingency_vector[i]) * (x[i] - contingency_vector[i]) for i in range(n)), gp.GRB.MINIMIZE)

        # Additional constraints
        for i, constraint in enumerate(constraints):
            self.model.addConstr(constraint(x), name=f"GivenConstraint_{i}")

        # Run the model
        self.model.optimize()

        # Check for infeasibility
        if self.model.status == gp.GRB.INFEASIBLE:
            print(f"Model is infeasible for node {id_node}.")
            self.model.write(OUTPUT_PATH+"infeasible_model.lp")
            return None

        return x.X

    
    def rounding_estimation(self, x_tilde, id_node, constraints=None):
        '''Rounding estimation of the contingency vector.
        
        This method creates a Gurobi model to estimate the non negative discrete contingency vector.
        '''
        self.model = gp.Model(f'RoundingEstimation. NodeID: {id_node}')
        self.model.setParam('OutputFlag', 0)
        
        n = len(x_tilde)
        
        # Rounding problem
        x_floor = np.floor(x_tilde)
        residual_round = x_tilde - x_floor
        
        y = self.model.addMVar(shape=n, vtype=gp.GRB.BINARY, name="y")

        # Objective function: minimize the sum of squared differences (L2 norm squared)
        self.model.setObjective(gp.quicksum((residual_round[i] - y[i]) * (residual_round[i] - y[i]) for i in range(n)), gp.GRB.MINIMIZE)

        x_rounded = x_floor + y

        # Additional constraints
        for i, constraint in enumerate(constraints):
            self.model.addConstr(constraint(x_rounded), name=f"GivenConstraint_{i}")
        
        # Run the model
        self.model.optimize()

        # Check for infeasibility
        if self.model.status == gp.GRB.INFEASIBLE:
            print(f"Model is infeasible for node {id_node}.")
            self.model.write(OUTPUT_PATH+"infeasible_model.lp")
            return None
        
        return x_floor + y.X

