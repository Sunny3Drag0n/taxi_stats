from taxi_stats.server import (
    send_add_route_message,
    send_add_route_schedule_message,
    send_get_all_routes_message,
    send_get_route_info_message,
    send_delete_route_schedule_message,
    send_delete_route_message,
)
from taxi_stats.route import Route, GeographicCoordinate
from taxi_stats.time_schedule import Day, Week, time
from pprint import pprint
import json, logging, sys

url = "http://localhost:13337"
client_id = 9999


def load_from_file() -> list[Route]:
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
    return routes


if __name__ == "__main__":
    logging.basicConfig(
        format="%(asctime)s - %(levelname)s - %(message)s",
        level=logging.DEBUG,
        stream=sys.stdout,
    )
    src_routes: dict[int, Route] = {}
    # Добавление всех маршрутов из файла (мои тестовые координаты)
    file_routes = load_from_file()
    for route in file_routes:
        response = send_add_route_message(url, client_id, route)
        assert response is not None
        assert response.client_id == client_id
        src_routes[response.route_id] = route

    week = Week()
    week.days = {day_name: Day(day_name) for day_name in Week.days_names}
    for day in week.days.values():
        day.time_schedule = {
            t: [] for t in [time(7, 0), time(7, 10), time(7, 20), time(7, 30)]
        }

    # Для всех маршрутов добавил расписание на всю неделю
    for id in src_routes.keys():
        response = send_add_route_schedule_message(url, client_id, id, week)
        assert response is not None
        assert response.client_id == client_id

    # Проверяю все добавленные маршруты без прав доступа
    response = send_get_all_routes_message(url, client_id=123)
    assert response is None
    # Проверяю все добавленные маршруты
    response = send_get_all_routes_message(url, client_id)
    assert response is not None
    assert response.client_id == client_id
    for route_msg in response.routes:
        assert route_msg.route_id in src_routes
        assert route_msg.route == src_routes[route_msg.route_id]

    for id, route in src_routes.items():
        response = send_get_route_info_message(url, client_id, id)
        assert response is not None
        assert response.schedule == week

        # Удаляю расписание маршрута, т.к. без этого не удалить маршрут
        response = send_delete_route_schedule_message(url, client_id, id)
        assert response.client_id == client_id and response.route_id == id
        response = send_get_route_info_message(url, client_id, id)
        assert response is not None
        assert len(response.schedule.days) == 0
        # Удаляю эти маршруты т.к. проверил. Для след запуска теста
        response = send_delete_route_message(url, client_id, id)
        assert response.client_id == client_id and response.route_id == id

    response = send_get_all_routes_message(url, client_id)
    assert response is None
