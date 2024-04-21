import asyncio
from taxi_stats.core import QueryCore
import logging, sys


def load_from_file(core: QueryCore):
    import json
    from taxi_stats.route import Route, GeographicCoordinate

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
    for route in routes:
        core.db.routes_table.insert_data(route, 0)


async def start():
    core = QueryCore()
    # load_from_file(core)
    await core.run_event_loop()


if __name__ == "__main__":
    logging.basicConfig(
        format="%(asctime)s - %(levelname)s - %(message)s",
        level=logging.DEBUG,
        stream=sys.stdout,
    )
    asyncio.run(start())
