from .route import Route, GeographicCoordinate
from .time_schedule import Week
from .route import Route
import requests, logging


class AddRouteMessage:
    def __init__(self, client_id: int, route: Route) -> None:
        self.client_id: int = client_id
        self.route: Route = route

    def from_json(data) -> "AddRouteMessage":
        client_id = int(data.get("client_id"))
        from_coord = data.get("from")
        dest_coord = data.get("dest")
        comment = data.get("comment")
        from_ = GeographicCoordinate(
            latitude=from_coord.get("latitude"),
            longitude=from_coord.get("longitude"),
        )
        dest_ = GeographicCoordinate(
            latitude=dest_coord.get("latitude"),
            longitude=dest_coord.get("longitude"),
        )
        route = Route(from_, dest_, comment=comment)
        return AddRouteMessage(client_id, route)

    def to_json(self):
        return {
            "client_id": f"{self.client_id}",
            "from": {
                "latitude": f"{self.route.from_coords.latitude}",
                "longitude": f"{self.route.from_coords.longitude}",
            },
            "dest": {
                "latitude": f"{self.route.dest_coords.latitude}",
                "longitude": f"{self.route.dest_coords.longitude}",
            },
            "comment": f"{self.route.comment}",
        }


class RouteInfoMessage:
    def __init__(self, route_id: int, route: Route) -> None:
        self.route_id: int = route_id
        self.route: Route = route

    def from_json(data) -> "RouteInfoMessage":
        route_id = int(data.get("route_id"))
        from_coord = data.get("from")
        dest_coord = data.get("dest")
        comment = data.get("comment")
        from_ = GeographicCoordinate(
            latitude=float(from_coord.get("latitude")),
            longitude=float(from_coord.get("longitude")),
        )
        dest_ = GeographicCoordinate(
            latitude=float(dest_coord.get("latitude")),
            longitude=float(dest_coord.get("longitude")),
        )
        route = Route(from_, dest_, comment=comment)
        return RouteInfoMessage(route_id, route)

    def to_json(self):
        return {
            "route_id": f"{self.route_id}",
            "from": {
                "latitude": f"{self.route.from_coords.latitude}",
                "longitude": f"{self.route.from_coords.longitude}",
            },
            "dest": {
                "latitude": f"{self.route.dest_coords.latitude}",
                "longitude": f"{self.route.dest_coords.longitude}",
            },
            "comment": f"{self.route.comment}",
        }


class ListOfRouteInfoMessage:
    def __init__(self, client_id, routes: list[RouteInfoMessage]) -> None:
        self.client_id: int = client_id
        self.routes: list[RouteInfoMessage] = routes

    def from_json(data) -> "ListOfRouteInfoMessage":
        client_id = int(data.get("client_id"))
        return ListOfRouteInfoMessage(
            client_id,
            [RouteInfoMessage.from_json(data) for data in data.get("routes")],
        )

    def to_json(self):
        return {
            "client_id": f"{self.client_id}",
            "routes": [route.to_json() for route in self.routes],
        }


class RouteScheduleMessage:
    def __init__(self, client_id: int, route_id: int, schedule: Week) -> None:
        self.client_id: int = client_id
        self.route_id: int = route_id
        self.schedule: Week = schedule

    def from_json(data) -> "RouteScheduleMessage":
        client_id = int(data.get("client_id"))
        route_id = int(data.get("route_id"))
        schedule = data.get("schedule")
        week = Week.from_json(schedule)
        return RouteScheduleMessage(client_id, route_id, week)

    def to_json(self):
        return {
            "client_id": f"{self.client_id}",
            "route_id": f"{self.route_id}",
            "schedule": self.schedule.get_mapping(),
        }


class SuccesfulRouteMessage:
    def __init__(self, client_id: int, route_id: int) -> None:
        self.client_id: int = client_id
        self.route_id: int = route_id

    def from_json(data) -> "SuccesfulRouteMessage":
        client_id = int(data.get("client_id"))
        route_id = int(data.get("route_id"))
        return SuccesfulRouteMessage(client_id, route_id)

    def to_json(self):
        return {
            "client_id": f"{self.client_id}",
            "route_id": f"{self.route_id}",
        }


# Декораторы


def message_decorator(func):
    def wrapper(*args, **kwargs):
        logging.debug(f"{func.__name__}: {args} {kwargs}")
        ret = func(*args, **kwargs)
        return ret

    return wrapper


def succesful_route_message_decorator(func):
    def wrapper(*args, **kwargs):
        try:
            decorator = message_decorator(func)
            response = decorator(*args, **kwargs)
            if response.status_code == 200:
                data = response.json()
                return SuccesfulRouteMessage.from_json(data)

            logging.debug(f"{func.__name__} status code: {response.status_code}")

        except Exception as e:
            logging.debug(str(e))

        return None

    return wrapper


def get_routes_message_decorator(func):
    def wrapper(*args, **kwargs):
        try:
            decorator = message_decorator(func)
            response = decorator(*args, **kwargs)
            if response.status_code == 200:
                data = response.json()
                return ListOfRouteInfoMessage.from_json(data)

            logging.debug(f"{func.__name__} status code: {response.status_code}")

        except Exception as e:
            logging.debug(str(e))

        return None

    return wrapper


def get_route_schedule_message_decorator(func):
    def wrapper(*args, **kwargs):
        try:
            decorator = message_decorator(func)
            response = decorator(*args, **kwargs)
            if response.status_code == 200:
                data = response.json()
                return RouteScheduleMessage.from_json(data)

            logging.debug(f"{func.__name__} status code: {response.status_code}")

        except Exception as e:
            logging.debug(str(e))

        return None

    return wrapper


# Интерфейс запросов


@succesful_route_message_decorator
def send_add_route_message(url, client_id: int, route: Route) -> SuccesfulRouteMessage:
    """
    Добавить маршрут
    """
    message = AddRouteMessage(client_id, route)
    return requests.post(url=url + "/add_route", json=message.to_json())


@succesful_route_message_decorator
def send_add_route_schedule_message(
    url, client_id: int, route_id: int, schedule: Week
) -> SuccesfulRouteMessage:
    """
    Добавить расписание для маршрута
    """
    message = RouteScheduleMessage(client_id, route_id, schedule)
    return requests.post(url=url + "/add_route_schedule", json=message.to_json())


@get_routes_message_decorator
def send_get_all_routes_message(url, client_id: int) -> ListOfRouteInfoMessage:
    """
    Получить список маршрутов для client_id
    """
    return requests.get(
        url=url + "/get_all_routes",
        json={
            "client_id": f"{client_id}",
        },
    )


@get_route_schedule_message_decorator
def send_get_route_info_message(
    url, client_id: int, route_id: int
) -> RouteScheduleMessage:
    """
    Узнать расписание маршрута
    """
    return requests.get(
        url=url + "/get_route_info",
        json={"client_id": f"{client_id}", "route_id": f"{route_id}"},
    )


@succesful_route_message_decorator
def send_delete_route_schedule_message(
    url, client_id: int, route_id: int
) -> SuccesfulRouteMessage:
    """
    Удалить расписание для маршрута
    """
    return requests.delete(
        url=url + "/delete_route_schedule",
        json={"client_id": f"{client_id}", "route_id": f"{route_id}"},
    )


@succesful_route_message_decorator
def send_delete_route_message(
    url, client_id: int, route_id: int
) -> SuccesfulRouteMessage:
    """
    Удалить маршрут
    """
    return requests.delete(
        url=url + "/delete_route",
        json={"client_id": f"{client_id}", "route_id": f"{route_id}"},
    )
