import requests

def seconds_to_time(seconds):
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = seconds % 60
    return '{:02d}:{:02d}:{:02d}'.format(int(hours), int(minutes), int(seconds))

class TripInfo:
    """
    Сущность, содержащая данные о маршруте
    """
    def __init__(self, distance : float, time : float, options : dict):
        self._distance : float = distance    # Длина маршрута, м
        self._time : float = time            # Время поездки, сек
        self._options = options
        self._datetime = time

    def is_available(self) -> bool:
        """Доступна ли поездка"""
        return 'waiting_time' in self._options
    
    def travel_distance(self) -> float:
        return self._distance
    
    def travel_time(self) -> float:
        return self._time
    
    def class_level(self) -> int:
        return self._options['class_level']
    
    def class_text(self) -> str:
        return self._options['class_text']

    def price(self) -> float:
        return self._options['price']

    def waiting_time(self) -> float:
        return self._options['waiting_time'] if 'waiting_time' in self._options else 0

    def __str__(self):
        return f'''
    Длина маршрута, м: {self.travel_distance()}
    Время поездки: {seconds_to_time(self.travel_time())}
    Тариф поездки: {self.class_text()}
    {f'''
    Время ожидания машины: {seconds_to_time(self.waiting_time())}
    Стоимость поездки: {self.price()}''' if self.is_available() else 'Поездка недоступна'}
    '''

def parse_response(response : requests.Response) -> list[TripInfo]:
    """
    Парсинг 
    """
    data = response.json()
    return [TripInfo(distance=data['distance'], time=data['time'], options=options) for options in data['options']]
