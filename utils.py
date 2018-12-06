from math import radians, cos, sin, asin, sqrt


def lat_long_dist(lat1, lon1, lat2, lon2):
    """
    Calculate the great circle distance between two points
    on the earth (specified in decimal degrees)
    """
    # convert decimal degrees to radians
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])

    # haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * asin(sqrt(a))
    r = 6371  # Radius of earth in kilometers. Use 3956 for miles
    return c * r * 1000 # Convert to meters to match Yelp

def meters_to_miles(meters):
    return 0.00062137 * meters

def miles_to_meters(miles):
    return 1.0/0.00062137 * miles

def dedupe_list(items, item_key_fn):
    seen_keys = set()
    new_items = []
    for itm in items:
        key = item_key_fn(itm)
        if key not in seen_keys:
            new_items.append(itm)
        seen_keys.add(key)
    return new_items

def day_of_week(dt):
    return dt.weekday()