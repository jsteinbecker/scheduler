from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.decorators.csrf import csrf_exempt

from empl.models import PtoRequest, DayTemplate
from .models import Schedule, Workday, FillsWith, Slot, Version
from org.models import Department, Shift
from django.contrib import messages
from django.db.models import Sum, F, Q, Count, Value, Subquery, OuterRef, Case, When, CharField, Exists
import datetime as dt
from django.http import HttpResponse, HttpResponseRedirect


# Create your views here.

class SchViews:

    @staticmethod
    def sch_list_view(request, org_id, dept_id):
        schedules = Schedule.objects.filter(department__slug=dept_id)
        return render(request, 'sch/sch-list.pug', {
            'schedules': schedules,
        })

    @staticmethod
    def sch_detail_view(request, org_id, dept_id, sch_id):
        schedule = Schedule.objects.get(slug=sch_id, department__slug=dept_id)
        return render(request, 'sch/sch-detail.pug', {
            'schedule': schedule,
            'versions': schedule.versions.all(),
            'employees': schedule.employees.annotate(
                n_pto_reqs=Subquery(schedule.pto_requests.filter(employee=OuterRef('pk')).values('pk'))),
        })

    class Data:

        @staticmethod
        def sch_empl_pto_count(request, org_id, dept_id, sch_id, emp_id):
            schedule = Schedule.objects.get(slug=sch_id, department__slug=dept_id)
            employee = schedule.employees.get(slug=emp_id)
            return HttpResponse(schedule.pto_requests.filter(employee=employee).count())

    @staticmethod
    def new_schedule_view(request, org_id, dept_id):
        """NEW SCHEDULE VIEW
        =====================
        This view is called when a user clicks the "New Schedule" button on the department page.
        """
        dept = Department.objects.get(slug=dept_id)  # type: Department
        start_date = dept.get_next_start_date()
        sch = Schedule.objects.create(
            department=dept,
            start_date=start_date,
            num=Schedule.objects.filter(department=dept, year=start_date.year).count() + 1,
            year=start_date.year,
        )
        return HttpResponseRedirect(sch.url())

    @staticmethod
    def del_schedule(request, org_id, dept_id, sch_id):
        schedule = Schedule.objects.get(slug=sch_id, department__slug=dept_id)
        schedule.delete()
        return HttpResponseRedirect(Department.objects.get(slug=dept_id).url)

    @staticmethod
    def empl_pto_view(request, org_id, dept_id, sch_id, emp_id):
        schedule = Schedule.objects.get(slug=sch_id, department__slug=dept_id)
        emp = schedule.employees.get(slug=emp_id)
        tdos = DayTemplate.objects.filter(
            employee=emp,
            collection__employee__active=True
        )

        return render(request, 'sch/empl-pto.pug', {
            'schedule': schedule,
            'employee': emp,
            'month': schedule.start_date.strftime('%B'),
            'schedule_days': schedule.versions.first().workdays.all(),
            'tdo_days': tdos if tdos.exists() else None,

        })

    @csrf_exempt
    def empl_pto_view_day_partial(request, org_id, dept_id, sch_id, emp_id, day):
        schedule = Schedule.objects.get(slug=sch_id, department__slug=dept_id)
        emp = schedule.employees.get(slug=emp_id)
        date_slug = day.split('-')
        date = dt.date(int(date_slug[0]), int(date_slug[1]), int(date_slug[2]))

        if request.method == 'POST':
            if emp.pto_requests.filter(date=date).exists():
                pass
            else:
                emp.pto_requests.create(date=date)
        if request.method == 'DELETE':
            if emp.pto_requests.filter(date=date).exists():
                emp.pto_requests.filter(date=date).delete()
            else:
                pass

        HTML_CLS = "text-center cursor-pointer pt-1 rounded-full h-9 w-9 hover:bg-blue-200 hover:bg-opacity-25"

        if emp.pto_requests.filter(date=date).exists():
            HTMX_DEL = f"hx-delete='{day}/' hx-swap='outerHTML'"
            return HttpResponse(
                f"<div class='{HTML_CLS} bg-blue-500 border-white text-white' {HTMX_DEL}>{date.day}</div>")

        else:
            HTMX_ADD = f"hx-post='{day}/' hx-swap='outerHTML'"
            return HttpResponse(
                f"<div class='border border-blue-500 text-blue-500 {HTML_CLS}' {HTMX_ADD}>{date.day}</div>")

    @staticmethod
    def define_prn_employee_requested_hours(request, org_id, dept_id, sch_id):
        schedule = Schedule.objects.get(slug=sch_id, department__slug=dept_id)
        employees = schedule.employees.prn()

        return render(request, 'sch/prn-empl.pug', {
            'schedule': schedule,
            'employees': employees,
            'week_count': range(schedule.versions.first().workdays.count() // 7)
        })


class VerViews:

    @staticmethod
    def ver_detail_view(request, org_id, dept_id, sch_id, ver_id):
        schedule = Schedule.objects.get(slug=sch_id, department__slug=dept_id)
        version = schedule.versions.get(num=ver_id)
        version.save()

        return render(request, 'ver/ver-detail.pug', {
            'schedule': schedule,
            'version': version,
            'percent': int(version.percent * 100),
            'workdays': version.workdays.all(),
            'all_shifts': schedule.shifts.all(),
            'n_pto_ct': version.slots.filter(state=Slot.SlotStates.PTO_CONFLICT).count() or 0,
            'n_tdo_ct': version.slots.filter(state=Slot.SlotStates.TDO_CONFLICT).count() or 0,
            'prd_id_list': list(set(version.workdays.values_list('prd_id', flat=True))),
            'wk_id_list': list(set(version.workdays.values_list('wk_id', flat=True))),

        })

    def new_version_view(request, org_id, dept_id, sch_id):
        schedule = Schedule.objects.get(slug=sch_id, department__slug=dept_id)
        schedule.versions.create(num=schedule.versions.count() + 1, status=Version.StatusChoices.DRAFT)
        return HttpResponseRedirect(schedule.versions.last().url())

    @staticmethod
    def ver_assign_templates(request, org_id, dept_id, sch_id, ver_id):
        schedule = Schedule.objects.get(slug=sch_id, department__slug=dept_id)
        version = schedule.versions.get(num=ver_id)
        n, ver = version.actions.set_templates(version)

        messages.success(request, f'{n} D-Directed Templates assigned.')
        return HttpResponseRedirect(version.url())

    @staticmethod
    def ver_assign_generic_templates(request, org_id, dept_id, sch_id, ver_id):
        schedule = Schedule.objects.get(slug=sch_id, department__slug=dept_id)
        version = schedule.versions.get(num=ver_id)
        n, ver = version.actions.slot_in_generic_templates(version)

        messages.success(request, f'{n} G-Directed Templates assigned.')
        return HttpResponseRedirect(version.url())

    @staticmethod
    def ver_clear_all(request, org_id, dept_id, sch_id, ver_id):
        schedule = Schedule.objects.get(slug=sch_id, department__slug=dept_id)
        version = schedule.versions.get(num=ver_id)
        version.slots.all().update(employee=None)
        version.pay_period_monitors.all().update(hours=0, state='S')
        return HttpResponseRedirect(version.url())

    @staticmethod
    def del_version(request, org_id, dept_id, sch_id, ver_id):
        schedule = Schedule.objects.get(slug=sch_id, department__slug=dept_id)
        version = schedule.versions.get(num=ver_id)
        version.delete()
        if schedule.versions.count() == 0:
            schedule.versions.create(num=1, status=Version.StatusChoices.DRAFT)
        return HttpResponseRedirect(schedule.url())

    @staticmethod
    def ver_clear_one_offs_and_retry(request, org_id, dept_id, sch_id, ver_id):
        schedule = Schedule.objects.get(slug=sch_id, department__slug=dept_id)
        version = schedule.versions.get(num=ver_id)
        version.slots.filter(is_one_off=True).update(employee=None)

        return HttpResponseRedirect(reverse_lazy('org:cal:ver-solve', args=[org_id, dept_id, sch_id, ver_id]))

    @staticmethod
    def ver_solve(request, org_id, dept_id, sch_id, ver_id):
        schedule = Schedule.objects.get(slug=sch_id, department__slug=dept_id)
        version = Version.objects.get(schedule=schedule, num=ver_id)

        if request.method == 'POST':
            iterations = int(request.POST.get('iterations'))
            user = request.user
            version.actions.solve(version, user=user, iterations=iterations)
            messages.success(request, f'Schedule solved.')
            return HttpResponseRedirect(version.url())

        return HttpResponse('NO ACTION')

    @staticmethod
    def ver_fix_pto(request, org_id, dept_id, sch_id, ver_id):
        schedule = Schedule.objects.get(slug=sch_id, department__slug=dept_id)
        version = schedule.versions.get(num=ver_id)

        n = 0
        for slot in version.slots.filter(state=Slot.SlotStates.PTO_CONFLICT):
            slot.employee = None
            n += 1
            slot.save()

        version.save()
        messages.success(request, f'{n} Shifts assigned.')
        return HttpResponseRedirect(version.url())

    @staticmethod
    def ver_unfavorables(request, org_id, dept_id, sch_id, ver_id):
        schedule = Schedule.objects.get(slug=sch_id, department__slug=dept_id)
        version = schedule.versions.get(num=ver_id)
        unfavorables = version.slots.exclude(shift__phase__max_time=F('employee__phase_pref__max_time'))
        empls = schedule.employees.all().annotate(
            n_unfavorables=Count('slots', filter=Q(slots__in=unfavorables))
        )
        return render(request, 'ver/ver-unfavorables.pug', {
            'version': version,
            'unfavorables': unfavorables,
            'week_values': list(set(version.workdays.values_list('wk_id', flat=True))),
            'employees': empls.filter(n_unfavorables__gt=0),
        })

    @staticmethod
    def ver_hours_distribution(request, org_id, dept_id, sch_id, ver_id):
        schedule = Schedule.objects.get(slug=sch_id, department__slug=dept_id)
        version = schedule.versions.get(num=ver_id)

    @staticmethod
    def empl_ver_view(request, org_id, dept_id, sch_id, ver_id, emp_id):
        schedule = Schedule.objects.get(slug=sch_id, department__slug=dept_id)
        version = schedule.versions.get(num=ver_id)
        emp = schedule.employees.get(slug=emp_id)

        periods = []

        for pd in set(version.workdays.values_list('prd_id', flat=True).distinct()):
            prd = version.slots.filter(employee=emp, workday__prd_id=pd)
            periods.append(
                [{'sum': prd.aggregate(Sum('shift__hours'))['shift__hours__sum'],
                  'dates': list(prd.values_list('workday__date', 'shift__name'))}])

        workdays = []
        for wd in version.workdays.all():
            print(wd.on_tdo.filter(pk=emp.pk))
            if wd.slots.filter(employee=emp).exists():
                workdays.append(wd.slots.get(employee=emp).shift)
            elif PtoRequest.objects.filter(employee=emp, date=wd.date).exists():
                workdays.append("PTO")
            elif wd.on_tdo.filter(pk=emp.pk).exists():
                workdays.append("TDO")
            else:
                workdays.append(".")

        return render(request, 'ver/emp-view.pug', {
            'periods': periods,
            'emp': emp,
            'workdays': workdays,
        })


class DayViews:

    @staticmethod
    def workday_detail_view(request, org_id, dept_id, sch_id, ver_id, wd_id):
        dept = Department.objects.get(slug=dept_id)
        schedule = Schedule.objects.get(slug=sch_id, department=dept)
        ver = schedule.versions.get(num=ver_id)
        workday = ver.workdays.get(date=wd_id)
        pto_reqs = workday.version.schedule.pto_requests.filter(date=workday.date).values(
            'employee__first_name', 'employee__last_name', 'employee__slug')
        slots = workday.slots.all()
        for slot in slots:
            for fw in slot.fills_with.all():
                fw.save()
            slot.save()
        return render(request, 'wd/wd-detail.pug', {
            'schedule': schedule,
            'version': ver,
            'workday': workday,
            'pto_reqs': pto_reqs,
            'workday_slots': slots,
        })

    @staticmethod
    def workday_table_view(request, org_id, dept_id, sch_id, ver_id, wd_id):
        dept = Department.objects.get(slug=dept_id)
        schedule = Schedule.objects.get(slug=sch_id, department=dept)
        ver = schedule.versions.get(num=ver_id)
        workday = ver.workdays.get(date=wd_id)
        return render(request, 'wd/wd-table.pug', {
            'schedule': schedule,
            'version': ver,
            'employees': schedule.employees.all(),
            'workday': workday,
            'shifts': Shift.objects.filter(pk__in=workday.slots.all().values('shift__pk'))
        })


class SlotViews:

    @staticmethod
    def slot_detail_view(request, org_id, dept_id, sch_id, ver_id, wd_id, slot_id):
        from django.db.models import OuterRef, Subquery, Sum, F, Value, IntegerField
        from django.db.models.functions import Coalesce
        from .models import Slot

        dept = Department.objects.get(slug=dept_id)
        schedule = Schedule.objects.get(slug=sch_id, department=dept)
        ver = schedule.versions.get(num=ver_id)
        workday = ver.workdays.get(date=wd_id)
        slot = workday.slots.get(shift__name=slot_id)
        fills_with = slot.fills_with.all()
        for fw in fills_with:
            fw.hours_in_week = Slot.objects.filter(employee=fw.employee, workday__version=ver,
                                                   workday__wk_id=fw.slot.workday.wk_id).aggregate(
                hours_in_week=Coalesce(Sum('shift__hours'), Value(0), output_field=IntegerField()))['hours_in_week']
            fw.hours_in_period = Slot.objects.filter(employee=fw.employee, workday__version=ver,
                                                     workday__wk_id__lte=fw.slot.workday.wk_id).aggregate(
                hours_in_period=Coalesce(Sum('shift__hours'), Value(0), output_field=IntegerField()))['hours_in_period']
            fw.hours_needed = fw.employee.fte * 80 - fw.hours_in_period

            fw.save()

        return render(request, 'slot/slot-detail.pug', {
            'schedule': schedule,
            'version': ver,
            'workday': workday,
            'slot': slot,
            'fills_with': fills_with,
        })

    @staticmethod
    def assign_slot(request, org_id, dept_id, sch_id, ver_id, wd_id, slot_id, emp_id):
        dept = Department.objects.get(slug=dept_id)
        schedule = Schedule.objects.get(slug=sch_id, department=dept)
        ver = schedule.versions.get(num=ver_id)
        workday = ver.workdays.get(date=wd_id)
        slot = workday.slots.get(shift__name=slot_id)
        empl = dept.employees.get(slug=emp_id)
        slot.set_employee(empl)
        slot.save()
        messages.success(request, f'{empl.initials} assigned to {slot.shift.name} on {slot.workday.date}')
        return HttpResponseRedirect(slot.workday.url)
