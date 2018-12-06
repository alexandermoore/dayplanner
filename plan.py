import copy

def default_neighbor_state_fn(graph, curr_state, global_memory):
    if curr_state is None:
        neighbors = [n for n in graph.nodes]
    else:
        neighbors = graph.get_edges(curr_state)
    return neighbors

def default_process_state_fn(graph, curr_state, global_memory):
    pass

def default_is_success_state_fn(graph, curr_state, global_memory):
    return True

"""
Outputs a list of successful terminal states.
"""
def generate_plans(graph, initial_states, neighbor_state_fn, success_state_fn, process_state_fn):
    global_memory = {}
    queue = copy.copy(initial_states)
    success_states = set()
    while len(queue) > 0:
        state = queue.pop()
        #print("Popping {0}".format(state.node.entity.name))
        # Process state (make any edits to global memory if needed)
        # process_state_fn(graph, state, global_memory)

        # Check if successful final state. If so, add it to successful plan states.
        if success_state_fn(graph, state, global_memory):
            success_states.add(state)

        # Add state neighbors
        neighbors = neighbor_state_fn(graph, state, global_memory)
        #print("\tFound {} neighbors".format(len(neighbors)))
        queue.extend(neighbors)

    return success_states
