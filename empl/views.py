from django.shortcuts import render
import datetime as dt
from django.forms import modelformset_factory, formset_factory
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib import messages
from django.urls import reverse_lazy

from .models import Employee, TemplatedDayOffSet, PtoRequest, TemplateSlotSet, TemplateSlot
from .forms import DayOffForm
from org.models import Organization, Department, Shift
# Create your views here.

def empl_detail_view(request, org_id, dept_id, emp_id):
    emp = Employee.objects.get(slug=emp_id)
    return render(request, 'empl/empl-detail.pug', {
                'employee': emp, # type: Employee
                'tdo_sets': emp.templated_day_off_sets.all(),
                'pto_requests': emp.pto_requests.all(),
                'template_set': emp.template_slot_sets.first() or None,

            })

def empl_tdoset_view(request, org_id, dept_id, emp_id, tdoset_date):
    emp = Employee.objects.get(slug=emp_id, department__slug=dept_id,)
    tdoset = TemplatedDayOffSet.objects.filter(effective_date=tdoset_date, employee=emp)
    if tdoset.count() > 1 or tdoset.count() == 0:
        messages.error(request, f"Multiple TDOSets found for {emp} on {tdoset_date}")
        return HttpResponseRedirect(emp.url)
    tdoset = tdoset.first()
    return render(request, 'empl/empl-tdoset.pug', {
                'employee': emp, # type: Employee
                'tdoset': tdoset, # type: TemplatedDayOffSet
            })

def empl_tdoset_new(request, org_id, dept_id, emp_id):
    emp = Employee.objects.get(slug=emp_id)
    dept = emp.department
    week_count = emp.template_size
    day_range = range(1, (week_count * 7) +1)
    if TemplatedDayOffSet.objects.filter(employee=emp, effective_date=dt.date.today()).count() > 0:
        messages.error(request, f"TDOSet already exists for {emp} on {dt.date.today()}")
        return HttpResponseRedirect(emp.url)
    if request.method == 'POST':
        tdoset = TemplatedDayOffSet.objects.create(employee=emp, effective_date=dt.date.today())
        tdoset.save()
        truth_array = [False] * week_count * 7
        days_off = request.POST.getlist('form-day')
        for day in days_off:
            truth_array[int(day)-1] = True
        tdoset.days = ''.join(['T' if x else 'F' for x in truth_array])
        tdoset.save()
        print(tdoset.days)
        return HttpResponseRedirect(emp.url)
    return render(request, 'empl/empl-new-tdoset.pug', {
                'employee': emp, # type: Employee
                'day_range': day_range,
                'one_week': range(1,8),
            })

def empl_new_templates (request, org_id, dept_id, emp_id):
    dept = Department.objects.get(slug=dept_id)
    emp = Employee.objects.get(slug=emp_id,department=dept)
    if TemplateSlotSet.objects.filter(employee=emp, effective_date=dt.date.today()).count() > 0:
        tss = TemplateSlotSet.objects.filter(employee=emp, effective_date=dt.date.today()).first()
        tss.delete()
    week_count = emp.template_size
    day_range = [
        {'sd_id': i,
         'shifts': Shift.objects \
             .filter(pk__in=emp.trainings \
                     .filter(
                        is_available=True,
                        shift__weekdays__contains="SMTWRFA"[(i-1)%7]
                    ).values('shift')) \
             .exclude(pk__in=
                TemplateSlot.objects.filter(
                    slot_set__active=True,
                    sd_id=i) \
                .values('shift__pk')
         ),
         }
        for i in range(1, (week_count * 7) +1)
    ]

    if request.method == 'POST':
        data = request.POST
        print(data)
        cleaned = []
        template_repeats = emp.department.schedule_week_count // week_count
        print(f"Template repeats: {template_repeats}")
        template_set = TemplateSlotSet.objects.create(employee=emp, effective_date=dt.date.today(), active=True)
        for d in range(1, (week_count * 7) +1):
            if request.POST.get(f'sft-{d}', None):
                print(f"Day {d} has a shift")
                day = d
                shift = Shift.objects.filter(slug=request.POST.get(f'sft-{d}'))
                if shift.exists():
                    shift = shift.first()
                    days = [int(day) + (7 * r * template_repeats) for r in range(template_repeats)]
                    for i in days:
                        template = TemplateSlot.objects.create(slot_set=template_set, sd_id=i, shift=shift, )
                        template.save()
                    print(template)
        template_set.save()
        print(template_set)
        return HttpResponseRedirect(emp.url)
    return render(request, 'template-set/tset.pug', {
                'employee': emp, # type: Employee
                'days': day_range,
            })

def empl_switch_template_size(request, org_id, dept_id, emp_id):
    emp = Employee.objects.get(slug=emp_id, department__slug=dept_id,)
    dept = emp.department
    if emp.template_size == Employee.TemplateSizeChoices.WEEKS_2:
        emp.template_size = Employee.TemplateSizeChoices.WEEKS_3
    elif emp.template_size == Employee.TemplateSizeChoices.WEEKS_3:
        emp.template_size = Employee.TemplateSizeChoices.WEEKS_2

    emp.save()
    return HttpResponseRedirect(reverse_lazy('org:empl:template-set-new', args=(org_id, dept_id, emp_id,)))







