import json
import requests
import datetime
import time
import dateutil.parser
import pytz

# YELP TIMEZONE BUG:
# All events are assumed to originally have been in Pacific time.
# To query Yelp, change the timezone of your query to Pacific (don't change time, just timezone)
# and then convert that to UTC.
# When getting results from Yelp, convert from UTC to Pacific time, then set the Timezone to the local time (without changing time)
def str_to_datetime(date_string, timezone_name):
    dt = dateutil.parser.parse(date_string)
    return pytz.timezone(timezone_name).localize(dt)

def str_to_unix(date_string, timezone_name):
    # dt = str_to_datetime(date_string, timezone_name)
    dt = str_to_datetime(date_string, 'America/Los_Angeles')
    return int(dt.timestamp())

def to_local_time(dt, timezone_name):
    # Convert from UTC to PDT
    dt = dt.astimezone(pytz.timezone("America/Los_Angeles"))
    # Set timezone to actual timezone instead of PDT and remove timezone info.
    return pytz.timezone(timezone_name).localize(dt.replace(tzinfo=None)).replace(tzinfo=None)
    # return dt.astimezone(pytz.timezone(timezone_name))

class BusinessSearchResult():
    def __init__(self,
                 rating=None,
                 price=None,
                 phone=None,
                 id=None,
                 alias=None,
                 is_closed=None,
                 categories=None,
                 review_count=None,
                 name=None,
                 url=None,
                 latitude=None,
                 longitude=None,
                 image_url=None,
                 location=None,
                 distance=None,
                 transactions=None,
                 hours=None):
        self. rating = rating
        self.price = price
        self.phone = phone
        self.id = id
        self.alias = alias
        self. is_closed = is_closed
        self.categories = categories
        self.review_count = review_count
        self.name = name
        self.url = url
        self.latitude = latitude
        self.longitude = longitude
        self.image_url = image_url
        self.location = location
        self.distance = distance
        self.transactions = transactions
        self.hours = hours # Will be none unless using graphql

class BusinessDetails():
    def __init__(self,
                 id=None,
                 alias=None,
                 name=None,
                 image_url=None,
                 is_claimed=None,
                 is_closed=None,
                 url=None,
                 price=None,
                 rating=None,
                 review_count=None,
                 phone=None,
                 photos=None,
                 hours=None,
                 categories=None,
                 latitude=None,
                 longitude=None,
                 location=None,
                 transactions=None
                 ):
        self.id = id
        self.alias = alias
        self.name = name
        self.image_url = image_url
        self.is_claimed = is_claimed
        self.is_closed = is_closed
        self.url = url
        self.price = price
        self.rating = rating
        self.review_count = review_count
        self.phone = phone
        self.photos = photos
        self.hours = hours
        self.categories = categories
        self.latitude = latitude
        self.longitude = longitude
        self.location = location
        self.transactions = transactions

class EventSearchResult():
    def __init__(self,
                 attending_count=None,
                 categories=None,
                 cost=None,
                 cost_max=None,
                 description=None,
                 url=None,
                 id=None,
                 image_url=None,
                 interested_count=None,
                 is_canceled=None,
                 is_free=None,
                 is_official=None,
                 latitude=None,
                 longitude=None,
                 name=None,
                 tickets_url=None,
                 start_time=None,
                 end_time=None,
                 location=None,
                 cross_streets=None,
                 business_alias=None):
        self.attending_count = attending_count
        self.categories = categories
        self.cost = cost
        self.cost_max = cost_max
        self.description = description
        self.url = url
        self.id = id
        self.image_url = image_url
        self.interested_count = interested_count
        self.is_canceled = is_canceled
        self.is_free = is_free
        self.is_official = is_official
        self.latitude = latitude
        self.longitude = longitude
        self.name = name
        self.tickets_url = tickets_url
        self.start_time = start_time
        self.end_time = end_time
        self.location = location
        self.cross_streets = cross_streets
        self.business_alias = business_alias


class YelpAPI():
    def __init__(self, apikey, categories_file):
        self.API_HOST = r"https://api.yelp.com/v3/"
        self.API_KEY = apikey
        self.BIZ_CATEGORIES = self._read_categories(categories_file)
        self.EVENT_CATEGORIES = {
            "music": {"title": "Music", "parents": []},
            "visual-arts": {"title": "Visual Arts", "parents": []},
            "performing-arts": {"title": "Performing Arts", "parents": []},
            "film": {"title": "Film", "parents": []},
            "lectures-books": {"title": "Lectures & Books", "parents": []},
            "fashion": {"title": "Fashion", "parents": []},
            "food-and-drink": {"title": "Food & Drink", "parents": []},
            "festivals-fairs": {"title": "Festivals & Fairs", "parents": []},
            "charities": {"title": "Charities", "parents": []},
            "sports-active-life": {"title": "Sports & Active Life", "parents": []},
            "nightlife": {"title": "Nightlife", "parents": []},
            "kids-family": {"title": "Kids & Family", "parents": []},
            "other": {"title": "Other", "parents": []}
        }

    def _read_categories(self, categories_file):
        with open(categories_file, "r") as f:
            cats = json.load(f)
        categories = {}
        for elem in cats:
            categories[elem['alias']] = {"title": elem['title'], "parents": elem['parents']}
        return categories

    def _request(self, endpoint, url_params):
        headers = {
            "Authorization": "Bearer {0}".format(self.API_KEY)
        }
        url = "{0}{1}".format(self.API_HOST, endpoint)
        response = requests.request('GET', url, headers=headers, params=url_params)
        return response.json()

    def _graphql_request(self, query):
        headers = {
            "Authorization": "Bearer {0}".format(self.API_KEY),
            "Content-Type": "application/graphql",
            "Accept-Language": "en_US"
        }
        url = "{0}graphql".format(self.API_HOST)
        response = requests.request('POST', url, headers=headers, data=query)
        resp = response.json()
        if 'data' in resp:
            return resp['data']
        else:
            return resp

    def flatten_raw_categories(self, categories):
        return set([cat['alias'] for cat in categories]) if categories is not None else None

    def add_parent_categories(self, categories):
        if categories is None:
            return None
        enhanced_categories = set()
        queue = []
        queue.extend(categories)
        while(len(queue) > 0):
            cat = queue.pop()
            if cat not in enhanced_categories:
                if cat in self.BIZ_CATEGORIES:
                    parents = self.BIZ_CATEGORIES[cat]['parents']
                    queue.extend(parents)
                enhanced_categories.add(cat)
        return enhanced_categories

    # https://www.yelp.com/developers/documentation/v3/business_search
    # Fusion endpoint. Doesn't return hours.
    def business_search(self,
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
        params = dict(locals())
        del params['add_parent_categories']
        del params['self']
        keys = list(params.keys())
        for k in keys:
            if params[k] is None:
                del params[k]
        response = self._request("businesses/search", params)
        businesses = response['businesses']
        business_objs = self._process_business_search_businesses(businesses, add_parent_categories)
        result = {
            "total": response['total'],
            "businesses": business_objs,
            "latitude": response['region']['center']['latitude'],
            "longitude": response['region']['center']['longitude']
        }
        return result

    def _process_business_search_businesses(self, businesses, add_parent_categories):
        business_objs = []
        for biz in businesses:
            cats = self.flatten_raw_categories(biz.get('categories'))
            if add_parent_categories:
                cats = self.add_parent_categories(cats)
            business_objs.append(
                BusinessSearchResult(
                    rating=biz.get('rating'),
                    price=biz.get('price'),
                    phone=biz.get('phone'),
                    id=biz['id'],
                    alias=biz['alias'],
                    is_closed=biz.get('is_closed'),
                    categories=cats,
                    review_count=biz.get('review_count'),
                    name=biz.get('name'),
                    url=biz.get('url'),
                    latitude=biz['coordinates']['latitude'],
                    longitude=biz['coordinates']['longitude'],
                    image_url=biz.get('image_url'),
                    location=biz.get('location'),
                    distance=biz.get('distance'),
                    transactions=biz.get('transactions'),
                    hours=biz.get('hours')
                )
            )
        return business_objs

    # https://www.yelp.com/developers/documentation/v3/business
    def business_details(self, id, add_parent_categories=False):
        result = self._request("businesses/{0}".format(id), {})
        return self._process_business_detail(result, add_parent_categories)

    def graphql_bulk_business_hours(self, ids):
        business_query_str = """
          b{0}: business(id: "{1}") {{
            name
            id
            hours {{
              is_open_now
              open {{
                day
                is_overnight
                start
                end
              }}
            }}
          }}
        """
        formatted_businesses = []
        for idx, biz_id in enumerate(ids):
            formatted_businesses.append(business_query_str.format(idx, biz_id))
        query = "{{ {0} }}".format("\n".join(formatted_businesses))
        results = self._graphql_request(query)

        all_hours = []
        for i in range(len(ids)):
            result = results["b{0}".format(i)]
            hours_raw = result.get('hours')
            hours = None
            if hours_raw is not None:
                hours = self._reformat_business_hours(hours_raw)
            all_hours.append(hours)
        return all_hours

    def add_hours_to_search_results(self, results):
        ids = [r.id for r in results]
        hours = self.graphql_bulk_business_hours(ids)
        for i in range(len(results)):
            results[i].hours = hours[i]

    def _reformat_business_hours(self, hours_raw):
        # Change format of hours to a list. One element for each day,
        # and each element is a list of the various hours for that day.
        # "REGULAR" is omitted since it's always that.
        hours = None
        if hours_raw is not None:
            hours = [[] for _ in range(7)]
            for hrs in hours_raw:
                for elem in hrs['open']:
                    stime = time.strptime(elem['start'], "%H%M")
                    etime = time.strptime(elem['end'], "%H%M")
                    hours[elem['day']].append({
                        "is_overnight": elem['is_overnight'],
                        "start": datetime.time(stime.tm_hour, stime.tm_min),
                        "end": datetime.time(etime.tm_hour, etime.tm_min)
                    })
        return hours

    def _process_business_detail(self, result, add_parent_categories):
        cats = self.flatten_raw_categories(result.get('categories'))
        if add_parent_categories:
            cats = self.add_parent_categories(cats)

        hours_raw = result.get('hours')
        hours = None
        if hours_raw is not None:
            hours = self._reformat_business_hours(hours_raw)

        return BusinessDetails(
            id=result['id'],
            alias=result['alias'],
            name=result.get('name'),
            image_url=result.get('image_url'),
            is_claimed=result.get('is_claimed'),
            is_closed=result.get('is_closed'),
            url=result.get('url'),
            price=result.get('price'),
            phone=result.get('phone'),
            photos=result.get('photos'),
            hours=hours,
            categories=cats,
            latitude=result['coordinates']['latitude'],
            longitude=result['coordinates']['longitude'],
            transactions=result.get('transactions')
        )

    def event_search(self,
                     offset=None,
                     limit=None,
                     sort_by=None,
                     sort_on=None,
                     start_date=None, # Datetime object
                     end_date=None, # Datetime object
                     categories=None,
                     is_free=None,
                     location=None,
                     latitude=None,
                     longitude=None,
                     radius=None,
                     excluded_events=None,
                     timezone=None,
                     duration_if_no_end=datetime.timedelta(seconds=3600 * 2)): # Default duration 2hrs if no end time
        if timezone is None:
            raise Exception("Must specify timezone")
        start_date = str_to_unix(start_date, timezone)
        end_date = str_to_unix(end_date, timezone)
        params = dict(locals())
        #del params['add_parent_categories']
        keys = list(params.keys())
        for k in keys:
            if params[k] is None:
                del params[k]
        response = self._request("events", params)
        events = response["events"]
        event_objs = []
        print([x['id'] for x in events])
        for event in events:
            if "category" in event:
                cats = set(["event", event.get('category')]) # Events only have 1 category. Manually adding "event" as parent category.
            else:
                cats = set(["event"])
            print(event['time_start'], event['time_end'])
            stime = to_local_time(dateutil.parser.parse(event['time_start']), timezone)
            if event['time_end'] is not None:
                etime = to_local_time(dateutil.parser.parse(event['time_end']), timezone)
            elif duration_if_no_end is not None:
                etime = stime + duration_if_no_end
            else:
                etime = None
            event_objs.append(
                EventSearchResult(
                    attending_count=event.get('attending_count'),
                    categories=cats,
                    cost=event.get('cost'),
                    cost_max=event.get('cost_max'),
                    url=event.get('event_site_url'),
                    id=event['id'],
                    image_url=event.get('image_url'),
                    interested_count=event.get('interested_count'),
                    is_canceled=event.get('is_canceled'),
                    is_free=event.get('is_free'),
                    is_official=event.get('is_official'),
                    latitude=event.get('latitude'),
                    longitude=event.get('longitude'),
                    name=event.get('name'),
                    tickets_url=event.get('tickets_url'),
                    start_time=stime,
                    end_time=etime,

                )
            )
        print(events[0]['time_start'])
        return event_objs


