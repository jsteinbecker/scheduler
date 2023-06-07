import datetime
import random

from django.test import TestCase

from cal.models import FillsWith
from sch.models import Department, Schedule, Shift, Employee, Version, Workday, Slot
from empl.tests import NCMCTestCase


# Create your tests here.

class TestScheduleBuilds(NCMCTestCase):

    def setUp(self):
        super().setUp()
        dept = Department.objects.get(name='CPhT')
        sd = dept.get_next_start_date()
        sch = dept.schedules.create(start_date=sd)
        sch.save()

        print("==" * 45)
        print("* * * SCHEDULE BUILD TEST * * *")
        print("- " * 45)
        print(f"""{sch.slug} ~~~
        YEAR:   {sch.start_date.year} 
        NUMBER: {sch.num}, 
        STARTS: {sch.start_date}, ENDS: {sch.start_date + datetime.timedelta(days=sch.day_count - 1)}
        """)

        assert sch.versions.count() == 1
        assert sch.versions.first().schedule == sch
        assert sch.employees.count() == Employee.objects.filter(department=dept).count()
        assert sch.versions.first().workdays.count() == sch.day_count
        print("N WORKDAYS", sch.versions.first().workdays.count())
        assert sch.versions.first().slots.count() == 354
        print("N SLOTS", sch.versions.first().slots.count())
        assert sch.versions.first().workdays.last().date == sch.start_date + datetime.timedelta(days=sch.day_count - 1)
        print("LAST DATE IS CORRECT :", sch.versions.first().workdays.last().date)
        print("- " * 45)

    def test_auto_turnaround_prevention(self):
        dept = Department.objects.get(name='CPhT')
        sch = dept.schedules.create(start_date=dept.get_next_start_date())
        sch.save()
        # ASSIGN EMPLOYEE TO SPECIFIC SLOT
        slot = sch.versions.first().slots.get(workday__sd_id=3, shift__name='MI')
        emp = Employee.objects.get(first_name='Josh')
        slot.set_employee(emp)
        # VERIFY ASSIGNMENT
        assert slot.employee == emp
        # VERIFY RESTRICTION OF FILLS_WITH OBJS ON SAME DAY
        fw_same_day = FillsWith.objects.filter(slot__workday=slot.workday, employee=emp)
        print('Same Day Count:', fw_same_day.count())
        print('On Same Day:', fw_same_day.values_list('state', flat=True))
        print(slot.workday, slot.workday.sd_id, slot.shift, slot.employee)
        print('_' * 45)

    def test_week_monitor_construction(self):

        dept = Department.objects.get(name='CPhT')
        sch = dept.schedules.create(start_date=dept.get_next_start_date())
        sch.save()
        ver = sch.versions.first() # type: Version
        print("version slot count: ",ver.slots.count())
        # ASSIGN EMPLOYEE TO SPECIFIC SLOT

        emp = Employee.objects.get(first_name='Josh')
        ppms = ver.pay_period_monitors.filter(employee=emp)
        for ppm in ppms:
            print(f"PPM: {ppm} ({ppm.prd_id}) // {ppm.week_monitors.count()} child-WMs")
            assert ppm.week_monitors.count() == 2

            for wm in ppm.week_monitors.all():
                print(f"\t WM: {wm} ({wm.wk_id}) // {wm.slots.count()} slots // {wm.hours}hrs. // {wm.state}")
        ppm = ppms.first()
        while ppm.state == 'S':
            slot = ver.slots.all()[random.randint(0, ver.slots.count() - 1)] # type: Slot
            if slot.check_employee(emp):
                slot.set_employee(emp)
                print("ASSIGNED:", slot, slot.employee)
                ppm = slot.prd_monitors.first()
                ppm.save()
                print(f"   (contained in PPM{ppm.prd_id}", ppm.prd_id, ")")
                print(f"   PPM Status: {ppm.hours}hrs, {ppm.get_state_display()}")
        print("**********")
        print(f"WM: {ppm.week_monitors.first().hours}hrs, {ppm.week_monitors.first().state}")
        print("**********")






