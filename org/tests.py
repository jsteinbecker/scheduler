from django.test import TestCase
from .models import Organization, Department, Shift
# Create your tests here.

class BaseTest(TestCase):
    def setUp(self):

        org = Organization.objects.create(name="NCMC",slug='ncmc')

        dept1 = Department.objects.create(
                name="Dept1", organization=org,
                schedule_week_count=6, initial_start_date="2022-12-25")
        dept2 = Department.objects.create(
                name="Dept2", organization=org,
                schedule_week_count=4, initial_start_date="2021-01-01")

        sftA = dept1.shifts.create(name="MI", start_time="08:00", hours=8,weekdays="M,T,W,R,F")
        sftB = dept1.shifts.create(name="AI", start_time="16:00", hours=10)
        sftC = dept1.shifts.create(name="N", start_time="00:00", hours=10)

        print([sft.slug for sft in [sftA,sftB,sftC]])

        return super().setUp()

    def test_start_dates(self):

        depts = Department.objects.all()

        for dept in depts:
            print("="*75)
            print(dept.name, f"(uses {dept.schedule_week_count}-week schedules)")
            dates=list(dept.start_dates_from_year(2023))

            print("Sch. Start dates in 2023: ", [d.strftime('%m.%d') for d in dates])
            print("Start Dates:", len(dates))

        assert depts.count() == 2

    def test_shifts(self):

        shifts = Shift.objects.all()
        print(shifts.values_list('name', 'department__name'))

        assert shifts.count() == 3
        print (shifts.filter(weekdays__contains="S").values('name'))
        assert shifts.filter(weekdays__contains="S").count() == 2

        shifts_on_wed = shifts.filter(weekdays__contains='W')
        assert shifts_on_wed.count() == 3
        print("SHIFTS ON WEDNESDAY: ", list(shifts_on_wed.values_list('name',flat=True)))


