from taxi_stats.db_interface import DataBase
from taxi_stats.db_tables import *
import pytest


def test_routes_table(routes_table: RoutesTable):
    client_id = 123
    route = Route(
        GeographicCoordinate(0.123, 63.63), GeographicCoordinate(63.63, 63.63)
    )
    route1 = Route(GeographicCoordinate(0.234, 22.22), GeographicCoordinate(2.2, 63.63))

    route_id = routes_table.insert_data(client_id=client_id, route=route)
    assert route_id == 1
    assert routes_table.get_route(route_id) == route

    route_id_1 = routes_table.insert_data(client_id=client_id, route=route1)
    assert route_id_1 == 2
    assert routes_table.get_route(route_id_1) == route1

    map = routes_table.get_all_routes(client_id)
    assert len(map) == 2
    assert map[route_id] == route
    assert map[route_id_1] == route1

    other_client_id = 345
    other_route_id = routes_table.insert_data(client_id=other_client_id, route=route)

    map = routes_table.get_all_routes(client_id)
    assert len(map) == 2
    assert map[route_id] == route
    assert map[route_id_1] == route1

    map = routes_table.get_all_routes(other_client_id)
    assert len(map) == 1
    assert map[other_route_id] == route

    # от нескольких client_id
    map = routes_table.get_all_routes()
    assert len(map) == 3

    # Нет права удаления
    routes_table.delete_data(client_id=111, route_id=route_id)
    assert len(routes_table.get_all_routes()) == 3

    # Есть право на удаление
    routes_table.delete_data(client_id=client_id, route_id=route_id)
    assert len(routes_table.get_all_routes()) == 2
    routes_table.delete_data(client_id=client_id, route_id=33333333)
    assert len(routes_table.get_all_routes()) == 2
    routes_table.delete_data(client_id=other_client_id, route_id=other_route_id)
    assert len(routes_table.get_all_routes()) == 1


if __name__ == "__main__":
    config_file = "configs/test_db.yml"
    DataBase._drop_db(config_file)
    db = DataBase(config_file)
    test_routes_table(db.routes_table)
