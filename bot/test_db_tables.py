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

    routes_table.insert_data(client_id=client_id, route=route)
    routes_table.insert_data(client_id=client_id, route=route1)


def test_request_schedule_table(request_schedule_table: RequestScheduleTable):
    # существует route_id 2, 4, 5
    def test_route_2():
        week = Week()
        sunday = Day(Week.days_names[0])
        sunday.add_to_schedule(2, [time(6, 0), time(12, 10), time(11, 30)])
        week.add(sunday)

        monday = Day(Week.days_names[1])
        monday.add_to_schedule(2, [time(7, 0), time(12, 0), time(17, 30)])
        week.add(monday)

        request_schedule_table.insert_data(route_id=2, schedule=week)
        week_route_2 = request_schedule_table.get_route_schedule(route_id=2)
        assert week_route_2 == week

    test_route_2()

    def test_route_4():
        route_4_week = Week()
        route_4_monday = Day(Week.days_names[1])
        route_4_monday.add_to_schedule(4, [time(8, 0), time(9, 0), time(10, 30)])
        route_4_week.add(route_4_monday)

        request_schedule_table.insert_data(route_id=4, schedule=route_4_week)
        get_route_4_week = request_schedule_table.get_route_schedule(route_id=4)
        assert get_route_4_week == route_4_week

    test_route_4()

    # Проверяю все расписание
    schedule = request_schedule_table.get_all_schedule()
    for day in schedule.days.values():
        if day.name == Week.days_names[1]:
            assert len(day.time_schedule) == 6
        else:
            assert len(day.time_schedule) == 3

        for _, ids in day.time_schedule.items():
            assert len(ids) == 1

    # Проверка удаления
    request_schedule_table.delete_data(4)
    schedule = request_schedule_table.get_all_schedule()
    for day in schedule.days.values():
        assert len(day.time_schedule) == 3
        for _, ids in day.time_schedule.items():
            assert len(ids) == 1


if __name__ == "__main__":
    config_file = "configs/test_db.yml"
    DataBase._drop_db(config_file)
    db = DataBase(config_file)
    test_routes_table(db.routes_table)
    test_request_schedule_table(db.request_schedule_table)
