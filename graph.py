class EdgeDoesNotExistException(Exception):
    def __init__(self, nodeA, nodeB):

        message = "Edge from {0} to {1} does not exist!".format(nodeA, nodeB)
        # Call the base class constructor with the parameters it needs
        super(Exception, self).__init__(message)

class Graph:
    def __init__(self):
        self.nodes = set()
        self.edges = {}
        self.edge_properties = {}

    def get_edges(self, node):
        return self.edges.get(node, [])

    def get_edge_properties(self, node1, node2):
        try:
            return self.edge_properties[(node1, node2)]
        except KeyError:
            raise EdgeDoesNotExistException(node1, node2)

    def add_node(self, node):
        self.nodes.add(node)

    def add_edge(self, node1, node2, properties):
        if node1 not in self.nodes:
            self.add_node(node1)
        if node1 not in self.edges:
            self.edges[node1] = set()
        self.edges[node1].add(node2)
        self.edge_properties[(node1, node2)] = properties

    """
    Automatically construct the graph connecting nodes when edge_condition_fn is satisfied
    and assigning properties via edge_properties_fn
    """
    def auto_build_edges(self, edge_condition_fn, edge_properties_fn):
        for nodeA in self.nodes:
            for nodeB in self.nodes:
                if nodeA != nodeB:
                    if edge_condition_fn(nodeA, nodeB):
                        self.add_edge(nodeA, nodeB, edge_properties_fn(nodeA, nodeB))
