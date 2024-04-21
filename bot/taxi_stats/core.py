import asyncio
from .db_interface import DataBase
from .taxi_route_info_api import TaxiRouteInfoApi
from .time_schedule import Week, Day
from .trip_info import parse_response
from datetime import datetime, time, timedelta
import logging


class QueryCore:
    """
    Запускает основной event_loop модуля выполнения запросов
    """

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
        logging.info(f"[QueryCore] Обновление расписания из БД")
        self._request_schedule = self.db.request_schedule_table.get_all_schedule()

    def _parse_response(self, route_id, request_id, response):
        """
        Парсинг данных от API taxi и распределение по соотв. таблицам
        """
        if response.status_code == 200:
            info_list = parse_response(response)
            for obj in info_list:
                if obj.is_available():
                    self.db.available_trips_statistics_table.insert_data(
                        request_id, route_id, obj
                    )
                else:
                    self.db.unavailable_trips_statistics_table.insert_data(
                        request_id, route_id, obj
                    )

    def _execute_request_from_api(self, route_id):
        """
        Выполнение запроса данных по маршруту
        с сохранением всех данных в БД.
        """
        route = self.db.routes_table.get_route(route_id)

        current_datetime = datetime.now()
        response = self.taxi_api.request(route)
        request = self.taxi_api.params

        request_id = self.db.requests_table.insert_data(
            current_datetime.strftime("%Y-%m-%d %H:%M:%S"),
            route_id,
            request,
            response.status_code,
            response.json(),
        )
        self._parse_response(route_id, request_id, response)

    async def _wait_next_task(self) -> list[int]:
        """
        Ожидание времени следующего запроса в расписании.
        Асинхронно ожидаем по минуте времени наступления события,
        Периодически обновляем расписание из БД.
        Возвращаем list[route_id] когда текущее время
        с погрешностью в 1 мин удовлетворяет искомое.
        """
        while True:
            next_task_timepoint, ids = self._request_schedule.next_time_point()
            if next_task_timepoint is not None:
                delta = abs(next_task_timepoint - datetime.now())
                logging.info(
                    f"[QueryCore] Следующий запрос: {next_task_timepoint.isoformat()}"
                )
                if delta <= timedelta(minutes=1):
                    await asyncio.sleep(delta.seconds + 1)
                    return ids

            else:
                logging.info(f"[QueryCore] Следующий запрос не найден")

            await asyncio.sleep(60)

            self._load_schedule_from_db()

    async def run_event_loop(self):
        """
        Основной цикл обработки:
            ждем наступления нужного события,
            выполняем запросы
        """
        while True:
            ids = await self._wait_next_task()
            for route_id in ids:
                logging.info(f"[QueryCore] Выполнение запроса для route_id={route_id}")
                self._execute_request_from_api(route_id)
