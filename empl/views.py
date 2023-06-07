from django.db.models import OuterRef
from django.shortcuts import render
import datetime as dt
from django.forms import modelformset_factory, formset_factory
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib import messages
from django.urls import reverse_lazy
from django.views.decorators.csrf import csrf_exempt

from .models import Employee, PtoRequest, DayTemplateSet, DayTemplate
from .forms import DayOffForm
from org.models import Organization, Department, Shift
# Create your views here.

def empl_detail_view(request, org_id, dept_id, emp_id):
    emp = Employee.objects.get(slug=emp_id)
    return render(request, 'empl/empl-detail.pug', {
                'employee': emp, # type: Employee,
                'pto_requests': emp.pto_requests.all(),
                'template_set': emp.day_template_sets.last() or None,

            })


def empl_switch_template_size(request, org_id, dept_id, emp_id):
    emp = Employee.objects.get(slug=emp_id, department__slug=dept_id,)
    dept = emp.department
    if emp.template_size == Employee.TemplateSizeChoices.WEEKS_2:
        emp.template_size = Employee.TemplateSizeChoices.WEEKS_3
    elif emp.template_size == Employee.TemplateSizeChoices.WEEKS_3:
        emp.template_size = Employee.TemplateSizeChoices.WEEKS_2
    emp.save()
    emp.day_template_sets.filter(expiration_date__isnull=True).delete()
    return HttpResponseRedirect(reverse_lazy('org:empl:template-set', args=(org_id, dept_id, emp_id,)))

def empl_template_set(request, org_id, dept_id, emp_id):
    dept = Department.objects.get(slug=dept_id, organization__slug=org_id,)
    emp = Employee.objects.get(slug=emp_id, department__slug=dept_id,)


    if DayTemplateSet.objects.filter(employee=emp).exists():
        tmp_set = emp.day_template_sets.get(expiration_date__isnull=True)
        return render(request, 'empl/empl-new-template-set.pug', {'template_set': tmp_set, 'employee': emp, 'dept': dept,})

    tmp_set = DayTemplateSet.objects.create(employee=emp)
    tmp_set.save()
    return render(request, 'empl/empl-new-template-set.pug', {'template_set': tmp_set, 'employee': emp, 'dept': dept,})

def empl_template_set_del(request, org_id, dept_id, emp_id):
    if request.method == 'POST':
        emp = Employee.objects.get(slug=emp_id, department__slug=dept_id,)
        tmp_set = emp.day_template_sets.get(active=True)
        tmp_set.delete()
        return HttpResponseRedirect(reverse_lazy('org:empl:detail', args=(org_id, dept_id, emp_id,)))
    return HttpResponse('Method not allowed', status=405)

@csrf_exempt
def empl_day_template_partial(request, org_id, dept_id, emp_id, sd_id):
    emp      = Employee.objects.get(slug=emp_id, department__slug=dept_id,)
    tmp_set  = emp.day_template_sets.get(expiration_date__isnull=True)
    template = tmp_set.day_templates.get(sd_id=sd_id) # type: DayTemplate
    weekday  = Shift.WeekdayChoices.choices[(int(sd_id)-1)% 7][0]
    possibilities = emp.shifts_trained.exclude(
                pk__in= DayTemplate.objects.filter(
                employee__department= emp.department,
                sd_id= sd_id,
                shift= OuterRef('pk'),
                state__contains= DayTemplate.States.DEFINED_SLOT,
                 ).exclude(
            pk=template.pk
                ).values_list('shift__pk', flat=True)
            ).filter(
        weekdays__contains=weekday)

    taken_slots = DayTemplate.objects.filter(sd_id=sd_id, shift__isnull=False).values_list('shift__slug', flat=True)

    if template.state == 'D':
        for ts in taken_slots:
            template.shift_options.remove(Shift.objects.get(slug=ts))
        for sft in Shift.objects \
            .filter(department=emp.department) \
            .exclude(weekdays=Shift.WeekdayChoices.choices[template.sd_id % 7][0]):
                template.shift_options.remove(sft)
    elif template.state == 'G':
        for ts in taken_slots:
            template.shift_options.remove(Shift.objects.get(slug=ts))
        for sft in Shift.objects \
            .filter(department=emp.department) \
            .exclude(weekdays__contains=Shift.WeekdayChoices.choices[template.sd_id % 7][0]):
                template.shift_options.remove(sft)

    if request.method == 'POST':
        if template.state == 'D':
            shift = Shift.objects.get(slug=request.POST['shift'])
            template.shift = shift
            template.save()
            print(template.shift)
        elif template.state == 'G':
            template.state = 'G'
            shifts = request.POST.getlist('shifts')
            template.shift_options.clear()
            for shift in shifts:
                template.shift_options.add(Shift.objects.get(slug=shift))
            template.save()
            print(template.shift_options.all())

    return render(request, 'empl/empl-day-template-partial.pug',
                  {'template': template,'shifts': emp.shifts_trained.exclude(
                                            pk__in=DayTemplate.objects.filter(
                                                employee__department=emp.department) \
                                                .exclude(employee=emp).values_list('pk', flat=True)),
                   "selected_options": template.shift_options.all(),
                   "selected_shift": template.shift,
                     "taken_slots": taken_slots,
                     "possibilities": possibilities,
                   "weekday": weekday,
                   })


def empl_day_template_change(request, org_id, dept_id, emp_id, sd_id):
    emp = Employee.objects.get(slug=emp_id, department__slug=dept_id,)
    tmp_set = emp.day_template_sets.get(expiration_date__isnull=True)
    template = tmp_set.day_templates.get(sd_id=sd_id)
    template.change_state()
    template.save()
    return HttpResponseRedirect("../")



class PtoViews:

    @staticmethod
    def empl_list(request, org_id, dept_id, emp_id):
        from sch.models import Schedule
        from .forms import PtoForm

        emp = Employee.objects.get(slug=emp_id, department__slug=dept_id,)
        sch_initial = Schedule.objects.filter(employees=emp, start_date__gte=dt.date.today()).order_by('-start_date').first()

        if request.method == 'POST':
            form = PtoForm(request.POST, instance=emp)
            if form.is_valid():
                form.save()

        return render(request, 'pto/list.pug', {
            'employee': emp,
            'pto_requests': emp.pto_requests.all(),
            'form': PtoForm(initial={
                                'employee':emp,
                                'start_date': dt.date.today() + dt.timedelta(days=30),
                                'end_date': dt.date.today() + dt.timedelta(days=30),
                                'schedule': sch_initial
                        })
                    })

    @staticmethod
    def add(request, org_id, dept_id, emp_id, date):
        pass

    @staticmethod
    def delete(request, org_id, dept_id, emp_id, date):
        pass
