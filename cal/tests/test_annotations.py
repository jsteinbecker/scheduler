import random

from django.test import TestCase

from sch.models import *


class TestWeekAggregationAnnotation(TestCase):

    def setUp(self):
        from sch.data import create_ncmc_env

        create_ncmc_env()

        dept = Department.objects.get(name__iexact='CPhT')

        print(f"DEPARTMENT: \t {dept.name}")
        print(">>> build_schedule")

        sch = dept.schedules.create(start_date='2022-12-25')
        sch.save()

        print(f"SCHEDULE: \t {sch.slug}")
        print(f"\tVERSIONS: \t {sch.versions.count()}\n")



    def test_week_aggregation(self):
        sch = Schedule.objects.first()
        ver = sch.versions.first()  # type: Version

        assert ver.schedule == sch
        assert ver.workdays.count() == 42
        assert ver.slots.count() == 228

        print(f"CHECKING VERSION FOR CORRECT WORKDAY_COUNT, SLOT_COUNT:")
        print(f"\t WORKDAYS: {ver.workdays.count()}")
        print(f"\t SLOTS:    {ver.slots.count()}\n")

        # Get FirstWeekMonitor for FirstEmployee of FirstVersion
        empl = ver.schedule.employees.first()  # type: Employee
        wk_mtr = empl.week_monitors.filter(version=ver).first()  # type: EmployeeWeekMonitor

        print(f"WEEK_MONITOR: <{wk_mtr}>")
        print(f"\t hours: {wk_mtr.hours}")
        print(f"\t goal:  {wk_mtr.goal}")
        print(f"\t state: {wk_mtr.get_state_display()}")

        wk_id = wk_mtr.wk_id
        potential_slots = ver.slots.filter(workday__wk_id=wk_id, shift__in=empl.shifts_trained.all(),
                                           employee__isnull=True)
        print(f"\t POTENTIAL SLOTS: {potential_slots.count()}")
        print(" ".join(
            [f"{s.shift.name}({'Su Mo Tu We Th Fr Sa'.split(' ')[s.workday.weekday]})" for s in potential_slots]))

        # Assign Slots to Employee
        s1 = potential_slots[random.randint(0, potential_slots.count() - 1)]
        s1.set_employee(empl)  # type: Slot

        s2 = potential_slots[random.randint(0, potential_slots.count() - 1)]
        s2.set_employee(empl)  # type: Slot

        print(f"\nASSIGNED SLOTS: {empl.slots.count()}")
        print(s1, s1.employee)
        print(s2, s2.employee)
