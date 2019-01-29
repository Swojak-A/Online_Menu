from geopy.geocoders import Nominatim
import logging
import pprint

class Geolocator():
    def __init__(self):
        self.geolocator = Nominatim(user_agent="site_geolocator")

    def geolocate(self, input):
        try:
            # geolocator = Nominatim(user_agent="api_downloader")
            location = self.geolocator.geocode(input)
        except Exception as err:
            logging.warning("Could not geolocate due to error:\n {}\nTrying again...".format(err))
            location = self.geolocate(input)
        return location

    def reverse_geolocate(self, location):
        print()
        try:
            location = self.geolocator.reverse((location.latitude, location.longitude))

            pprint(location.raw)

        except Exception as err:
            logging.warning("Could not geolocate due to error:\n {}\nTrying again...".format(err))
            raise err
            location = self.reverse_geolocate(location)
        return location


if __name__ == "__main__":
    g = Geolocator()
    input = "1520 west indian school road, phoenix"
    location = g.geolocate(input)
    raw_location = g.reverse_geolocate(location)
    pprint(raw_location.raw)