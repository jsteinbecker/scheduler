from django.db.models import F
from django.test import TestCase
from .models import Employee
import datetime as dt
from org.models import Organization, Department, Shift, TimePhase


# Create your tests here.
class NCMCTestCase(TestCase):
    def setUp(self):
        def test_create_org_and_departments():

            ncmc = Organization.objects.create(name="NCMC", full_name="North Colorado Medical Center")

            ncmc.time_phases.create(name="AM", full_name="Morning", max_time=dt.time(9,30), position=0)
            ncmc.time_phases.create(name="MD", full_name="Midday", max_time=dt.time(12,0), position=1)
            ncmc.time_phases.create(name="PM", full_name="Afternoon", max_time=dt.time(14,0), position=2)
            ncmc.time_phases.create(name="EV", full_name="Evening", max_time=dt.time(19,0), position=3)
            ncmc.time_phases.create(name="XN", full_name="Overnight", max_time=dt.time(23,59), position=4)

            cpht = Department.objects.create(
                name="CPhT",
                full_name="Pharmacy Technicians",
                organization=ncmc,
                schedule_week_count=6,
                initial_start_date="2022-12-25"
                )

            rph = Department.objects.create(
                name="RPh",
                full_name="Pharmacists",
                organization=ncmc,
                schedule_week_count=6,
                initial_start_date="2022-12-25"
                )

            return ncmc, cpht, rph

        ncmc, cpht, rph = test_create_org_and_departments()

        def test_create_shifts():

            mi = Shift.objects.create(name="MI", start_time=dt.time(6,30), hours=10, department=cpht)
            _7c = Shift.objects.create(name="7C", start_time=dt.time(7,00), hours=8, department=cpht)
            _7p = Shift.objects.create(name="7P", start_time=dt.time(7,00), hours=8, department=cpht)
            s = Shift.objects.create(name="S", start_time=dt.time(8,00), hours=10, department=cpht, on_holidays=False, weekdays='MTWRF')
            op = Shift.objects.create(name="OP", start_time=dt.time(7,40), hours=8, department=cpht, on_holidays=False,weekdays='MTWRF')
            ei = Shift.objects.create(name="EI", start_time=dt.time(12,30), hours=10, department=cpht)
            ep = Shift.objects.create(name="EP", start_time=dt.time(12,30), hours=10, department=cpht)
            _3 = Shift.objects.create(name="3", start_time=dt.time(15,00), hours=10, department=cpht)
            n = Shift.objects.create(name="N", start_time=dt.time(20,30), hours=10, department=cpht)

            i_rph = Shift.objects.create(name="I", start_time=dt.time(6,30), hours=10, department=rph)
            pc_rph = Shift.objects.create(name="PC", start_time=dt.time(7,00), hours=10, department=rph, on_holidays=False, weekdays='MTWRF')
            s_rph = Shift.objects.create(name="S", start_time=dt.time(7,00), hours=10, department=rph,)
            m_rph = Shift.objects.create(name="M", start_time=dt.time(7,00), hours=10, department=rph)
            moc_rph = Shift.objects.create(name="MO", start_time=dt.time(7,45), hours=8, department=rph, on_holidays=False, weekdays='MTWRF')
            c_rph = Shift.objects.create(name="C", start_time=dt.time(10,00), hours=10, department=rph)
            e_rph = Shift.objects.create(name="E", start_time=dt.time(12,30), hours=10, department=rph, on_holidays=False, weekdays='MTWRF')
            _3_rph = Shift.objects.create(name="3", start_time=dt.time(15,00), hours=10, department=rph)
            n_rph = Shift.objects.create(name="N", start_time=dt.time(20,30), hours=10, department=rph)

            return Shift.objects.filter(department=cpht)

        cpht_shifts = test_create_shifts()

        def test_create_employees():
            josh = Employee.objects.create(first_name="Josh", last_name="Steinbecker", department=cpht, fte=0.625,
                                            trade_one_offs=True, phase_pref=TimePhase.objects.get(name='AM'))
            josh.shifts_trained.add(*cpht_shifts)
            josh.save()

            brittanie = Employee.objects.create( first_name="Brittanie", last_name="Spahn", department=cpht, fte=1,
                                                 trade_one_offs=False, phase_pref=TimePhase.objects.get(name='AM'))
            brittanie.shifts_trained.add(Shift.objects.get(name='OP'))
            brittanie.save()

            sabrina = Employee.objects.create( first_name="Sabrina", last_name="Berg", department=cpht, fte=1,
                                               trade_one_offs=False, phase_pref=TimePhase.objects.get(name='AM'))
            sabrina.shifts_trained.add(*cpht_shifts.exclude(name='OP'))
            sabrina.save()

            brianna = Employee.objects.create( first_name="Brianna", last_name="Annan", department=cpht, fte=1,
                                               trade_one_offs=True, phase_pref=TimePhase.objects.get(name='AM'))
            brianna.shifts_trained.add(*cpht_shifts.exclude(name='OP'))
            brianna.save()

            esperanza = Employee.objects.create( first_name="Esperanza", last_name="Gonzalez", department=cpht, fte=1,
                                                 trade_one_offs=True, phase_pref=TimePhase.objects.get(name='AM'))
            esperanza.shifts_trained.add(*cpht_shifts.exclude(name='OP'))
            esperanza.save()

            return Employee.objects.filter(department=cpht)

        cpht_empls = test_create_employees()

        assert cpht_empls.count() == 5
        assert cpht_empls[0].shifts_trained.count() == 9
        assert cpht_empls[1].shifts_trained.count() == 1

    def test_time_phases(self):
        cpht = Department.objects.get(name="CPhT")
        rph = Department.objects.get(name="RPh")

        t_phases = TimePhase.objects.all()
        assert(t_phases[0].shifts.filter(department=cpht).count() == 5)

        return t_phases

    def test_weekend_shift_distribution(self):
        s = Shift.objects.get(name='S', department__name='CPhT')
        print()
        print("=="*45)
        print("TEST // WEEKEND SHIFT DISTRIBUTION")
        print(f'SHIFT: {s} / WEEKDAYS: {s.weekdays}')


        sat_shifts = Shift.objects.filter(weekdays__contains='A')
        print(f'Shifts on SATURDAY: {sat_shifts.values_list("name", flat=True)}')
        no_sat_shifts = Shift.objects.exclude(weekdays__contains='A')

        sat_shifts_cpht, sat_shits_rph = sat_shifts.filter(department__name='CPhT'), sat_shifts.filter(department__name='RPh')
        assert len(sat_shifts_cpht) == 7
        assert len(sat_shits_rph) == 6
        assert sat_shifts.get(name='S').department.name == 'RPh'
        print(f'Shifts on SATURDAY for CPhT: {sat_shifts_cpht.values_list("name", flat=True)}')
        print(f'Shifts on SATURDAY for RPh: {sat_shits_rph.values_list("name", flat=True)}')

        print(f'Shifts NOT on SATURDAY: {no_sat_shifts.values_list("name", flat=True)}')
        assert len(no_sat_shifts) == 5
        print(f'Number of shifts on SATURDAY: {len(sat_shifts)}', ' **CALCULATED CORRECTLY')

