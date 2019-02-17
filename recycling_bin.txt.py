# Uses graphql endpoint and also returns hours. Doesn't return search region.
# Fusion endpoint doesn't return hours.

# GRAPHQL CANT RETURN LAT/LONG! I need this info. Better to use GraphQL on the business details side instead.
# Will create a custom command just for pulling hours in bulk.
def graphql_business_search(self,
                            term=None,
                            location=None,
                            latitude=None,
                            longitude=None,
                            radius=None,
                            categories=None,
                            locale=None,
                            limit=None,
                            offset=None,
                            sort_by=None,
                            price=None,
                            open_now=None,
                            open_at=None,
                            attributes=None,
                            add_parent_categories=False):
    # Set up params dict
    params = dict(locals())
    del params['add_parent_categories']
    del params['self']
    keys = list(params.keys())
    for k in keys:
        if params[k] is None:
            del params[k]

    # Reformat to graphql expected format and generate query
    formatted_params = []
    for k, v in params.items():
        if k not in ["latitude", "longitude", "radius", "limit", "offset", "open_at"]:
            param = '{0}: "{1}"'.format(k, v)
        else:
            param = '{0}: {1}'.format(k, v)
        formatted_params.append(param)
    formatted_params = ",".join(formatted_params)
    query = """
     {{
         search({0}) {{
         total
         business {{
             rating
             price
             phone
             id
             alias
             is_closed
             categories {{
                 alias
                 title
             }}
             review_count
             name
             url
             distance
             transactions
             hours
           location {{
             address1
             city
             state
             country
           }}
         }}
       }}
     }}
     """.format(formatted_params)

    # Submit graphql query
    response = self._graphql_request(query)
    print(query)
    print(response)
    businesses = response['business']
    business_objs = self._process_business_search_businesses(businesses, add_parent_categories)
    result = {
        "total": response['total'],
        "businesses": business_objs
    }
    return result