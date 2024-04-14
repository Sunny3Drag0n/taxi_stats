from taxi_stats.taxi_route_info_api import *
from taxi_stats.route import *
from taxi_stats.trip_info import *
from taxi_stats.core import *
from taxi_stats.server import *


def old_run():
    try:
        import json

        with open("configs/yandex_taxi_api.json", "r", encoding="utf-8") as config_file:
            config = json.load(config_file)

        routes = [
            Route(
                comment=json_obj["comment"],
                from_coords=GeographicCoordinate(
                    json_obj["from"][0], json_obj["from"][1]
                ),
                dest_coords=GeographicCoordinate(
                    json_obj["dest"][0], json_obj["dest"][1]
                ),
            )
            for json_obj in config.get("routes")
        ]
        api = TaxiRouteInfoApi(CLID=config.get("CLID"), APIKEY=config.get("APIKEY"))

        for route in routes:
            response = api.request(route=route)
            if response.status_code == 200:
                info_list = parse_response(response)
                for obj in info_list:
                    print(f'Результат по маршруту "{route.comment}"')
                    print(obj)

            else:
                print("Ошибка при запросе:", response.status_code)

    except Exception as e:
        print(e)


def generate_day(day_index: int, from_time: str, to_time: str) -> Day:
    day = Day(name=Week.days_names[day_index])

    from datetime import datetime, timedelta, time

    time_point = datetime.strptime(from_time, "%H:%M")
    to_time_point = datetime.strptime(to_time, "%H:%M")

    while time_point <= to_time_point:
        day.add_time(time_point.time())
        time_point += timedelta(minutes=10)

    return day


def generate_test_case(day_index: int) -> tuple[list[Route], Week]:
    import json

    with open("configs/yandex_taxi_api.json", "r", encoding="utf-8") as config_file:
        config = json.load(config_file)

    routes = [
        Route(
            comment=json_obj["comment"],
            from_coords=GeographicCoordinate(json_obj["from"][0], json_obj["from"][1]),
            dest_coords=GeographicCoordinate(json_obj["dest"][0], json_obj["dest"][1]),
        )
        for json_obj in config.get("routes")
    ]
    week = Week()
    week.add(generate_day(day_index, "07:00", "08:10"))

    return routes, week


def fill_from_file(client_id: int, test_day: int, core: CoreInterface):
    routes, week = generate_test_case(test_day)
    for route in routes:
        route_id = core.add_route(route=route, client_id=client_id)
        core.add_route_schedule(route_id, week)


def run():
    client_id = 0
    test_day = 1
    core = CoreInterface()

    # Добавляю тестовые данные
    schedule = core.db.request_schedule_table.get_all_schedule()
    if len(schedule) == 0:
        fill_from_file(client_id, test_day, core)

    # # Хочу пройтись по маршрутам
    # schedule_day = core._request_schedule.days[Week.days_names[test_day]]
    # for time, route_id_list in schedule_day.time_schedule.items():
    #     print(time)
    #     for route_id in route_id_list:
    #         core.execute(route_id)
    #     return


if __name__ == "__main__":
    run()
