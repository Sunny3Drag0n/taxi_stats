import psycopg2
from psycopg2 import pool
import yaml
from .db_tables import *


class DataBase:
    def _db_exist(cursor, dbname):
        cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (dbname,))
        return cursor.fetchone()

    def _create_database_if_not_exist(dbname, user, password, host, port):
        conn = psycopg2.connect(
            dbname="postgres", user=user, password=password, host=host, port=port
        )
        conn.autocommit = True
        cursor = conn.cursor()

        if not DataBase._db_exist(cursor=cursor, dbname=dbname):
            print(f"Создана БД {dbname}")
            cursor.execute(f"CREATE DATABASE {dbname}")

        conn.close()

    def __init__(self, config_file="configs/database.yml") -> None:
        print(f"Создание бд из конфига: {config_file}")
        with open(config_file, "r") as file:
            config = yaml.safe_load(file)

        DataBase._create_database_if_not_exist(
            dbname=config["postgres"]["dbname"],
            user=config["postgres"]["user"],
            password=config["postgres"]["password"],
            host=config["postgres"]["host"],
            port=config["postgres"]["port"],
        )

        self._connection_pool = pool.SimpleConnectionPool(
            minconn=1,
            maxconn=10,
            dbname=config["postgres"]["dbname"],
            user=config["postgres"]["user"],
            password=config["postgres"]["password"],
            host=config["postgres"]["host"],
            port=config["postgres"]["port"],
        )

        self.routes_table = RoutesTable(self._connection_pool)
        self.requests_table = ApiRequestsTable(self._connection_pool)
        self.request_schedule_table = RequestScheduleTable(self._connection_pool)
        self.unavailable_trips_statistics_table = UnavailableTripsStatisticsTable(
            self._connection_pool
        )
        self.available_trips_statistics_table = AvailableTripsStatisticsTable(
            self._connection_pool
        )
