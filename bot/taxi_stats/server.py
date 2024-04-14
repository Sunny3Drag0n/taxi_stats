import asyncio
from aiohttp import web
import json

from .route import Route, GeographicCoordinate
from .time_schedule import Week, Day
from .core import QueryCore
from .route import Route


class AddRouteMessage:
    def __init__(self, client_id: int, route: Route) -> None:
        self.client_id = client_id
        self.route = route

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


class GetRouteMessage:
    def __init__(self, route_id: int, route: Route) -> None:
        self.route_id = route_id
        self.route = route

    def from_json(data) -> "GetRouteMessage":
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


class EditRouteScheduleMessage:
    def __init__(self, route_id: int, schedule: Week) -> None:
        self.route_id = route_id
        self.schedule = schedule

    def from_json(data) -> "EditRouteScheduleMessage":
        route_id = data.get("route_id")
        schedule = data.get("schedule")
        week = Week.from_json(schedule)
        return EditRouteScheduleMessage(route_id, week)

    def to_json(self):
        return {
            "route_id": f"{self.route_id}",
            "schedule": {json.dumps(self.schedule.get_mapping())},
        }


class CoreInterface(QueryCore):
    def __init__(self):
        QueryCore.__init__(self)

    def has_access(self, client_id: int, route_id: int):
        routes = self.db.routes_table.get_all_routes(client_id=client_id)
        return route_id in routes

    def add_route(self, client_id: int, route: Route) -> int:
        """
        Интерфейс добавления маршрута с расписанием для пользователя
        """
        route_id = self.db.routes_table.insert_data(route, client_id)
        return route_id

    def add_route_schedule(self, route_id: int, week: Week):
        """
        Интерфейс добавления расписания маршрута
        """
        self.db.request_schedule_table.insert_data(route_id, week)

    def delete_route_schedule(self, route_id: int):
        """
        Удаляет расписание маршрута.
        """
        self.db.request_schedule_table.delete_data(route_id)


class Server:
    def __init__(self) -> None:
        self.core = CoreInterface()

    def run(self):
        app = web.Application()
        app.router.add_post("/add_route", self.add_route)
        app.router.add_post("/add_route_schedule", self.add_route_schedule)
        app.router.add_get("/get_all_routes", self.get_all_routes)
        app.router.add_get("/get_route_info", self.get_route_info)
        app.router.add_delete("/delete_route_schedule", self.delete_route_schedule)
        web.run_app(app=app, host="localhost", port=13337)

    async def add_route(self, request):
        data = await request.json()
        try:
            route_message = AddRouteMessage.from_json(data=data)
            route_id = self.core.add_route(route_message.client_id, route_message.route)
            return web.json_response(status=200, data={"route_id": f"{route_id}"})
        except Exception as e:
            example_message = AddRouteMessage(
                0, Route(GeographicCoordinate(0, 0), GeographicCoordinate(1, 1))
            )
            return web.json_response(
                status=400,
                data=example_message.to_json(),
            )

    async def add_route_schedule(self, request):
        data = await request.json()
        try:
            client_id = data.get("client_id")
            message = EditRouteScheduleMessage.from_json(data=data)
            if self.core.has_access(
                client_id,
            ):
                self.core.add_route_schedule(
                    route_id=message.route_id, week=message.schedule
                )
                return web.json_response(
                    status=200, data={"client_id": f"{client_id}", "route_id": f"{0}"}
                )
            return web.json_response(status=401, data={"message": "access denied"})

        except Exception as e:
            return web.json_response(status=400)

    async def delete_route_schedule(self, request):
        data = await request.json()
        try:
            client_id = data.get("client_id")
            route_id = data.get("route_id")
            if self.core.has_access(
                client_id,
            ):
                self.core.delete_route_schedule(route_id=route_id)
                return web.json_response({"message": "Route deleted successfully"})

            return web.json_response(status=401, data={"message": "access denied"})

        except Exception as e:
            return web.json_response(status=404)

    async def get_all_routes(self, request):
        data = await request.json()
        try:
            client_id = data.get("client_id")
            routes = self.core.db.routes_table.get_all_routes(client_id=client_id)
            routes_json = {
                "client_id": f"{client_id}",
                "routes": [
                    GetRouteMessage(route_id, route).to_json()
                    for route_id, route in routes.items()
                ],
            }
            return web.json_response(routes_json)
        except Exception as e:
            return web.json_response(status=404)

    async def get_route_info(self, request):
        data = await request.json()
        try:
            client_id = data.get("client_id")
            route_id = data.get("route_id")
            route = self.core.db.routes_table.get_route(
                route_id=route_id, client_id=client_id
            )
            if self.core.has_access(
                client_id,
            ):
                routes_json = {
                    "client_id": f"{client_id}",
                    "routes": [GetRouteMessage(route_id, route).to_json()],
                }
                return web.json_response(routes_json)

            return web.json_response(status=401, data={"message": "access denied"})

        finally:
            return web.json_response(status=404)
