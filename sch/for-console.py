from sch.models import *

def wipe_db():
    Employee.objects.all().delete()
    Shift.objects.all().delete()
    Department.objects.all().delete()
    Organization.objects.all().delete()
wipe_db()

def create_org_and_departments():

    ncmc = Organization.objects.create(name="NCMC", full_name="North Colorado Medical Center")

    ncmc.save()

    ncmc.time_phases.create(name="AM", full_name="Morning", max_time=dt.time(9, 30), position=0).save()
    ncmc.time_phases.create(name="MD", full_name="Midday", max_time=dt.time(12, 0), position=1).save()
    ncmc.time_phases.create(name="PM", full_name="Afternoon", max_time=dt.time(14, 0), position=2).save()
    ncmc.time_phases.create(name="EV", full_name="Evening", max_time=dt.time(19, 0), position=3).save()
    ncmc.time_phases.create(name="XN", full_name="Overnight", max_time=dt.time(23, 59), position=4).save()

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

    cpht.save()
    rph.save()

    print(f'ORG: {ncmc}')
    print(f'DEPARTMENTS: {cpht}, {rph}')
    print("_"*80)

    return
create_org_and_departments()

def create_shifts():

    cpht = Department.objects.get(name="CPhT")

    mi = Shift.objects.create(name="MI", start_time=dt.time(6, 30), hours=10, department=cpht)
    mi.save()
    _7c = Shift.objects.create(name="7C", start_time=dt.time(7, 00), hours=8, department=cpht)
    _7c.save()
    _7p = Shift.objects.create(name="7P", start_time=dt.time(7, 00), hours=8, department=cpht)
    _7p.save()
    s = Shift.objects.create(name="S", start_time=dt.time(8, 00), hours=10, department=cpht, on_holidays=False,
                             weekdays='MTWRF')
    s.save()
    op = Shift.objects.create(name="OP", start_time=dt.time(7, 40), hours=8, department=cpht, on_holidays=False,
                              weekdays='MTWRF')
    op.save()
    ei = Shift.objects.create(name="EI", start_time=dt.time(12, 30), hours=10, department=cpht)
    ei.save()
    ep = Shift.objects.create(name="EP", start_time=dt.time(12, 30), hours=10, department=cpht)
    ep.save()
    _3 = Shift.objects.create(name="3", start_time=dt.time(15, 00), hours=10, department=cpht)
    _3.save()
    n = Shift.objects.create(name="N", start_time=dt.time(20, 30), hours=10, department=cpht)
    n.save()

    print(f'SHIFTS: {", ".join([str(s) for s in [mi, _7c, _7p, s, op, ei, ep, _3, n]])}')
    shifts = [mi, _7c, _7p, s, op, ei, ep, _3, n]

    print('PHASES:')
    for shift in shifts:
        print(f'{shift}: {shift.phase}, {shift.start_time.strftime("%H:%M")}')

    return
create_shifts()

def create_employees():
    cpht        = Department.objects.get(name="CPhT")
    cpht_shifts = Shift.objects.filter(department=cpht)

    josh = Employee.objects.create(
        first_name="Josh",
        last_name="Steinbecker",
        department=cpht,
        fte=0.625,
        trade_one_offs=True,
        phase_pref=TimePhase.objects.get(name='AM'))
    josh.shifts_trained.add(*cpht_shifts)
    josh.save()

    brittanie = Employee.objects.create(
        first_name="Brittanie",
        last_name="Spahn",
        department=cpht,
        fte=1,
        trade_one_offs=False,
        phase_pref=TimePhase.objects.get(name='AM'))
    brittanie.shifts_trained.add(Shift.objects.get(name='OP'))
    brittanie.save()

    sabrina = Employee.objects.create(
        first_name="Sabrina",
        last_name="Berg",
        department=cpht,
        fte=1,
        trade_one_offs=False,
        phase_pref=TimePhase.objects.get(name='AM'))
    sabrina.shifts_trained.add(*cpht_shifts.exclude(name='OP'))

    return Employee.objects.filter(department=cpht)
create_employees()


