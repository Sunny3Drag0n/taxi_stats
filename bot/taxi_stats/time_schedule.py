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

    def add_time(self, time : time):
        self.time_schedule.setdefault(time, [])

    def merge(self, other_day: 'Day') -> 'Day':
        merged_day = Day(self.name)
        
        for time, ids in self.time_schedule.items():
            merged_day.time_schedule.setdefault(time, []).extend(ids)
        for time, ids in other_day.time_schedule.items():
            merged_day.time_schedule.setdefault(time, []).extend(ids)

        return merged_day

    def next_time_point(self, from_datetime: Optional[datetime] = None) -> time:
        """
        Ищет ближайшее время в расписании
        Returns:
            time: следующая точка времени расписания.
            Если не найдено - None
        """
        if from_datetime is None:
            from_datetime = datetime.now()

        from_time = from_datetime.time()

        next_time = None
        for schedule_time in sorted(self.time_schedule.keys()):
            if schedule_time > from_time:
                next_time = schedule_time
                break

        return next_time

class Week:
    """
    Расписание на неделю.
    Пример расписания, полученного из get_mapping
        {
            "Monday": ["09:00", "12:00", "15:00"],
            "Tuesday": ["10:00", "13:00", "16:00"]
        }
    """
    days_names = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
    def __init__(self) -> None:
        self.days : dict[str, Day] = {day_name: Day(day_name) for day_name in Week.days_names}
        
    def add(self, day : Day):
        self.days[day.name] = self.days[day.name].merge(day)
    
    def get_mapping(self) -> dict[str, list[str]]:
        return {day_name: sorted([time.strftime("%H:%M") for time in day.time_schedule.keys()]) for day_name, day in self.days.items()}

    def next_time_point(self, from_datetime: Optional[datetime] = None) -> datetime:
        """
        Ищет ближайшую точку в расписании (за ближайшие 7 дней чтоб не циклиться)
        Returns:
            datetime: следующая точка времени расписания. Если не найдено - None
        """
        if from_datetime is None:
            from_datetime = datetime.now()

        next_point = None

        days_counter = 0
        while next_point is None and days_counter < 7:
            day_name = from_datetime.strftime("%A")

            next_time = self.days[day_name].next_time_point(from_datetime)
            if next_time:
                next_point = datetime(year=from_datetime.year,
                                         month=from_datetime.month,
                                         day=from_datetime.day,
                                         hour = next_time.hour,
                                         minute = next_time.minute,
                                         second = next_time.second)
            else:
                from_datetime += timedelta(days=1)
                from_datetime = datetime(year=from_datetime.year,
                                         month=from_datetime.month,
                                         day=from_datetime.day,
                                         hour=0, minute=0, second = 0)
                days_counter += 1

        return next_point


if __name__ == "__main__":
    week = Week()
    day1 = Day('Thursday')
    day2 = Day('Friday')
    day3 = Day('Monday')
    day4 = Day('Thursday')

    day1.add_time(time(7,0))
    day1.add_time(time(12,0))
    day2.add_time(time(7,0))
    day2.add_time(time(12,0))
    day3.add_time(time(7,0))
    day3.add_time(time(12,0))
    day4.add_time(time(8,0))
    day4.add_time(time(11,0))

    week.add(day1)
    week.add(day2)
    week.add(day3)

    next = week.next_time_point()

    print(next)
    
    empty_week = Week()
    
    print(empty_week.next_time_point())
    
    week1 = Week()
    week1.add(day3)
    print(week1.next_time_point())