from sch.models import *


def create_ncmc_env():
        ncmc = Organization.objects.create(name="NCMC",slug='ncmc')

        # TimePhases
        am = ('AM', 'Morning', ncmc, "09:45")
        md = ('MD', 'Midday', ncmc, "11:30")
        pm = ('PM', 'Afternoon', ncmc, "14:30")
        ev = ('EV', 'Evening', ncmc, "19:00")
        xn = ('XN', 'Night', ncmc, "23:59")
        phases = [am, md, pm, ev, xn]
        for phase in phases:
            TimePhase.objects.create(name=phase[0],full_name=phase[1],organization=phase[2], max_time=phase[3])

        # Departments
        cpht = Department.objects.create(
                name="CPHT", organization=ncmc, full_name="Technicians",
                schedule_week_count=6, initial_start_date="2022-12-25")
        rph = Department.objects.create(
                name="RPH", organization=ncmc, full_name="Pharmacists",
                schedule_week_count=4, initial_start_date="2021-01-01")

        # Shifts
        # Tech Shifts
        D7 = "S,M,T,W,R,F,A"

        cpht_mi = ("MI", "06:30", 8,  D7)
        cpht_7c = ("7C", "07:00", 10, D7)
        cpht_7p = ("7P", "07:00", 10, D7)
        cpht_s =  ("S",  "08:00", 10, "M,T,W,R,F")
        cpht_op = ("OP", "7:45",  8,  "M,T,W,R,F")
        cpht_n =  ("N",  "20:30", 10, D7)
        shifts = [cpht_mi, cpht_7c, cpht_7p, cpht_s, cpht_op, cpht_n]
        for shift in shifts:
                s = cpht.shifts.create(name=shift[0], start_time=shift[1], hours=shift[2], weekdays=shift[3])
                s.save()


        # Pharmacist Shifts
        rph_i = rph.shifts.create(name="I", start_time="06:30", hours=10)
        rph_pc = rph.shifts.create(name="PC", start_time="07:00", hours=10, weekdays="M,T,W,R,F")
        rph_s = rph.shifts.create(name="S", start_time="07:00", hours=10)
        rph_m = rph.shifts.create(name="M", start_time="07:00", hours=10)
        rph_c = rph.shifts.create(name="C", start_time="10:00", hours=10)

        josh = Employee.objects.create(name="Josh Steinbecker", department=cpht, fte=0.625)
        josh.shifts_trained.set(Shift.objects.filter(department=cpht))
        josh.save()

        brittanie = Employee.objects.create(name="Brittanie Spahn", department=cpht, fte=0.625)
        brittanie.shifts_trained.add(Shift.objects.get(name="OP"))
        brittanie.save()


