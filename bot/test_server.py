from taxi_stats.server import (
    AddRouteMessage,
    RouteInfoMessage,
    ListOfRouteInfoMessage,
    EditRouteScheduleMessage,
    send_add_route_message,
    send_add_route_schedule_message,
    send_get_all_routes_message,
    send_get_route_info_message,
)
from taxi_stats.route import Route, GeographicCoordinate
from pprint import pprint

url = "http://localhost:13337"


client_id = 0

routes = send_get_all_routes_message(url, client_id)
if routes is not None:
    for route in routes.routes:
        pprint(route.to_json())

# route = Route(GeographicCoordinate(, ), GeographicCoordinate(, ), "тестовый маршрут")
