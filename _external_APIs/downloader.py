# creating test db
import requests
import json
from pprint import pprint
from random import randint
import datetime
from geopy.geocoders import Nominatim

import logging

logging.basicConfig(level=logging.DEBUG)


# basic functions
def save_json(file_name, data):
    with open(file_name, "w") as fp:
        json.dump(data, fp)
        logging.debug("Saved json to file: {}.".format(file_name))
    return None

def open_json(file_name):
    with open(file_name) as fp:
        data = json.load(fp)
    return data

# API classes
class Eatstreet_API():
    def __init__(self):
        self.key = "0a72c7182d649950"
        self.header = {"User-agent": "curl/7.43.0", "Accept": "application/json", "X-Access-Token": self.key}

        # URLs
        self.restaurant_url = "https://api.eatstreet.com/publicapi/v1/restaurant/search"

    def menu_url(self, restaurant_id):
        return "https://api.eatstreet.com/publicapi/v1/restaurant/{}/menu".format(restaurant_id)

        # params



class Zomato_API():
    def __init__(self):
        self.key = "4c46fa3f7fdeee84299bb34ef33f0ba7"
        self.header = {"User-agent": "curl/7.43.0", "Accept": "application/json", "user_key": self.key}

        # URLs
        self.search_url = "https://developers.zomato.com/api/v2.1/search"
        self.restaurant_url = "https://developers.zomato.com/api/v2.1/restaurant"
        self.location_url = "https://developers.zomato.com/api/v2.1/locations"
        self.reviews_url = "https://developers.zomato.com/api/v2.1/reviews"

    # params
    def location_params(self, city, latitude, longitude):
        location_params = {
            "query": city,
            "lat": latitude,
            "lon": longitude
        }
        return location_params


    # fetching methods
    def fetch_cities(self, cities):
        for city in cities:
            city_location = geolocate(city)
            city_location_lat = city_location.latitude
            city_location_lon = city_location.longitude
            print(city, city_location.latitude, city_location.longitude)

            response = requests.get(self.location_url, headers=self.header,
                                    params=self.location_params(city=city, latitude=city_location_lat,
                                                                      longitude=city_location_lon))
            zomato_location_response = response.json()["location_suggestions"][0]
            zomato_city_name = zomato_location_response["city_name"]
            zomato_city_id = zomato_location_response["city_id"]

            output_file = {}
            output_file["eatstreet_city_name"] = city
            output_file["latitude"] = city_location_lat
            output_file["longitude"] = city_location_lon
            output_file["zomato_city_name"] = zomato_city_name
            output_file["zomato_city_id"] = zomato_city_id

            pprint(output_file)

            save_json(file_name="data/cities/city_{}.json".format(city.replace(",", "_").replace(" ", "")), data=output_file)



def geolocate(city):
    try:
        geolocator = Nominatim(user_agent="api_downloader")
        city_location = geolocator.geocode(city)
    except Exception as err:
        logging.warning("Could not geolocate due to error:\n {}\nTrying again...".format(err))
        city_location = geolocate(city)
    return city_location



#  cities file
with open("data/_cities.txt") as fp:
    cities_data = fp.read()
cities = cities_data.split("\n")
cities = [e.lstrip() for e in cities]



if __name__ == "__main__":
    e = Eatstreet_API()
    z = Zomato_API()

    z.fetch_cities(cities)