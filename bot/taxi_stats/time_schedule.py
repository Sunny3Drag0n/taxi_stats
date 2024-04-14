from datetime import datetime, time, timedelta
from typing import Optional


class Day:
    """
    Расписание на день.
    dict[time, list[id]]
    """

    def __init__(self, name) -> None:
        self.name = name
        self.time_schedule: dict[time, list[int]] = {}

    def add_time(self, time: time):
        """
        Интерфейс заполнения расписания
        """
        self.time_schedule.setdefault(time, [])

    def add_to_schedule(self, id: int, times: list[time]):
        """
        Интерфейс заполнения расписания
        """
        for t in times:
            self.time_schedule.setdefault(t, []).append(id)

    def remove_from_schedule(self, id: int, times: list[time]):
        """
        Интерфейс удаления элементов
        """
        for t in times:
            if t in self.time_schedule and id in self.time_schedule[t]:
                self.time_schedule[t].remove(id)
                if len(self.time_schedule[t]) == 0:
                    del self.time_schedule[t]

    def merge(self, other_day: "Day") -> "Day":
        """
        return Day - совмещенное расписание
        """
        merged_day = Day(self.name)

        for time, ids in self.time_schedule.items():
            merged_day.time_schedule.setdefault(time, []).extend(ids)
        for time, ids in other_day.time_schedule.items():
            merged_day.time_schedule.setdefault(time, []).extend(ids)

        return merged_day

    def next_time_point(
        self, from_datetime: Optional[datetime] = None
    ) -> tuple[time, list[int]]:
        """
        Ищет ближайшее время в расписании
        Returns:
            time: следующая точка времени расписания, если не найдено - None
            list: значение из расписания для ключа time
        """
        if from_datetime is None:
            from_datetime = datetime.now()

        from_time = from_datetime.time()

        next_time = None
        values = []
        for schedule_time, schedule_values in sorted(self.time_schedule.items()):
            if schedule_time > from_time:
                next_time = schedule_time
                values = schedule_values
                break

        return next_time, values


class Week:
    """
    Расписание на неделю.
    """

    days_names = [
        "Sunday",
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
    ]

    def __init__(self) -> None:
        self.days: dict[str, Day] = {
            day_name: Day(day_name) for day_name in Week.days_names
        }

    def add(self, day: Day):
        self.days[day.name] = self.days[day.name].merge(day)

    def get_mapping(self) -> dict[str, list[str]]:
        """
        Returns:
            dict[str, list[str]]: расписание в виде json объекта из меток времени
        Пример:
            {
                "Monday": ["09:00", "12:00", "15:00"],
                "Tuesday": ["10:00", "13:00", "16:00"]
            }
        """
        return {
            day_name: sorted(
                [time.strftime("%H:%M") for time in day.time_schedule.keys()]
            )
            for day_name, day in self.days.items()
        }

    def next_time_point(
        self, from_datetime: Optional[datetime] = None
    ) -> tuple[datetime, list[int]]:
        """
        Ищет ближайшую точку в расписании (за ближайшие 7 дней чтоб не циклиться)
        Returns:
            datetime: следующая точка времени расписания. Если не найдено - None
            list: значение из расписания для datetime
        """
        if from_datetime is None:
            from_datetime = datetime.now()

        next_point = None
        values = []

        days_counter = 0
        while next_point is None and days_counter < 7:
            day_name = from_datetime.strftime("%A")

            next_time, values = self.days[day_name].next_time_point(from_datetime)
            if next_time:
                next_point = datetime(
                    year=from_datetime.year,
                    month=from_datetime.month,
                    day=from_datetime.day,
                    hour=next_time.hour,
                    minute=next_time.minute,
                    second=next_time.second,
                )
            else:
                from_datetime += timedelta(days=1)
                from_datetime = datetime(
                    year=from_datetime.year,
                    month=from_datetime.month,
                    day=from_datetime.day,
                    hour=0,
                    minute=0,
                    second=0,
                )
                days_counter += 1

        return next_point, values

    def from_json(data):
        week = Week()
        for day_name, schedule in data.items():
            day = Day(day_name)
            for t in schedule:
                day.add_time(datetime.strptime(t, "%H:%M").time())
            week.add(day)
        return week
