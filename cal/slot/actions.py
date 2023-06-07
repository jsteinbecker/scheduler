from sch.models import Slot, DayTemplate


def get_highest_priority_template(slot:Slot):

    dept = slot.shift.department # type:Department
    sd_id = slot.workday.sd_id
    version = slot.workday.version
    pto_emps = slot.workday.pto_requests.values('employee')

    all_templates = DayTemplate.objects.filter(
            sd_id=sd_id,
            shift=slot.shift,
            collection__active=True,
            shift__department=dept,
        )
    if all_templates.filter(state='D').exists():
        definite_template_emp = all_templates.filter(state='D').first().employee
        if not definite_template_emp in pto_emps:
            return definite_template_emp

    if all_templates.filter(state='G').exclude(employee__in=pto_emps).exists():
        return all_templates.filter(state='G').exclude(employee__in=pto_emps)

    if all_templates.filter(state='A').exclude(employee__in=pto_emps).exists():
        return all_templates.filter(state='A').exclude(employee__in=pto_emps)



