from graph import Graph
from utils import lat_long_dist, day_of_week
import datetime

class EntityTypes:
    BUSINESS = 0
    EVENT = 1



class PlanState:
    def __init__(self, node, start_dt, end_dt, prev_state, num_prev_states):
        self.node = node
        self.start_dt = start_dt
        self.end_dt = end_dt
        self.num_prev_states = num_prev_states
        self.prev_state = prev_state
        self._prev_state_list = None

    def prev_state_list(self):
        out = []
        s = self.prev_state
        while s is not None:
            out.append(s)
            s = s.prev_state
        self._prev_state_list = out[::-1]
        return self._prev_state_list

class ConstraintParams:
    def __init__(self, graph, curr_state, next_state, global_memory):
        self.graph = graph
        self.curr_state = curr_state
        self.next_state = next_state
        self.global_memory = global_memory if global_memory is not None else {}


class Entity:
    def __init__(self, business=None, event=None):
        self.open_times = {}
        self.close_times = {}
        self.start_dt = None
        self.end_dt = None
        self.spans_days = False # For events across multiple days where time will be unclear
        self.entity = business if business is not None else event

        self.type = EntityTypes.BUSINESS if business is not None else EntityTypes.EVENT
        if business is not None:
            pass
        elif event is not None:
            self.start_dt = event.start_time
            self.end_dt = event.end_time
            if self.end_dt - self.start_dt > datetime.timedelta(hours=24):
                self.spans_days = True

    def hours_open(self, dt):
        pass

    def open_at(self, dt):
        is_open = False
        # If it's an event, check that we're between the start and end times
        if self.type == EntityTypes.EVENT:
            if self.start_dt <= dt <= self.end_dt:
                is_open = True
        # Otherwise check that it's between business hours
        else:
            weekday = day_of_week(dt)
            tm = dt.time()
            # Check that we're in at least one of the timespans
            for hours in self.entity.hours[weekday]:
                # Between start and end hours and it isn't overnight OR
                # between an overnight start + end date
                if (hours['start'] <= tm <= hours['end']
                        and not hours['is_overnight']) \
                        or ((hours['start'] <= tm or tm <= hours['end'])
                            and hours['is_overnight']):
                    is_open = True
                    break
        return is_open

    def get_address(self):
        if self.type == EntityTypes.BUSINESS:
            return " ".join(self.entity.location['display_address'])
        else:
            return ""

# Todo: Maybe abstract these node/edge conditions out into a function for more flexibility
def build_entity_graph(entities,
                         category_sequence=None,
                         min_distance=0,
                         max_distance=10e10,
                         min_rating=None,
                         max_rating=None,
                         min_dollar_signs=None,
                         max_dollar_signs=None,
                         min_review_count=None,
                         max_review_count=None,
                         ignore_missing_info=True):
    g = Graph()
    for b in entities:
        if b.type == EntityTypes.BUSINESS:
            bb = b.entity
            # Ignore things with no hours
            if bb.hours is None:
                continue
            # Ignore rating if filter applied but it's missing
            if min_rating is not None and max_rating is not None and bb.rating is None and ignore_missing_info:
                continue
            # Ignore price if filter applied but it's missing
            if(min_dollar_signs is not None or max_dollar_signs is not None) and bb.price is None and ignore_missing_info:
                continue
            # Ignore review count if filter applied but it's missing
            if min_review_count is not None and bb.review_count is None and ignore_missing_info:
                continue

            # Check rating
            if (min_rating is not None and bb.rating < min_rating) or (max_rating is not None and bb.rating > max_rating):
                continue
            # Check price
            if (min_dollar_signs is not None and len(bb.price) < min_dollar_signs) or (max_dollar_signs is not None and len(bb.price) > max_dollar_signs):
                continue
            # Check review count
            if min_review_count is not None and max_review_count is not None and (bb.review_count < min_review_count or bb.review_count > max_review_count):
                continue
        else:
            # Event conditions go here (if I decide to add those... may be better to roll them into constraints
            # that are applied now at graph creation time so all constraints defined in same way.
            pass

        # Add if all conditions passed
        g.add_node(b)

    valid_seqs = set()
    # Generate all possible sequences of categories for faster lookup
    if category_sequence is not None:
        for i in range(len(category_sequence) - 1):
            for j in range(len(category_sequence[i])):
                for k in range(len(category_sequence[i + 1])):
                    valid_seqs.add((category_sequence[i][j], category_sequence[i + 1][k]))

    def is_valid_edge(bizA, bizB):
        bizA = bizA.entity
        bizB = bizB.entity
        # Distance check
        dist = lat_long_dist(bizA.latitude, bizA.longitude, bizB.latitude, bizB.longitude)
        if dist > max_distance or dist < min_distance:
            return False

        # Category check
        categories_valid = False
        for catA in bizA.categories:
            for catB in bizB.categories:
                        if (catA, catB) in valid_seqs or category_sequence is None:
                            return True
        return categories_valid

    def edge_properties(bizA, bizB):
        bizA, bizB = bizA.entity, bizB.entity
        return {"dist": lat_long_dist(bizA.latitude, bizA.longitude, bizB.latitude, bizB.longitude)}

    g.auto_build_edges(is_valid_edge, edge_properties)

    return g


def default_time_spent_fn(entity):
    return [datetime.timedelta(hours=1.5)]


def default_distance_time_fn(dist):
    avg_walk_speed = 1.4 # m/s
    return datetime.timedelta(seconds=dist/avg_walk_speed)

def build_neighbor_state_fn(constraint, time_spent_fn=default_time_spent_fn, distance_time_fn=default_distance_time_fn):
    """
    Returns a function that returns all the valid neighbors of given state.
    :param constraint: The constraint that determines whether something is a valid neighbor or not.
    :param time_spent_fn: A function which returns how much time could be spent somewhere given an Entity as a list
                          of timedeltas.
    :param distance_time_fn: A function that converts distance (meters) to travel time (timedelta)
    :return:
    """
    def neighbor_state_fn(constraint_params):
        graph, curr_state, global_memory = constraint_params.graph, constraint_params.curr_state, constraint_params.global_memory
        neighbors = []
        num_prev_states = curr_state.num_prev_states + 1
        potential_neighbors = graph.get_edges(curr_state.node)
        #print("\t\tFound {} potential neighbors".format(len(potential_neighbors)))
        for node in potential_neighbors:
            properties = graph.get_edge_properties(curr_state.node, node)
            dist = properties['dist']

            # Only explore things that are open at desired start time
            next_start_dt = curr_state.end_dt + distance_time_fn(dist)
            if node.open_at(next_start_dt):
                # Try all possible amounts of time to stay at next spot
                possible_times_spent_next = time_spent_fn(node)
                for time_spent_next in possible_times_spent_next:
                    next_end_dt = next_start_dt + time_spent_next
                    # Make sure it's open
                    if node.open_at(next_end_dt):
                        next_state = PlanState(node, next_start_dt, next_end_dt, curr_state, num_prev_states)
                        constraint_params = ConstraintParams(graph, curr_state, next_state, global_memory)
                        if constraint(constraint_params):
                            neighbors.append(next_state)

        return neighbors
    return neighbor_state_fn


def build_initial_states(graph, possible_start_dts, constraint, time_spent_fn=default_time_spent_fn):
    """
    Returns a list of valid starting states according to the constraint.
    :param graph: The graph whose states will be returned.
    :param possible_start_dts: The possible start times.
    :param constraint: The constraint on initial states (passed as the "current state" to constraints)
    :param time_spent_fn: A function that returns a list of possible times spent given an Entity.
    :return:
    """
    initial_states = []
    for node in graph.nodes:
        possible_times_spent = time_spent_fn(node)
        for start_dt in possible_start_dts:
            if node.open_at(start_dt):
                for time_spent in possible_times_spent:
                    end_dt = start_dt + time_spent
                    if node.open_at(end_dt):
                        initial_state = PlanState(node, start_dt, end_dt, None, 0)
                        constraint_params = ConstraintParams(graph, initial_state, None, None)
                        if constraint(constraint_params):
                            initial_states.append(initial_state)
    return initial_states

def build_success_state_fn(constraint):
    """
    A function that returns True if the current state is a success state, and False otherwise.
    Passes the current candidate success state as the "current state". Does not include any
    "next state".
    :param constraint: The constraint indicating whether this is a success state.
    :return:
    """
    def success_state_fn(constraint_params):
        return constraint(constraint_params)
    return success_state_fn