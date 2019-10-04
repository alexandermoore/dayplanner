from utils import dedupe_list
from algo import Entity
import urllib
import math

def fetch_businesses_by_categories(api,
                                   location,
                                   categories,
                                   num_businesses_per_category=20,
                                   request_separately=True,
                                   add_hours=True,
                                   as_entities=True):
    businesses = []
    if request_separately:
        for cat in categories:
            results = api.business_search(location=location,
                                          categories=[cat],
                                          add_parent_categories=True,
                                          max_num_businesses=num_businesses_per_category)
            businesses.extend(results['businesses'])
    else:
        results = api.business_search(location=location,
                                      categories=categories,
                                      add_parent_categories=True,
                                      max_num_businesses=num_businesses_per_category * len(categories))
        businesses.extend(results['businesses'])
    businesses = dedupe_list(businesses, lambda x: x.id)

    if add_hours:
        # Add hours in groups of 20 to reduce load
        for i in range(0, int(math.ceil(len(businesses)/20))):
            api.add_hours_to_search_results(businesses[i*20:(i+1)*20])

    if as_entities:
        businesses = [Entity(business=b) for b in businesses]
    return businesses

def build_maps_link(places, travelmode):
    origin = places[0]
    dest = places[-1]
    waypoints = '|'.join(places[1:-1])
    #print(waypoints)
    waypoints = urllib.parse.quote_plus(waypoints)
    if waypoints != "":
        waypoints = "&waypoints=" + waypoints
    url = "https://www.google.com/maps/dir/?api=1&origin={}&destination={}&travelmode={}{}".format(
        origin,
        dest,
        travelmode,
        waypoints
    )
    return url

def plan_total_distance(graph, final_state):
    states = final_state.prev_state_list() + [final_state]
    dist = 0
    for i in range(len(states) - 1):
        dist += graph.get_edge_properties(states[i].node, states[i + 1].node)['dist']
    return dist

def sort_plans_by(states, sort_fn):
    return sorted(states, key=sort_fn)

#https://www.google.com/maps/dir/?api=1&origin=Paris,France&destination=Cherbourg,France&travelmode=driving&waypoints=Palace+of+Versailles