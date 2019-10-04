"""
Pre-defined constraints for convenience.
Considered when generating neighbors for a given current state.
Executed on all edges from a particular state
"""

from utils import meters_to_miles


class BooleanConstraints:
    def __init__(self):
        pass

    def bool_and(self, constraints):
        def bool_and_fn(constraint_params):
            for c in constraints:
                if not c(constraint_params):
                    return False
            return True
        return bool_and_fn

    def bool_or(self, constraints):
        def bool_or_fn(constraint_params):
            for c in constraints:
                if c(constraint_params):
                    return True
            return False
        return bool_or_fn

    def bool_not(self, constraints):
        def bool_not_fn(constraint_params):
            for c in constraints:
                if c(constraint_params):
                    return False
            return True
        return bool_not_fn

    def bool_true(self):
        def bool_true_fn(constraint_params):
            return True
        return bool_true_fn

    def bool_false(self):
        def bool_false_fn(constraint_params):
            return False
        return bool_false_fn

    def bool_if_then_else(self, if_constraint, then_constraint, else_constraint):
        def bool_if_then_else_fn(constraint_params):
            if if_constraint(constraint_params):
                return then_constraint(constraint_params)
            else:
                return else_constraint(constraint_params)
        return bool_if_then_else_fn

    def bool_equals(self, curr_state_fn, next_state_fn):
        def bool_equals_fn(constraint_params):
            return curr_state_fn(constraint_params) == next_state_fn(constraint_params)
        return bool_equals_fn

    def bool_gtr_than(self, curr_state_fn, next_state_fn):
        def bool_gt_fn(constraint_params):
            return curr_state_fn(constraint_params) > next_state_fn(constraint_params)
        return bool_gt_fn

    def bool_less_than(self, curr_state_fn, next_state_fn):
        def bool_less_fn(constraint_params):
            return curr_state_fn(constraint_params) < next_state_fn(constraint_params)
        return bool_less_fn

    def bool_boolean(self, bool_fn):
        def bool_fn_(constraint_params):
            return bool_fn(constraint_params)
        return bool_fn_


class EdgeConstraints:
    def __init__(self):
        pass

    def category_seq(self, valid_cats_A, valid_cats_B):
        def cat_fn(constraint_params):
            curr_state = constraint_params.curr_state
            next_state = constraint_params.next_state

            curr_intersect = False
            next_intersect = False

            # Check for special case intersections:
            #   1) No required first category (doesn't matter where we come from)
            #   2) No required second category (doesn't matter where we go)
            if valid_cats_A is None:
                curr_intersect = True
            if valid_cats_B is None:
                next_intersect = True

            # If no exemption found, actually check for an intersection
            if not curr_intersect and curr_state is not None:
                curr_intersect = len(set(valid_cats_A).intersection(curr_state.node.entity.categories)) > 0
            if not next_intersect:
                next_intersect = len(set(valid_cats_B).intersection(next_state.node.entity.categories)) > 0

            """
            print("{} vs {} | {} ........ {} vs {} | {}".format(curr_state.node.entity.categories,
                                                                valid_cats_A,
                                                                curr_intersect,
                                                                next_state.node.entity.categories,
                                                                valid_cats_B,
                                                                next_intersect))
            """
            return curr_intersect and next_intersect
        return cat_fn


class StateConstraints:
    def __init__(self):
        self.b = BooleanConstraints()

    # Pass a dict mapping # previous states to a constraint (mapping happens on curr_state)
    # Ignore missing keys specifies whether missing keys are treated as "True"
    def prev_state_dependent(self, constraint_dict, ignore_missing_keys=True):
        def prev_state_dependent_fn(constraint_params):
            curr_state = constraint_params.curr_state
            if curr_state.num_prev_states in constraint_dict:
                constraint = constraint_dict[curr_state.num_prev_states]
            elif ignore_missing_keys:
                constraint = self.b.bool_true()
            else:
                # TODO: Create separate exception class for this
                raise Exception("Missing state dependent key {}".format(curr_state.num_prev_states))
            return constraint(constraint_params)
        return prev_state_dependent_fn

    def curr_state_category_in(self, cats):
        def curr_state_category_in_fn(constraint_params):
            curr_state = constraint_params.curr_state
            #print(curr_state.node.entity.categories)
            if len(curr_state.node.entity.categories.intersection(cats)):
                return True
            return False
        return curr_state_category_in_fn

    def no_repeat_visits(self):
        def fn(constraint_params):
            next_state = constraint_params.next_state
            prev = set([s.node.entity.id for s in next_state.prev_state_list()])
            return next_state.node.entity.id not in prev
        return fn

class UberConstraints:
    def __init__(self):
        self._b = BooleanConstraints()
        self._s = StateConstraints()
        self._e = EdgeConstraints()

    def follows_cat_sequence(self, category_sequence):
        const_dict = {}
        for i in range(len(category_sequence) - 1):
            const_dict[i] = self._e.category_seq(category_sequence[i], category_sequence[i + 1])
        const_dict[len(category_sequence) - 1] = self._b.bool_false()
        return self._s.prev_state_dependent(const_dict)


class StateExtractors:
    def __init__(self):
        pass

    def get_categories(self, use_next=False):
        def getcats_fn(constraint_params):
            state = constraint_params.curr_state if not use_next else constraint_params.next_state
            if state is not None:
                return state.node.entity.categories
            else:
                return set()
        return getcats_fn

    def get_entity_type(self, use_next=False):
        def get_entity_type_fn(constraint_params):
            state = constraint_params.curr_state if not use_next else constraint_params.next_state
            return state.node.entity.entity

    def get_attr(self, attr_name, use_next=False):
        def getattr_fn(constraint_params):
            state = constraint_params.curr_state if not use_next else constraint_params.next_state
            return getattr(state, attr_name)
        return getattr_fn

    def get_entity_attr(self, attr_name, use_next=False):
        def get_node_attr_fn(constraint_params):
            def getattr_fn(constraint_params):
                state = constraint_params.curr_state if not use_next else constraint_params.next_state
                return getattr(state, attr_name)

    def const(self, value):
        def const_fn(constraint_params):
            return value
        return const_fn

class EdgeExtractors:
    def __init__(self):
        pass

    def get_distance(self, use_miles=False):
        def fn(constraint_params):
            graph, curr_state, next_state = constraint_params.graph, constraint_params.curr_state, constraint_params.next_state
            dist = graph.get_edge_properties(curr_state.node, next_state.node)['dist']
            return dist if not use_miles else meters_to_miles(dist)
        return fn
