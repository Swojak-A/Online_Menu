# creating test db
import requests
import os
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
        logging.debug("Opened json from file: {}.".format(file_name))
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
    def restaurant_params(self, latitude, longitude):
        restaurant_params = {
            "latitude": latitude,
            "longitude": longitude,
            "method": "both"
        }
        return restaurant_params

    def menu_params(self):
        menu_params = {
            "includeCustomizations": "false"
        }
        return menu_params

        # assert json
    def assert_json(self, input):
        try:
            assert input.endswith(".json") == True
        except AssertionError:
            logging.error("Parameter: {} is not a json file".format(input))
            raise

        # fetching methods
    def fetch_restaurants(self, city_file):
        self.assert_json(input=city_file)

        city_data = open_json(city_file)

        response = requests.get(self.restaurant_url, headers=self.header,
                                params=self.restaurant_params(latitude=city_data["latitude"], longitude=city_data["longitude"]))
        eatstreet_restaurant_response = response.json()
        data = eatstreet_restaurant_response

        # pprint(data)

        for restaurant in data["restaurants"]:
            restaurant["zomato_city_id"] = city_data["zomato_city_id"]

            name = restaurant["name"].encode("ascii", errors="ignore").decode()
            city = restaurant["city"]
            state = restaurant["state"]

            save_json(file_name="data/restaurants/restaurant_{}_{}_{}.json".format(city, state, name), data=restaurant)

    def fetch_all_restaurants(self, path="data/cities/"):
        for file in os.listdir(path):
            city_file = path + file

            logging.info("Preparing to fetch data from: {}".format(city_file))

            self.fetch_restaurants(city_file=city_file)

    def fetch_menu(self, restaurant_file):
        self.assert_json(input=restaurant_file)

        print(restaurant_file)

        restaurant_data = open_json(restaurant_file)
        eatstreet_id = restaurant_data["apiKey"]

        response = requests.get(self.menu_url(eatstreet_id), headers=self.header,
                                params=self.menu_params())
        eatstreet_menu_response = response.json()
        data = eatstreet_menu_response

        restaurant_data["menu"] = data

        save_json(file_name=restaurant_file, data=restaurant_data)

    def fetch_all_menus(self, path="data/restaurants/"):
        for file in os.listdir(path):
            restaurant_file = path + file

            logging.info("Preparing to fetch data from: {}".format(restaurant_file))

            self.fetch_menu(restaurant_file=restaurant_file)

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

    def search_params(self, city_id, query_keyword):
        search_params = {
            "entity_id": city_id,
            "entity_type": "city",
            "q": query_keyword
        }
        return search_params


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

    def fetch_zomato_rest_data(self, restaurant_file):
        restaurant_data = open_json(restaurant_file)

        print("searching for matches for: {}".format(restaurant_data["name"]))

        try:
            response = requests.get(self.search_url, headers=self.header,
                                    params=self.search_params(city_id=restaurant_data["zomato_city_id"],
                                                              query_keyword=" ".join(restaurant_data["name"].split()[:2])
                                                              ))
            zomato_search_response = response.json()["restaurants"][0]["restaurant"]
            zomato_id = zomato_search_response["id"]
            zomato_name = zomato_search_response["name"]

            accept_input = input("eatstreet: {}, \nzomato: {}\nis it okay? ".format(restaurant_data["name"], zomato_name))

            if accept_input == "y" or accept_input == "z":
                restaurant_data["zomato_id"] = zomato_id
                restaurant_data["zomato_name"] = zomato_name

                save_json(file_name=restaurant_file, data=restaurant_data)
        except Exception as err:
            logging.warning("error ({}) occured when fetching data from file: {}".format(err, restaurant_file))
            with open("data/_reviews_errorlist.txt", "a") as fp:
                fp.write(restaurant_file + "\n")



    def fetch_all_zomato_rest_data(self, path="data/restaurants/"):
        for file in os.listdir(path):
            restaurant_file = path + file

            logging.info("Preparing to fetch data from: {}".format(restaurant_file))

            self.fetch_zomato_rest_data(restaurant_file=restaurant_file)

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

    z.fetch_all_zomato_rest_data()