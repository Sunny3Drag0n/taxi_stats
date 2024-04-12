import asyncio
from .db_interface import DataBase
from .taxi_route_info_api import TaxiRouteInfoApi
from .route import Route, GeographicCoordinate
from .time_schedule import Week, Day
from .trip_info import TripInfo, parse_response
from .server import Server
from datetime import datetime, time, timedelta


class Core:
    def __init__(self) -> None:
        import json

        with open("configs/yandex_taxi_api.json", "r", encoding="utf-8") as config_file:
            config = json.load(config_file)

        self.db = DataBase()
        self.taxi_api = TaxiRouteInfoApi(
            CLID=config.get("CLID"), APIKEY=config.get("APIKEY")
        )

        self._load_schedule_from_db()

    def _load_schedule_from_db(self):
        """
        Загрузка расписания из БД
        """
        rows = self.db.request_schedule_table.get_all_schedule()
        self._request_schedule = Week()
        for row in rows:
            id = row[0]
            route_id = row[1]
            schedule = row[2]
            for day_name, time_list in schedule.items():
                if len(time_list) > 0:
                    day = Day(day_name)
                    for time_str in time_list:
                        key = time.fromisoformat(time_str)
                        day.add_time(key)
                        day.time_schedule[key].append(route_id)

                    self._request_schedule.add(day=day)

    async def add_route(self, route: Route, week: Week, client_id):
        """
        Интерфейс добавления маршрута с расписанием для пользователя
        с сохранением всех данных в БД.
        """
        # Сохранили в БД маршрут
        route_id = self.db.routes_table.insert_data(route, client_id)
        for day in week.days.values():
            for time in day.time_schedule:
                day.time_schedule[time].append(route_id)

        # Сохранили в БД расписание
        self.db.request_schedule_table.insert_data(route_id, week)

        self._request_schedule.add(day)

    async def execute_request_from_api(self, route_id):
        """
        Выполнение запроса данных по маршруту
        с сохранением всех данных в БД.
        """
        route = self.db.routes_table.get_route(route_id)

        current_datetime = datetime.now()
        response = self.taxi_api.request(route)
        request = self.taxi_api.params

        self.db.debug_table.insert_data(
            current_datetime.strftime("%Y-%m-%d %H:%M:%S"),
            route_id,
            request,
            response.status_code,
            response.json(),
        )

        if response.status_code == 200:
            info_list = parse_response(response)
            for obj in info_list:
                if obj.is_available():
                    self.db.available_trips_statistics_table.insert_data(
                        current_datetime, route_id, obj
                    )
                else:
                    self.db.unavailable_trips_statistics_table.insert_data(
                        current_datetime, route_id, obj
                    )

    async def wait_next_task(self) -> list[int]:
        """
        Ожидание времени следующего запроса в расписании.
        Асинхронно ожидаем по минуте времени наступления события,
        Возвращаем list[route_id] когда текущее время
        с погрешностью в 1 мин удовлетворяет искомое.
        """
        while True:
            next_task_timepoint, ids = self._request_schedule.next_time_point()
            delta = abs(next_task_timepoint - datetime.now())
            if delta <= timedelta(minutes=1):
                return ids
            elif delta < timedelta(minutes=2):
                await asyncio.sleep(delta.seconds)
            else:
                await asyncio.sleep(60)

    async def run_event_loop(self):
        """
        Основной цикл обработки:
            ждем наступления нужного события,
            выполняем запросы
        """
        while True:
            ids = self.wait_next_task()
            for route_id in ids:
                self.execute_request_from_api(route_id)

    async def _handle(self, message):
        print(message)
        pass
