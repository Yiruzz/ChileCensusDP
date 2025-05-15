import numpy as np

def manhattan_distance(vector1, vector2):
    '''Computes the Manhattan distance between two vectors.'''
    if vector1 is not None and vector2 is not None:
        return np.sum(np.abs(vector1 - vector2))
    return None

def euclidean_distance(vector1, vector2):
    '''Computes the Euclidean distance between two vectors.'''
    if vector1 is not None and vector2 is not None:
        return np.sqrt(np.sum((vector1 - vector2) ** 2))
    return None

def tvd(vector1, vector2):
    '''Computes the Total Variation Distance (TVD) between two vectors.'''
    if vector1 is not None and vector2 is not None:
        sum1 = np.sum(vector1)
        sum2 = np.sum(vector2)
        if sum1 == 0 or sum2 == 0: return 0
        p = vector1 / sum1
        q = vector2 / sum2
        return 0.5 * np.sum(np.abs(p - q))
    return None

def cosine_similarity(vector1, vector2):
    '''Computes the Cosine Similarity between two vectors.'''
    if vector1 is not None and vector2 is not None:
        dot_product = np.dot(vector1, vector2)
        norm_a = np.linalg.norm(vector1)
        norm_b = np.linalg.norm(vector2)
        if norm_a == 0 or norm_b == 0: return 0
        return dot_product / (norm_a * norm_b)
    return None