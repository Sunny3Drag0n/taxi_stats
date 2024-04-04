
class GeographicCoordinate:
    """
    Представление географических координат
    Широта (latitude), Долгота (longitude)
    """
    def __init__(self, latitude : float, longitude : float):
        # Широта
        self.latitude = latitude
        # Долгота
        self.longitude = longitude

class Route:
    """
    Описание маршрута: откуда(from_coords), куда(dest_coords).
    comment - Описание маршрута (пользовательский комментарий)
    """
    def __init__(self, from_coords : GeographicCoordinate, dest_coords : GeographicCoordinate, comment : str = ''):
        self.from_coords = from_coords
        self.dest_coords = dest_coords
        self.comment = comment