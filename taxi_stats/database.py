import psycopg2
import yaml

class DataBase:
    def _db_exist(cursor, dbname):
        cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (dbname,))
        return cursor.fetchone()

    def _table_exists(cursor, table_name):
        cursor.execute("""
            SELECT EXISTS (
                SELECT 1
                FROM information_schema.tables
                WHERE table_name = %s
            )
        """, (table_name,))
        return cursor.fetchone()[0]

    def _create_database_if_not_exist(dbname, user, password, host, port):
        conn = psycopg2.connect(dbname='postgres', user=user, password=password, host=host, port=port)
        conn.autocommit = True
        cursor = conn.cursor()
        
        if not DataBase._db_exist(cursor=cursor, dbname=dbname):
            print(f"Создана БД {dbname}")
            cursor.execute(f"CREATE DATABASE {dbname}")
        
        conn.close()
    
    def __init__(self, config_file='configs/database.yml') -> None:
        print(f'Создание бд из конфига: {config_file}')
        with open(config_file, 'r') as file:
            config = yaml.safe_load(file)

        DataBase._create_database_if_not_exist(dbname=config['postgres']['dbname'],
                                               user=config['postgres']['user'],
                                               password=config['postgres']['password'],
                                               host=config['postgres']['host'],
                                               port=config['postgres']['port'])
        
        self.conn = psycopg2.connect(dbname=config['postgres']['dbname'],
                                               user=config['postgres']['user'],
                                               password=config['postgres']['password'],
                                               host=config['postgres']['host'],
                                               port=config['postgres']['port'])
        self.conn.autocommit = True
        self.cursor = self.conn.cursor()

        if not DataBase._table_exists(self.cursor, table_name='routes'):
            self._create_routes()
        if not DataBase._table_exists(self.cursor, table_name='api_debug'):
            self._create_api_debug()
        if not DataBase._table_exists(self.cursor, table_name='request_schedule'):
            self._create_request_schedule()
        if not DataBase._table_exists(self.cursor, table_name='statistics'):
            self._create_statistics()

    
    def _create_routes(self):
        self.cursor.execute('''
CREATE TABLE routes (
    route_id SERIAL PRIMARY KEY,                -- ID маршрута
    client_id INT,                              -- ID клиента, задавшего маршрут
    from_latitude FLOAT,                        -- Координата начала поездки (широта)
    from_longitude FLOAT,                       -- Координата начала поездки (долгота)
    dest_latitude FLOAT,                        -- Координата завершения поездки (широта)
    dest_longitude FLOAT,                       -- Координата завершения поездки (долгота)
    client_comment TEXT                         -- Пользьвательский комментарий к маршруту
);
''')

# CREATE INDEX idx_routes_client_id ON routes (client_id);

    def _create_request_schedule(self):
        self.cursor.execute('''
CREATE TABLE request_schedule (
    schedule_id SERIAL PRIMARY KEY,             -- ID расписания 
    route_id INT REFERENCES routes(route_id),
                                                -- день недели
    event_day VARCHAR(10) CHECK (event_day IN ('Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday')),
    event_times TIME[]                          -- набор временных меток для запроса
);
''')
                            
# CREATE INDEX idx_request_schedule_event_day ON request_schedule (event_day);
    def _create_api_debug(self):
        self.cursor.execute('''
CREATE TABLE api_debug (
    id SERIAL PRIMARY KEY,                      -- ID запроса к api
    datetime TIMESTAMP,                         -- когда запрос
    route_id INT REFERENCES routes(route_id),
    request_params JSONB,                       -- параметры запроса
    response_code INT,                          -- код ответа
    response_json JSONB                         -- ответ
);
''')
                            
# CREATE INDEX idx_api_debug_datetime ON api_debug (datetime);
# CREATE INDEX idx_api_debug_route_id ON api_debug (route_id);

    def _create_statistics(self):
        self.cursor.execute('''
CREATE TABLE statistics (
    id SERIAL PRIMARY KEY,                      -- ID запроса
    route_id INT REFERENCES routes(route_id),
    api_request_id INT REFERENCES api_debug(id),
    datetime TIMESTAMP,							-- Дата запроса
    travel_time INTERVAL,                       -- Время поездки
    wait_time INTERVAL,                         -- Время ожидания
    trip_class VARCHAR(50),                     -- Класс поездки
    price NUMERIC(10, 2)                        -- Цена поездки
);
''')
# CREATE INDEX idx_statistics_route_id ON statistics (route_id);

    def __del__(self):
        self.conn.close()


if __name__ == '__main__':
    db = DataBase()