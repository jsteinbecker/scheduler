from django.http import HttpResponseRedirect, HttpResponse

from cal.models import Version, Slot, Workday, FillsWith, Schedule
from django.contrib.auth.models import User
from django.db.models import Sum, Count, F, Q, Subquery, OuterRef

from empl.models import Employee


def solve_version(request, org_id, dept_id, sch_id, ver_id):
    user = request.user
    version = Version.objects.get(schedule__slug=sch_id, num=ver_id, schedule__department__slug=dept_id)

    percent_initial = version.percent
    n_empty = version.slots.empty().count()

    for slot in version.slots.empty():
        slot.actions.solve(slot)

    percent_final = version.percent
    n_filled = n_empty - version.slots.empty().count()

    return HttpResponseRedirect(version.url())

def set_version_templates(request, org_id, dept_id, sch_id, ver_id):
    user = request.user
    version = Version.objects.get(schedule__slug=sch_id, num=ver_id)

    n = 0
    for slot in version.slots:
        if slot.template_employee:
            slot.set_employee(slot.template_employee)
            n += 1

    return HttpResponseRedirect(version.url())

def empl_phase_string(request, org_id, dept_id, sch_id, ver_id, emp_id):
    """EMPLOYEE PHASE STRING

    HTTP_RESPONSE
    ==========================
    A comma-separated string of the employee's phase for each workday in the version.

    example
    --------------------------
    empl_phase_string(request, 'org', 'dept', 'sch', 'ver', 'emp')

    >>> '1,1,2,.,.,.,2,2,3'
    """
    sch = Schedule.objects.get(slug=sch_id, department__slug=dept_id)
    ver = Version.objects.get(schedule=sch, num=ver_id)
    emp = sch.department.employees.get(slug=emp_id)
    output = []
    for wd in ver.workdays.all():
        if wd.slots.filter(employee=emp):
            output += [str(wd.slots.get(employee=emp).shift.phase)]
        else:
            output += ['.']
    return HttpResponse(','.join(output))


