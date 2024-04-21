from taxi_stats.time_schedule import *
import pytest
import json


def test_day_add_methods():
    monday_1 = Day("Monday")
    monday_1.add_time(time(12, 0))
    monday_1.add_time(time(12, 30))
    assert len(monday_1.time_schedule) == 2
    monday_2 = Day("Monday")
    monday_2.add_to_schedule(123, [time(12, 0), time(13, 20), time(12, 30)])
    assert len(monday_2.time_schedule) == 3
    monday_2.add_to_schedule(234, [time(12, 0), time(14, 20), time(12, 30)])
    assert len(monday_2.time_schedule) == 4
    assert monday_2.time_schedule[time(12, 0)].count(123) == 1
    assert monday_2.time_schedule[time(12, 0)].count(234) == 1

    assert monday_2.time_schedule[time(13, 20)].count(123) == 1
    assert monday_2.time_schedule[time(13, 20)].count(234) == 0

    assert monday_2.time_schedule[time(14, 20)].count(123) == 0
    assert monday_2.time_schedule[time(13, 20)].count(123) == 1
    assert monday_2.time_schedule[time(13, 20)].count(234) == 0


def test_day_remove_methods():
    monday_1 = Day("Monday")
    monday_1.add_time(time(12, 0))
    monday_1.add_time(time(12, 30))
    monday_2 = Day("Monday")
    monday_2.add_to_schedule(123, [time(12, 0), time(13, 20), time(12, 30)])
    monday_2.add_to_schedule(234, [time(12, 0), time(14, 20), time(12, 30)])

    assert len(monday_2.time_schedule[time(12, 0)]) == 2
    monday_1.remove_from_schedule(
        id=123, times=[time(12, 0), time(13, 0), time(13, 20)]
    )
    assert not time(12, 0) in monday_1.time_schedule
    monday_2.remove_from_schedule(
        id=123, times=[time(12, 0), time(13, 0), time(13, 20)]
    )
    assert len(monday_2.time_schedule[time(12, 0)]) == 1
    assert not time(13, 20) in monday_2.time_schedule
    monday_2.remove_from_schedule(id=234, times=[time(12, 0)])
    assert not time(12, 0) in monday_2.time_schedule


def test_day_collision():
    monday_1 = Day("Monday")
    monday_1.add_to_schedule(234, [time(12, 0), time(13, 20), time(12, 30)])
    monday_2 = Day("Monday")
    monday_2.add_to_schedule(123, [time(12, 0), time(13, 20), time(12, 30)])
    monday_3 = Day("Monday")
    monday_3.add_to_schedule(123, [time(12, 0), time(14, 20), time(15, 30)])

    monday_1_copy1 = Day("Monday").merge(monday_1)
    monday_1_copy2 = monday_1.merge(Day("Monday"))
    assert monday_1_copy1 == monday_1
    assert monday_1_copy2 == monday_1

    monday_2_copy1 = Day("Monday").merge(monday_2)
    monday_2_copy2 = monday_2.merge(Day("Monday"))
    assert monday_2_copy1 == monday_2
    assert monday_2_copy2 == monday_2

    merged_day = monday_1.merge(monday_2)
    assert len(merged_day.time_schedule) == 3
    for _, ids in merged_day.time_schedule.items():
        assert len(ids) == 2
        assert 123 in ids
        assert 234 in ids

    merged_day = monday_1.merge(monday_3)
    assert len(merged_day.time_schedule) == 5
    assert len(merged_day.time_schedule[time(12, 0)]) == 2
    assert len(merged_day.time_schedule[time(13, 20)]) == 1
    assert 234 in merged_day.time_schedule[time(13, 20)]
    assert 123 in merged_day.time_schedule[time(12, 0)]
    assert 234 in merged_day.time_schedule[time(12, 0)]


def test_day_time_search():
    monday = Day("Monday")
    monday.add_to_schedule(234, [time(7, 0), time(12, 0), time(17, 30)])
    monday.add_to_schedule(123, [time(7, 0), time(12, 10), time(17, 30)])

    t, ids = monday.next_time_point(datetime(year=2024, month=4, day=15, hour=0))
    assert t == time(7, 0)
    assert len(ids) == 2

    t, ids = monday.next_time_point(
        datetime(year=2024, month=4, day=15, hour=7, minute=0)
    )
    assert t == time(12, 0)
    assert len(ids) == 1

    t, ids = monday.next_time_point(
        datetime(year=2024, month=4, day=15, hour=11, minute=50)
    )
    assert t == time(12, 0)
    assert len(ids) == 1

    t, ids = monday.next_time_point(
        datetime(year=2024, month=4, day=15, hour=17, minute=50)
    )
    assert t is None
    assert len(ids) == 0


def test_week_add():
    week = Week()
    sunday = Day(Week.days_names[0])
    sunday.add_to_schedule(123, [time(7, 0), time(12, 10), time(17, 30)])

    monday = Day(Week.days_names[1])
    monday.add_to_schedule(234, [time(7, 0), time(12, 0), time(17, 30)])

    assert len(week.days) == 0
    week.add(sunday)
    assert len(week.days) == 1
    week.add(monday)
    assert len(week.days) == 2

    monday_1 = Day(Week.days_names[1])
    monday_1.add_to_schedule(123, [time(7, 0), time(12, 0), time(17, 30), time(23, 30)])
    week.add(monday_1)
    assert len(week.days) == 2

    assert len(week.days[Week.days_names[1]].time_schedule) == 4
    assert 123 in week.days[Week.days_names[1]].time_schedule[time(7, 0)]
    assert 234 in week.days[Week.days_names[1]].time_schedule[time(7, 0)]


def test_week_serialization():
    week = Week()
    sunday = Day(Week.days_names[0])
    sunday.add_to_schedule(123, [time(7, 0), time(12, 10), time(11, 30)])

    monday = Day(Week.days_names[1])
    monday.add_to_schedule(234, [time(7, 0), time(12, 0), time(17, 30)])

    week.add(sunday)
    week.add(monday)

    mapping = week.get_mapping()

    comp_tmpl = json.dumps(
        {
            "Sunday": ["07:00", "11:30", "12:10"],
            "Monday": ["07:00", "12:00", "17:30"],
        }
    )
    comp_js = json.dumps(mapping)

    assert str(comp_js) == str(comp_tmpl)

    other_week = Week.from_json(mapping)
    # other_week нельзя сравнить с week, т.к. week содержит id,
    # которые не сериализуются в get_mapping
    mapping = other_week.get_mapping()
    comp_js = json.dumps(mapping)

    assert other_week == Week.from_json(mapping)


def test_week_time_search():
    week = Week()
    sunday = Day(Week.days_names[0])
    sunday.add_to_schedule(123, [time(6, 0), time(12, 10), time(11, 30)])
    week.add(sunday)

    monday = Day(Week.days_names[1])
    monday.add_to_schedule(234, [time(7, 0), time(12, 0), time(17, 30)])
    week.add(monday)

    # вторник
    t, ids = week.next_time_point(
        datetime(year=2024, month=4, day=16, hour=11, minute=50)
    )
    assert t == datetime(year=2024, month=4, day=21, hour=6, minute=0)
    assert len(ids) == 1
    # Пн
    t, ids = week.next_time_point(
        datetime(year=2024, month=4, day=15, hour=8, minute=0)
    )
    assert t == datetime(year=2024, month=4, day=15, hour=12, minute=0)
    assert len(ids) == 1

    # Вс - Пн
    t, ids = week.next_time_point(
        datetime(year=2024, month=4, day=14, hour=17, minute=50)
    )
    assert t == datetime(year=2024, month=4, day=15, hour=7, minute=0)
    assert len(ids) == 1

    week = Week()
    # Пусто
    t, ids = week.next_time_point(
        datetime(year=2024, month=4, day=14, hour=17, minute=50)
    )
    assert t == None
    assert len(ids) == 0
    # В течении недели нет новых эвентов
    week.add(sunday)
    t, ids = week.next_time_point(
        datetime(year=2024, month=4, day=14, hour=17, minute=50)
    )
    assert t == None
    assert len(ids) == 0


if __name__ == "__main__":
    test_day_add_methods()
    test_day_remove_methods()
    test_day_collision()
    test_day_time_search()
    test_week_add()
    test_week_serialization()
    test_week_time_search()
