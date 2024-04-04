from taxi_stats.price_checker import *
from taxi_stats.route import *

try:
    import json
    with open("configs/yandex_taxi_api.json", "r", encoding='utf-8') as config_file:
        config = json.load(config_file)

    routes=[Route(comment=json_obj['comment'],
            from_coords=GeographicCoordinate(json_obj['from'][0],json_obj['from'][1]),
            dest_coords=GeographicCoordinate(json_obj['dest'][0],json_obj['dest'][1]))
            for json_obj in config.get("routes")
    ]
    api = TaxiRouteInfoApi(CLID=config.get("CLID"), APIKEY=config.get("APIKEY"))

    for route in routes:
        response = api.request(route=route)
        if response.status_code == 200:
            info_list = parse_response(response)
            for obj in info_list:
                print(f'Результат по маршруту \"{route.comment}\"')
                print(obj)

        else:
            print("Ошибка при запросе:", response.status_code)

except Exception as e:
    print(e)