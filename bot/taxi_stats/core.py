from .db_interface import DataBase
from .taxi_route_info_api import TaxiRouteInfoApi
from .route import Route, GeographicCoordinate
from .time_schedule import Week, Day
from .trip_info import TripInfo, parse_response
from datetime import datetime, time

class DayRequest(Day):
    pass

class Core:
    def __init__(self) -> None:
        import json
        with open("configs/yandex_taxi_api.json", "r", encoding='utf-8') as config_file:
            config = json.load(config_file)

        self._request_schedule = Week()
        self.db = DataBase()
        self.taxi_api = TaxiRouteInfoApi(CLID=config.get("CLID"), APIKEY=config.get("APIKEY"))
        
        self.load_from_db()
    
    def load_from_db(self):
        rows = self.db.request_schedule_table.get_all_schedule()
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

                    self._request_schedule.add()

    def add_route(self, route : Route, week : Week, client_id):
        # Сохранили в БД маршрут
        route_id = self.db.routes_table.insert_data(route, client_id)
        for day in week.days.values():
            for time in day.time_schedule:
                day.time_schedule[time].append(route_id)
                
        # Сохранили в БД расписание
        self.db.request_schedule_table.insert_data(route_id, week)
        
        self._request_schedule.add(day)

    def execute(self, route_id):
        route = self.db.routes_table.get_route(route_id)
        
        current_datetime = datetime.now()
        response = self.taxi_api.request(route)
        request = self.taxi_api.params
        
        self.db.debug_table.insert_data(current_datetime.strftime("%Y-%m-%d %H:%M:%S"), route_id, request, response.status_code, response.json())
        
        if response.status_code == 200:
            info_list = parse_response(response)
            for obj in info_list:
                if obj.is_available():
                    self.db.available_trips_statistics_table.insert_data(current_datetime, route_id, obj)
                else:
                    self.db.unavailable_trips_statistics_table.insert_data(current_datetime, route_id, obj)

