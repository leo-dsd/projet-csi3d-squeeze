import numpy as np

def predict(positions, neighbor_ids):
    acc = np.zeros(3, dtype=np.float64)
    for w in neighbor_ids:
        acc = acc + positions[w]
    return acc / float(len(neighbor_ids))
