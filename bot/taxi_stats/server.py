from aiohttp import web
import json, requests

from .route import Route, GeographicCoordinate
from .time_schedule import Week, Day
from .route import Route
from .db_interface import DataBase


class AddRouteMessage:
    def __init__(self, client_id: int, route: Route) -> None:
        self.client_id: int = client_id
        self.route: Route = route

    def from_json(data) -> "AddRouteMessage":
        client_id = data.get("client_id")
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
        route_id = data.get("route_id")
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
        return AddRouteMessage(route_id, route)

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
        client_id = data.get("client_id")
        return GetListOfRouteInfoMessage(
            client_id,
            [GetRouteInfoMessage.from_json(data) for data in data.get("routes")],
        )

    def to_json(self):
        return {
            "client_id": f"{self.client_id}",
            "routes": [route.to_json() for route in self.routes],
        }


class EditRouteScheduleMessage:
    def __init__(self, client_id: int, route_id: int, schedule: Week) -> None:
        self.client_id: int = client_id
        self.route_id: int = route_id
        self.schedule: Week = schedule

    def from_json(data) -> "EditRouteScheduleMessage":
        client_id = data.get("client_id")
        route_id = data.get("route_id")
        schedule = data.get("schedule")
        week = Week.from_json(schedule)
        return EditRouteScheduleMessage(client_id, route_id, week)

    def to_json(self):
        return {
            "client_id": f"{self.client_id}",
            "route_id": f"{self.route_id}",
            "schedule": {json.dumps(self.schedule.get_mapping())},
        }


class SuccesfulRouteMessage:
    def __init__(self, client_id: int, route_id: int) -> None:
        self.client_id: int = client_id
        self.route_id: int = route_id

    def from_json(data) -> "SuccesfulRouteMessage":
        client_id = data.get("client_id")
        route_id = data.get("route_id")
        return SuccesfulRouteMessage(client_id, route_id)

    def to_json(self):
        return {
            "client_id": f"{self.client_id}",
            "route_id": f"{self.route_id}",
        }


class ServerHandlers:
    def __init__(self) -> None:
        self.db = DataBase()

    def _has_access(self, client_id: int, route_id: int):
        routes = self.db.routes_table.get_all_routes(client_id=client_id)
        return route_id in routes

    async def add_route(self, request):
        data = await request.json()
        try:
            route_message = AddRouteMessage.from_json(data=data)
            route_id = self.db.routes_table.insert_data(
                client_id=route_message.client_id, route=route_message.route
            )
            return web.json_response(
                status=200,
                data=SuccesfulRouteMessage(route_message.client_id, route_id).to_json(),
            )

        except Exception as e:
            return web.json_response(status=400)

    async def add_route_schedule(self, request):
        data = await request.json()
        try:
            message = EditRouteScheduleMessage.from_json(data=data)
            if self._has_access(message.client_id, message.route_id):
                self.db.request_schedule_table.insert_data(
                    route_id=message.route_id, week=message.schedule
                )
                return web.json_response(
                    status=200,
                    data=SuccesfulRouteMessage(
                        message.client_id, message.route_id
                    ).to_json(),
                )

            return web.json_response(status=401, data={"message": "access denied"})

        except Exception as e:
            return web.json_response(status=400)

    async def delete_route(self, request):
        data = await request.json()
        try:
            client_id = data.get("client_id")
            route_id = data.get("route_id")
            if self._has_access(client_id, route_id):
                self.db.routes_table.delete_data(client_id=client_id, route_id=route_id)
                return web.json_response(
                    status=200,
                    data=SuccesfulRouteMessage(client_id, route_id).to_json(),
                )

            return web.json_response(status=401, data={"message": "access denied"})

        except Exception as e:
            return web.json_response(status=404)

    async def delete_route_schedule(self, request):
        data = await request.json()
        try:
            client_id = data.get("client_id")
            route_id = data.get("route_id")
            if self._has_access(client_id, route_id):
                self.db.request_schedule_table.delete_data(route_id=route_id)
                return web.json_response(
                    status=200,
                    data=SuccesfulRouteMessage(client_id, route_id).to_json(),
                )

            return web.json_response(status=401, data={"message": "access denied"})

        except Exception as e:
            return web.json_response(status=404)

    async def get_all_routes(self, request):
        data = await request.json()
        try:
            client_id = data.get("client_id")
            routes = self.db.routes_table.get_all_routes(client_id=client_id)
            message = ListOfRouteInfoMessage(
                client_id,
                [
                    RouteInfoMessage(route_id, route)
                    for route_id, route in routes.items()
                ],
            )
            return web.json_response(message.to_json())

        except Exception as e:
            return web.json_response(status=404)

    async def get_route_info(self, request):
        data = await request.json()
        try:
            client_id = data.get("client_id")
            route_id = data.get("route_id")
            route = self.db.routes_table.get_route(
                route_id=route_id, client_id=client_id
            )
            if self._has_access(client_id, route_id):
                message = ListOfRouteInfoMessage(
                    client_id, [RouteInfoMessage(route_id, route)]
                )
                return web.json_response(message.to_json())

            return web.json_response(status=401, data={"message": "access denied"})

        finally:
            return web.json_response(status=404)


class Server(ServerHandlers):
    def __init__(self) -> None:
        ServerHandlers.__init__(self)

    def run(self, host, port):
        app = web.Application()
        app.router.add_post("/add_route", self.add_route)
        app.router.add_post("/add_route_schedule", self.add_route_schedule)
        app.router.add_get("/get_all_routes", self.get_all_routes)
        app.router.add_get("/get_route_info", self.get_route_info)
        app.router.add_delete("/delete_route_schedule", self.delete_route_schedule)
        app.router.add_delete("/delete_route", self.delete_route)
        web.run_app(app=app, host=host, port=port)


def send_add_route_message(url, client_id: int, route: Route) -> SuccesfulRouteMessage:
    try:
        message = AddRouteMessage(client_id, route)
        response = requests.post(url=url + "/add_route", json=message.to_json())

        if response.status_code == 200:
            data = response.json()
            return SuccesfulRouteMessage.from_json(data)

    except Exception as e:
        pass

    return None


def send_add_route_schedule_message(url, client_id: int, route_id: int, schedule: Week):
    try:
        message = EditRouteScheduleMessage(client_id, route_id, schedule)
        response = requests.post(
            url=url + "/add_route_schedule", json=message.to_json()
        )

        if response.status_code == 200:
            data = response.json()
            return SuccesfulRouteMessage.from_json(data)

    except Exception as e:
        pass

    return None


def send_get_all_routes_message(url, client_id: int) -> ListOfRouteInfoMessage:
    try:
        response = requests.get(
            url=url + "/get_all_routes",
            json={
                "client_id": f"{client_id}",
            },
        )

        if response.status_code == 200:
            data = response.json()
            return ListOfRouteInfoMessage.from_json(data)

    except Exception as e:
        pass

    return None


def send_get_route_info_message(
    url, client_id: int, route_id: int
) -> ListOfRouteInfoMessage:
    try:
        response = requests.get(
            url=url + "/get_route_info",
            json={"client_id": f"{client_id}", "route_id": f"{route_id}"},
        )

        if response.status_code == 200:
            data = response.json()
            return ListOfRouteInfoMessage.from_json(data)

    except Exception as e:
        pass

    return None


def send_delete_route_schedule_message(
    url, client_id: int, route_id: int
) -> SuccesfulRouteMessage:
    try:
        response = requests.delete(
            url=url + "/delete_route_schedule",
            json={"client_id": f"{client_id}", "route_id": f"{route_id}"},
        )

        if response.status_code == 200:
            data = response.json()
            return SuccesfulRouteMessage.from_json(data)

    except Exception as e:
        pass

    return None


def send_delete_route_message(
    url, client_id: int, route_id: int
) -> SuccesfulRouteMessage:
    try:
        response = requests.delete(
            url=url + "/delete_route",
            json={"client_id": f"{client_id}", "route_id": f"{route_id}"},
        )

        if response.status_code == 200:
            data = response.json()
            return SuccesfulRouteMessage.from_json(data)

    except Exception as e:
        pass

    return None
