import requests
from route import Route

class TaxiRouteInfoApi:
    api_url = "https://taxi-routeinfo.taxi.yandex.net/taxi_info"
    headers = {
        "Accept": "application/json"
    }
    def __init__(self, CLID : str, APIKEY : str):
        self.params = {
            "rll": "",
            "clid": CLID,
            "apikey": APIKEY,
            "class" : ""
        }

    def request(self, route : Route, taxi_class : str = "econom,business,comfortplus") -> requests.Response:
        self.params["rll"] = f"{route.from_coords.longitude},{route.from_coords.latitude}~{route.dest_coords.longitude},{route.dest_coords.latitude}"
        self.params["class"] = f"{taxi_class}"

        return requests.get(url=TaxiRouteInfoApi.api_url, params=self.params, headers=TaxiRouteInfoApi.headers)
