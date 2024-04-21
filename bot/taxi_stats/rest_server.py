from aiohttp import web
import logging
from .db_interface import DataBase
from .rest_messages import (
    AddRouteMessage,
    SuccesfulRouteMessage,
    RouteScheduleMessage,
    ListOfRouteInfoMessage,
    RouteInfoMessage,
)


def benchmark(iters):
    def actual_decorator(func):
        import time

        def wrapper(*args, **kwargs):
            total = 0
            for i in range(iters):
                start = time.time()
                return_value = func(*args, **kwargs)
                end = time.time()
                total = total + (end - start)
            print("[*] Среднее время выполнения: {} секунд.".format(total / iters))
            return return_value

        return wrapper

    return actual_decorator


def log_decorator(func):
    def wrapper(*args, **kwargs):
        logging.debug(f"{func.__name__}: {args} {kwargs}")
        ret = func(*args, **kwargs)
        return ret

    return wrapper


class ServerHandlers:
    def __init__(self) -> None:
        self.db = DataBase()

    @log_decorator
    def _has_access(self, client_id: int, route_id: int) -> bool:
        routes = self.db.routes_table.get_all_routes(client_id=client_id)
        return route_id in routes

    @log_decorator
    async def add_route(self, request):
        """
        Добавить маршрут
        """
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
            return web.json_response(status=400, text=str(e))

    @log_decorator
    async def add_route_schedule(self, request):
        """
        Добавить расписание для маршрута
        """
        data = await request.json()
        try:
            message = RouteScheduleMessage.from_json(data=data)
            if self._has_access(message.client_id, message.route_id):
                self.db.request_schedule_table.insert_data(
                    route_id=message.route_id, schedule=message.schedule
                )
                return web.json_response(
                    status=200,
                    data=SuccesfulRouteMessage(
                        message.client_id, message.route_id
                    ).to_json(),
                )

            return web.json_response(status=401, data={"message": "access denied"})

        except Exception as e:
            return web.json_response(status=404, text=str(e))

    @log_decorator
    async def delete_route(self, request):
        """
        Удалить маршрут
        """
        data = await request.json()
        try:
            client_id = int(data.get("client_id"))
            route_id = int(data.get("route_id"))
            if self._has_access(client_id, route_id):
                self.db.routes_table.delete_data(client_id=client_id, route_id=route_id)
                return web.json_response(
                    status=200,
                    data=SuccesfulRouteMessage(client_id, route_id).to_json(),
                )

            return web.json_response(status=401, data={"message": "access denied"})

        except Exception as e:
            return web.json_response(status=404, text=str(e))

    @log_decorator
    async def delete_route_schedule(self, request):
        """
        Удалить расписание для маршрута
        """
        data = await request.json()
        try:
            client_id = int(data.get("client_id"))
            route_id = int(data.get("route_id"))
            if self._has_access(client_id, route_id):
                self.db.request_schedule_table.delete_data(route_id=route_id)
                return web.json_response(
                    status=200,
                    data=SuccesfulRouteMessage(client_id, route_id).to_json(),
                )

            return web.json_response(status=401, data={"message": "access denied"})

        except Exception as e:
            return web.json_response(status=404, text=str(e))

    @log_decorator
    async def get_all_routes(self, request):
        """
        Получить список маршрутов для client_id
        """
        data = await request.json()
        try:
            client_id = int(data.get("client_id"))
            routes = self.db.routes_table.get_all_routes(client_id=client_id)
            if len(routes) == 0:
                raise Exception("routes not found")

            message = ListOfRouteInfoMessage(
                client_id,
                [
                    RouteInfoMessage(route_id, route)
                    for route_id, route in routes.items()
                ],
            )
            return web.json_response(message.to_json())

        except Exception as e:
            return web.json_response(status=404, text=str(e))

    @log_decorator
    async def get_route_info(self, request):
        """
        Узнать расписание маршрута
        """
        data = await request.json()
        try:
            client_id = int(data.get("client_id"))
            route_id = int(data.get("route_id"))
            if self._has_access(client_id, route_id):
                schedule = self.db.request_schedule_table.get_route_schedule(
                    route_id=route_id
                )
                message = RouteScheduleMessage(client_id, route_id, schedule)
                return web.json_response(message.to_json())

            return web.json_response(status=401, data={"message": "access denied"})

        except Exception as e:
            return web.json_response(status=404, text=str(e))


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
