import asyncio
from aiohttp import web
import json

from .route import Route, GeographicCoordinate
from .time_schedule import Week, Day
from .core import Core


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


class Server:
    def __init__(self, core: Core) -> None:
        self.core = core

    async def run(self):
        app = web.Application()
        app.router.add_post("/add_route", self.add_route)
        app.router.add_post("/add_route_schedule", self.add_route_schedule)
        app.router.add_get("/get_all_routes", self.get_all_routes)
        app.router.add_get("/get_route_info", self.get_route_info)
        app.router.add_delete("/delete_route_schedule", self.delete_route_schedule)
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, "localhost", 13337)
        await site.start()

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
            self.core.add_route_schedule(
                route_id=message.route_id, week=message.schedule
            )
            return web.json_response(
                status=200, data={"client_id": f"{client_id}", "route_id": f"{0}"}
            )
        except Exception as e:
            return web.json_response(status=400)

    async def delete_route_schedule(self, request):
        data = await request.json()
        try:
            client_id = data.get("client_id")
            route_id = data.get("route_id")
            self.core.remove_route(route_id=route_id, client_id=client_id)
            return web.json_response({"message": "Route deleted successfully"})
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
            if route is not None:
                routes_json = {
                    "client_id": f"{client_id}",
                    "routes": [GetRouteMessage(route_id, route).to_json()],
                }
                return web.json_response(routes_json)
        finally:
            return web.json_response(status=404)
