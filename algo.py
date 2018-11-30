from graph import Graph
from utils import lat_long_dist

def build_business_graph(businesses, category_sequence, min_rating=-1):
    g = Graph()
    for b in businesses:
        if b.rating >= min_rating:
            g.add_node(b)

    valid_seqs = set()
    # Generate all possible sequences of categories for faster lookup
    for i in range(len(category_sequence) - 1):
        for j in range(len(category_sequence[i])):
            for k in range(len(category_sequence[i + 1])):
                valid_seqs.add((category_sequence[i][j], category_sequence[i + 1][k]))

    def is_valid_category_seq(bizA, bizB):
        for catA in bizA.categories:
            for catB in bizB.categories:
                        if (catA, catB) in valid_seqs:
                            return True
        return False

    def build_properties(nodeA, nodeB):
        return {"dist": lat_long_dist(nodeA.latitude, nodeA.longitude, nodeB.latitude, nodeB.longitude)}

    g.auto_build_edges(is_valid_category_seq, build_properties)

    return g
