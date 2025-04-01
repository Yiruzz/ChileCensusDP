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
        '''
        self.id = id
        self.children = []
        self.contingency_table = None

    def add_child(self, child):
        '''Adds a child node to the current node.'''
        self.children.append(child)

    def set_contingency_table(self, contingency_table):
        '''Sets the contingency table for the current node.'''
        self.contingency_table = contingency_table

    def __str__(self):
        '''Returns a string representation of the GeographicTree object.'''
        return f"GeographicTree({self.name})"
    
