import json
import requests

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
                 transactions=None):
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

class Business():
    pass


class YelpAPI():
    def __init__(self, apikey, categories_file):
        self.API_HOST = r"https://api.yelp.com/v3/"
        self.API_KEY = apikey
        self.CATEGORIES = self._read_categories(categories_file)

    def _read_categories(self, categories_file):
        with open(categories_file, "r") as f:
            cats = json.load(f)
        categories = {}
        for elem in cats:
            categories[elem['alias']] = elem['title']
        return categories

    def _request(self, endpoint, url_params):
        headers = {
            "Authorization": "Bearer {0}".format(self.API_KEY)
        }
        url = "{0}{1}".format(self.API_HOST, endpoint)
        response = requests.request('GET', url, headers=headers, params=url_params)
        return response.json()

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
                        attributes=None
                        ):
        params = dict(locals())
        keys = list(params.keys())
        for k in keys:
            if params[k] is None:
                del params[k]
        response = self._request("businesses/search", params)

        businesses = response['businesses']
        business_objs = []
        for biz in businesses:
            cats = [cat['alias'] for cat in biz['categories']]
            business_objs.append(
                BusinessSearchResult(
                    rating=biz.get('rating'),
                    price=biz.get('price'),
                    phone=biz.get('phone'),
                    id=biz['id'],
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
                    transactions=biz.get('transactions')
                )
            )

        result = {
            "total": response['total'],
            "businesses": business_objs,
            "latitude": response['region']['center']['latitude'],
            "longitude": response['region']['center']['longitude']
        }

        return result


