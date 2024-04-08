
class Day:
    """
    dict[time, list[id]]
    """
    def __init__(self, name) -> None:
        self.name = name
        self.time_schedule: dict[str, list[int]] = {}

    def merge(self, other_day: 'Day') -> 'Day':
        merged_day = Day(self.name)
        
        for time, ids in self.time_schedule.items():
            merged_day.time_schedule.setdefault(time, []).extend(ids)
        for time, ids in other_day.time_schedule.items():
            merged_day.time_schedule.setdefault(time, []).extend(ids)

        return merged_day

class Week:
    """
    Пример расписания
        {
            "Monday": ["09:00", "12:00", "15:00"],
            "Tuesday": ["10:00", "13:00", "16:00"]
        }
    """
    days_names = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
    def __init__(self) -> None:
        self.days : dict[str, Day] = {}
        
    def add(self, day : Day):
        if day.name in self.days:
            self.days[day.name] = self.days[day.name].merge(day)
        else:
            self.days[day.name] = day
    
    def get_mapping(self) -> dict[str, list[str]]:
        return {day_name: [time for time in day.time_schedule.keys()] for day_name, day in self.days.items()}
