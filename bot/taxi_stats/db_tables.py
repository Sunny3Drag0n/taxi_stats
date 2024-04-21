from .route import Route, GeographicCoordinate
from .time_schedule import Week, Day
from .trip_info import TripInfo
import json
from typing import Optional
from datetime import time


class DbTable:
    def __init__(self, db_connection_pool) -> None:
        self.connection_pool = db_connection_pool
        connection = self.connection_pool.getconn()
        connection.autocommit = True
        self.db_connection = connection

    def __del__(self):
        self.connection_pool.putconn(self.db_connection)

    def _table_exists(cursor, table_name):
        cursor.execute(
            """
            SELECT EXISTS (
                SELECT 1
                FROM information_schema.tables
                WHERE table_name = %s
            )
        """,
            (table_name,),
        )
        return cursor.fetchone()[0]

    def _create_if_noexist(self, cursor, table_name: str, table_def: str):
        if not DbTable._table_exists(cursor, table_name=table_name):
            self.execute(table_def)

    def execute(self, sql_request):
        cursor = self.db_connection.cursor()
        cursor.execute(sql_request)
        cursor.close()

    def insert(self, sql_request) -> int:
        """
        return id записи
        """
        cursor = self.db_connection.cursor()
        cursor.execute(sql_request)
        id = cursor.fetchone()[0]
        cursor.close()
        return id


class RoutesTable(DbTable):
    """
    Таблица содержащая маршруты поездок.
    Маршруты для каждого клиента свои.
    Маршрут: откуда, куда, пользовательский комментарий

    functions:
        insert_data(self, route: Route, client_id: int) -> int
        def delete_data(self, client_id: int, route_id: int)
        get_route(self, route_id: int) -> Route
        get_all_routes(self, client_id: Optional[int] = None) -> dict[int, Route]
    """

    table_name = "routes"

    def __init__(self, db_connection_pool):
        DbTable.__init__(self, db_connection_pool)
        cursor = self.db_connection.cursor()
        self._create_if_noexist(
            cursor,
            self.table_name,
            f"""
        CREATE TABLE {self.table_name} (
            route_id SERIAL PRIMARY KEY,                -- ID маршрута
            client_id INT,                              -- ID клиента, задавшего маршрут
            from_latitude FLOAT,                        -- Координата начала поездки (широта)
            from_longitude FLOAT,                       -- Координата начала поездки (долгота)
            dest_latitude FLOAT,                        -- Координата завершения поездки (широта)
            dest_longitude FLOAT,                       -- Координата завершения поездки (долгота)
            client_comment TEXT                         -- Пользьвательский комментарий к маршруту
        );
        """,
        )
        cursor.close()

    def insert_data(self, route: Route, client_id: int) -> int:
        return self.insert(
            f"""
            INSERT INTO {self.table_name} (
                client_id,
                from_latitude, from_longitude, 
                dest_latitude, dest_longitude, 
                client_comment
            ) VALUES (
                {client_id}, 
                {route.from_coords.latitude}, {route.from_coords.longitude}, 
                {route.dest_coords.latitude}, {route.dest_coords.longitude}, 
                '{route.comment}'
            ) RETURNING route_id;
        """
        )

    def get_route(self, route_id: int) -> Route:
        cursor = self.db_connection.cursor()
        cursor.execute(f"SELECT * FROM {self.table_name} WHERE route_id = {route_id};")
        row = cursor.fetchone()
        cursor.close()
        return Route(
            from_coords=GeographicCoordinate(row[2], row[3]),
            dest_coords=GeographicCoordinate(row[4], row[5]),
            comment=row[6],
        )

    def delete_data(self, client_id: int, route_id: int):
        return self.execute(
            f"""
            DELETE FROM {self.table_name}
            WHERE route_id = {route_id} AND client_id = {client_id};
        """
        )

    def get_all_routes(self, client_id: Optional[int] = None) -> dict[int, Route]:
        cursor = self.db_connection.cursor()
        if client_id is None:
            cursor.execute(f"SELECT * FROM {self.table_name};")
        else:
            cursor.execute(
                f"SELECT * FROM {self.table_name} WHERE client_id = {client_id};"
            )
        rows = cursor.fetchall()
        cursor.close()
        routes = {
            row[0]: Route(
                from_coords=GeographicCoordinate(row[2], row[3]),
                dest_coords=GeographicCoordinate(row[4], row[5]),
                comment=row[6],
            )
            for row in rows
        }
        return routes


class ApiRequestsTable(DbTable):
    """
    Таблица содержащая отладочные данные:
    время запроса, сам запрос, ответ

    functions:
        insert_data(self, datetime: str, route_id: int, request, response_code: int, response) -> int
    """

    table_name = "api_requests"

    def __init__(self, db_connection_pool):
        DbTable.__init__(self, db_connection_pool)
        cursor = self.db_connection.cursor()
        self._create_if_noexist(
            cursor,
            self.table_name,
            f"""
            CREATE TABLE {self.table_name} (
                id SERIAL PRIMARY KEY,                      -- ID запроса к api
                datetime TIMESTAMP,                         -- когда запрос
                route_id INT REFERENCES routes(route_id),
                request_params JSONB,                       -- параметры запроса
                response_code INT,                          -- код ответа
                response_json JSONB                         -- ответ
            );
        """,
        )
        cursor.close()

    def insert_data(
        self, datetime: str, route_id: int, request, response_code: int, response
    ) -> int:
        return self.insert(
            f"""
            INSERT INTO {self.table_name} (
                datetime,
                route_id, 
                request_params, 
                response_code, 
                response_json
                ) VALUES (
                    '{datetime}', 
                    {route_id},
                    '{json.dumps(request)}',
                    {response_code},
                    '{json.dumps(response)}'
                ) RETURNING id;
        """
        )


class RequestScheduleTable(DbTable):
    """
    Таблица содержащая расписание запросов.
    Расписание - мапинг вида {'день недели': ['время1', 'время2']}

    functions:
        insert_data(self, route_id: int, schedule: Week) -> int
        delete_data(self, route_id: int)
        get_route_schedule(self, route_id) -> list
        get_all_schedule(self) -> list
    """

    table_name = "request_schedule"

    def __init__(self, db_connection_pool):
        DbTable.__init__(self, db_connection_pool)
        cursor = self.db_connection.cursor()
        self._create_if_noexist(
            cursor,
            self.table_name,
            f"""
            CREATE TABLE {self.table_name} (
                id SERIAL PRIMARY KEY,                      -- ID расписания 
                route_id INT REFERENCES {RoutesTable.table_name}(route_id),
                day_time_mapping JSONB                      -- расписание запросов в виде JSON соответствия 
            );
        """,
        )
        cursor.close()

    def insert_data(self, route_id: int, schedule: Week) -> int:
        return self.insert(
            f"""
            INSERT INTO {self.table_name} (
                route_id,
                day_time_mapping
                ) VALUES (
                    {route_id}, 
                    '{json.dumps(schedule.get_mapping())}'
                ) RETURNING id;
        """
        )

    def delete_data(self, route_id: int):
        return self.execute(
            f"""
            DELETE FROM {self.table_name}
            WHERE route_id = {route_id};
        """
        )

    def parse_get_response(self, rows) -> Week:
        week = Week()
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

                    week.add(day=day)

        return week

    def get_route_schedule(self, route_id: int) -> Week:
        cursor = self.db_connection.cursor()
        cursor.execute(f"SELECT * FROM {self.table_name} WHERE route_id = {route_id};")
        rows = cursor.fetchall()
        cursor.close()
        return self.parse_get_response(rows)

    def get_all_schedule(self) -> Week:
        cursor = self.db_connection.cursor()
        cursor.execute(f"SELECT * FROM {self.table_name};")
        rows = cursor.fetchall()
        cursor.close()
        return self.parse_get_response(rows)


class UnavailableTripsStatisticsTable(DbTable):
    """
    Таблица с недоступными поездками.
    Информация: когда, какой класс, по какому маршруту

    functions:
        insert_data(self, request_id : int, route_id : int, info: TripInfo)
        ??? get_route_statistics(self, route_id, day_name: str) -> list
    """

    table_name = "statistics_unavailable"

    def __init__(self, db_connection_pool):
        DbTable.__init__(self, db_connection_pool)
        cursor = self.db_connection.cursor()
        self._create_if_noexist(
            cursor,
            self.table_name,
            f"""
            CREATE TABLE {self.table_name} (
                id SERIAL PRIMARY KEY,
                request_id INT REFERENCES {ApiRequestsTable.table_name}(id),
                route_id INT REFERENCES {RoutesTable.table_name}(route_id),
                trip_class VARCHAR(50)                      -- Класс поездки
            );
        """,
        )
        cursor.close()

    def insert_data(self, request_id: int, route_id: int, info: TripInfo):
        if info.is_available():
            raise Exception(f"TripInfo is available")

        return self.execute(
            f"""
            INSERT INTO {self.table_name} (
                request_id
                route_id,
                trip_class
            ) VALUES (
                {request_id},
                {route_id},
                '{info.class_text()}'
            );
        """
        )

    def get_route_statistics(self, route_id, day_name: str) -> list:
        cursor = self.db_connection.cursor()
        cursor.execute(
            f"""
            SELECT * FROM {self.table_name} 
            JOIN {RoutesTable.table_name} ON {self.table_name}.route_id = {RoutesTable.table_name}.route_id 
            WHERE {self.table_name}.route_id = {route_id} 
            AND EXTRACT(dow FROM {self.table_name}.datetime) = {Week.days_names.index(day_name)};
        """
        )
        rows = cursor.fetchall()
        cursor.close()
        return rows


class AvailableTripsStatisticsTable(DbTable):
    """
    Таблица с доступными поездками.
    Цена, время поездки, класс поездки, время ожидания

    functions:
        insert_data(self, datetime, route_id, info: TripInfo) -> int
        ??? get_route_statistics(self, route_id, day_name: str) -> list
    """

    table_name = "statistics_available"

    def __init__(self, db_connection_pool):
        DbTable.__init__(self, db_connection_pool)
        cursor = self.db_connection.cursor()
        self._create_if_noexist(
            cursor,
            self.table_name,
            f"""
            CREATE TABLE {self.table_name} (
                id SERIAL PRIMARY KEY,
                request_id INT REFERENCES {ApiRequestsTable.table_name}(id),
                route_id INT REFERENCES {RoutesTable.table_name}(route_id),
                trip_class VARCHAR(50),                     -- Класс поездки
                travel_time INTERVAL,                       -- Время поездки
                wait_time INTERVAL,                         -- Время ожидания
                price NUMERIC(10, 2)                        -- Цена поездки
            );
        """,
        )
        cursor.close()

    def insert_data(self, request_id: int, route_id: int, info: TripInfo):
        if not info.is_available():
            raise Exception(f"TripInfo is unavailable")

        return self.execute(
            f"""
            INSERT INTO {self.table_name} (
                request_id,
                route_id,
                travel_time, 
                wait_time, 
                trip_class, 
                price
            ) VALUES (
                {request_id},
                {route_id},
                INTERVAL '{info.travel_time()} seconds', 
                INTERVAL '{info.waiting_time()} seconds', 
                '{info.class_text()}',
                {info.price()}
            );
        """
        )

    def get_route_statistics(self, route_id, day_name: str) -> list:
        cursor = self.db_connection.cursor()
        cursor.execute(
            f"""
            SELECT * FROM {self.table_name} 
            JOIN {RoutesTable.table_name} ON {self.table_name}.route_id = {RoutesTable.table_name}.route_id 
            WHERE {self.table_name}.route_id = {route_id} 
            AND EXTRACT(dow FROM {self.table_name}.datetime) = {Week.days_names.index(day_name)};
        """
        )
        rows = cursor.fetchall()
        cursor.close()
        return rows


# CREATE INDEX idx_routes_client_id ON routes (client_id);
# CREATE INDEX idx_request_schedule_event_day ON request_schedule (event_day);
# CREATE INDEX idx_api_debug_datetime ON api_debug (datetime);
# CREATE INDEX idx_api_debug_route_id ON api_debug (route_id);
# CREATE INDEX idx_statistics_route_id ON statistics (route_id);
