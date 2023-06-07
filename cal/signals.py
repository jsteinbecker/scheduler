import datetime
from itertools import combinations

from empl.models import PtoRequest, EmployeePayPeriodMonitor, EmployeeWeekMonitor
from .models import Slot, FillsWith, Workday, Version, Transaction, Schedule
from empl.models import Employee, DayTemplateSet, DayTemplate
from django.db.models.signals import post_save, pre_save, m2m_changed, post_init
from django.dispatch import receiver, Signal
from django.db.models import Sum, Avg, Max, F

__SLOT_SIGNALS__ = \
    """
    slot_empty_resets_state,
    slot_checks_for_tdo,
    slot_checks_for_pto,
    slot_empty_resets_state,
    slot_acquires_template_employee,
    slot_disallows_turnaround_fills,
    slot_check_adjacent_one_off_state,
    slot_checks_for_turnaround
    """



@receiver(post_init, sender=Schedule)
def schedule_gets_year_if_not_set(sender, instance: Schedule, **kwargs):
    if isinstance(instance.start_date, str):
        instance.start_date = datetime.datetime.strptime(instance.start_date, '%Y-%m-%d')
    if not instance.year:
        instance.year = instance.start_date.year


@receiver(post_save, sender=Slot)
def slot_build_fills_with_options(sender, instance: Slot, **kwargs):
            def definite_template_with_no_pto():
                if instance.pk:
                    version = instance.workday.version
                    definite_template = DayTemplate.objects.filter(
                        sd_id=instance.workday.sd_id,
                        state='D',
                        collection__is_active=True,
                        shift=instance.shift,
                        shift__department=instance.shift.department)

                    if definite_template.exists():
                        if def_template_employee := definite_template.first().employee:
                            if def_template_employee not in instance.workday.pto_requests.values('employee'):
                                instance.fills_with.create(employee=def_template_employee)
                                instance.state['d_template'] = True
                                return True, def_template_employee

                return False, None

            has_d_template, d_employee = definite_template_with_no_pto()

            def definite_template_employee_has_pto():
                sd_id = instance.workday.sd_id
                version = instance.workday.version
                shift = instance.shift
                instance.fills_with.filter(employee=instance.employee).delete()
                for employee in version.schedule.employees.filter(shifts_trained=shift):
                    if employee.day_templates.filter(sd_id=sd_id, state__in=['G', 'A', ]).exists():
                        if employee not in instance.workday.pto_requests.values('employee'):
                            instance.fills_with.get_or_create(employee=employee)
                            instance.state['d_template'] = False
                            return True

            if has_d_template:
                d_template_available = definite_template_employee_has_pto()

                if d_template_available:

                    instance.fills_with.all().delete()
                    fw = instance.fills_with.get_or_create(employee=d_employee)[0]

                    instance.state['d_template'] = True
                    instance.state['g_template'] = False
                    instance.state['a_template'] = False
                    fw.save()

                    return

            def check_for_generic_templates():
                if instance.pk:
                    version = instance.workday.version
                    generic_templates = DayTemplate.objects.filter(
                        sd_id=instance.workday.sd_id,
                        state='G',
                        collection__is_active=True,
                        shift=instance.shift,
                        shift__department=instance.shift.department)
                    if generic_templates.exists():
                        for template in generic_templates:
                            if template.employee:
                                if template.employee not in instance.workday.pto_requests.values('employee'):
                                    instance.fills_with.get_or_create(employee=template.employee)
                                    instance.state['g_template'] = True
                        return True, generic_templates
                return False, None

            has_g_template, g_templates = check_for_generic_templates()

            if has_g_template:
                instance.state['d_template'] = False
                instance.state['g_template'] = True
                instance.state['a_template'] = False

                return

            def check_for_availability_templates():
                if instance.pk:
                    version = instance.workday.version
                    avail_templates = DayTemplate.objects.filter(
                        sd_id=instance.workday.sd_id,
                        state='A',
                        collection__is_active=True,
                        shift=instance.shift,
                        shift__department=instance.shift.department)
                    if avail_templates.exists():
                        for template in avail_templates:
                            if template.employee:
                                if template.employee not in instance.workday.pto_requests.values('employee'):
                                    instance.fills_with.get_or_create(employee=template.employee)
                                    instance.state['a_template'] = True
                                    return True, avail_templates
                return False, None

            has_a_template, a_templates = check_for_availability_templates()


            if has_a_template:
                instance.state['d_template'] = False
                instance.state['g_template'] = False
                instance.state['a_template'] = True
                return

            def check_for_tdo_templates():
                if instance.pk:
                    version = instance.workday.version
                    tdo_templates = DayTemplate.objects.filter(
                        sd_id=instance.workday.sd_id,
                        state='T',
                        collection__is_active=True,
                        shift=instance.shift,
                        shift__department=instance.shift.department)
                    if tdo_templates.exists():
                        for template in tdo_templates:
                            if template.employee:
                                instance.fills_with.filter(employee=template.employee).delete()
                            return True, tdo_templates
                return False, None

            has_tdo_template, tdo_templates = check_for_tdo_templates()

            if has_tdo_template:
                instance.state['d_template'] = False
                instance.state['g_template'] = False
                instance.state['a_template'] = False
                instance.state['t_template'] = True
                return

            return



@receiver(post_save, sender=Slot)
def slot_autodelete_untrained_fills_withs(sender, instance:Slot, **kwargs):
    if instance.pk:
        for fw in instance.fills_with.exclude(employee__shifts_trained=instance.shift):
            fw.delete()

@receiver(post_save, sender=Slot)
def slot_update_state(sender, instance:Slot, **kwargs):
    initial = instance.state

    if instance.employee:

        instance.state['is_empty'] = False

        if instance.employee in instance.workday.on_tdo.all():
            instance.state['is_tdo_conflict'] = True
        else: instance.state['is_tdo_conflict'] = False

        if instance.employee in instance.workday.pto_requests.all():
            instance.state['is_pto_conflict'] = True
        else: instance.state['is_pto_conflict'] = False

        if instance.conflicts.filter(employee=instance.employee).exists():
            instance.state['is_turnaround'] = True
            conflict = instance.conflicts.filter(employee=instance.employee).first()
            conflict.state['is_turnaround'] = True
        else: instance.state['is_turnaround'] = False

        if instance.shift not in instance.employee.shifts_trained.all():
            instance.state['is_untrained'] = True
        else: instance.state['is_untrained'] = False

        instance.state['is_allowed'] = [True if instance.state[key] == False \
                                            else False for key in instance.state.keys() \
                                            if 'is_' in key]


@receiver(post_save, sender=Slot)
def slot_removes_conflicting_fills_withs(sender, instance:Slot, **kwargs):
    if instance.pk:
        if instance.employee:
            for fw in instance.conflicting_slots.filter(employee=instance.employee):
                fw.delete()

@receiver(post_save, sender=Slot)
def slot_check_adjacent_one_off_state(sender, instance: Slot, **kwargs):
    if instance.employee:
        if instance.workday.get_previous():
            if instance.workday.get_previous().slots.filter(employee=instance.employee).exists():
                instance.workday.get_previous().slots.filter(employee=instance.employee).update(is_one_off=False)
        if instance.workday.get_next():
            if instance.workday.get_next().slots.filter(employee=instance.employee).exists():
                instance.workday.get_next().slots.filter(employee=instance.employee).update(is_one_off=False)



@receiver(post_save, sender=Slot)
def slot_acquires_template_employee(sender, instance: Slot, created, **kwargs):
    if created:
        template = DayTemplate.objects.filter(sd_id=instance.workday.sd_id, shift=instance.shift,
                                              employee=instance.employee)
        if template.exists():
            instance.template_employee = template.first().employee


@receiver(post_save, sender=Slot)
def slot_checks_for_pto(sender, instance: Slot, **kwargs):
    pto_req = PtoRequest.objects.filter(
                date=instance.workday.date,
                employee__in=instance.workday.version.schedule.employees.all())
    if pto_req.exists():
        instance.fills_with.filter(employee__in=pto_req.values('employee')).delete()
    if instance.employee:
        if PtoRequest.objects.filter(
                date=instance.workday.date,
                employee=instance.employee).exists():
            instance.state['is_pto_conflict'] = True



@receiver(post_save, sender=Slot)
def slot_checks_for_tdo(sender, instance: Slot, **kwargs):
    tdos = DayTemplate.objects.filter(
                sd_id=instance.workday.sd_id,
                state=DayTemplate.States.TDO,
                collection__expiration_date__isnull=True)
    if tdos.exists():
        instance.fills_with.filter(employee__in=tdos.values('employee')).delete()
    if instance.employee:
        if DayTemplate.objects.filter(
                sd_id=instance.workday.sd_id,
                state=DayTemplate.States.TDO,
                employee=instance.employee,
                collection__expiration_date__isnull=False) \
                .exists():
            instance.state['is_tdo_conflict'] = True


@receiver(post_save, sender=Slot)
def slot_empty_resets_state(sender, instance: Slot, **kwargs):
    if not instance.employee: instance.state['is_empty'] = True


@receiver(post_save, sender=Workday)
def workday_checks_for_pto(sender, instance: Workday, created, **kwargs):
    if created:
        for slot in instance.slots.all():
            if slot.employee:
                if PtoRequest.objects.filter(date=instance.date, employee=slot.employee).exists():
                    slot.state['is_pto_conflict'] = True
                    slot.save()


@receiver(post_save, sender=Slot)
def slot_checks_for_turnaround(sender, instance: Slot, **kwargs):
    if instance.employee:
        if instance.conflicting_slots.filter(employee=instance.employee).exists():
            if instance.state['is_turnaround'] == False:
                instance.state['is_turnaround'] = True
                instance.save()
        if instance.conflicting_slots.fills_with.filter(employee=instance.employee).exists():
            instance.conflicting_slots.fills_with.filter(employee=instance.employee).delete()


@receiver(post_save, sender=Slot)
def slot_keeps_ppm_informed(sender, instance:Slot, **kwargs):
    if instance.employee:
        ppm = instance.workday.version.pay_period_monitors.get_or_create(employee=instance.employee,
                                                                         prd_id=instance.workday.prd_id,
                                                                         version=instance.workday.version)[0]
        ppm.slots.add(instance)
        ppm.hours = ppm.slots.aggregate(hours=Sum('shift__hours'))['hours']
        ppm.state = 'P' if ppm.hours > ppm.goal else 'S' if ppm.hours < ppm.goal else 'C'
        ppm.save()

        wkm = ppm.week_monitors.get_or_create(employee=instance.employee,
                                              wk_id=instance.workday.wk_id,
                                              version=instance.workday.version)[0]
        wkm.slots.add(instance)
        wkm.hours = wkm.slots.aggregate(hours=Sum('shift__hours'))['hours']
        wkm.state = 'P' if wkm.hours > wkm.goal else 'S' if wkm.hours < wkm.goal else 'C'
        wkm.save()

    if not instance.employee:
        for ppm in instance.workday.version.pay_period_monitors.filter(slots=instance):
            ppm.slots.remove(instance)
            ppm.save()

        for wkm in instance.workday.version.week_monitors.filter(slots=instance):
            wkm.slots.remove(instance)
            wkm.save()


@receiver(pre_save, sender=Version)
def version_update_stats(sender, instance: Version, user=None, **kwargs):
    instance.previous_n_unfavorables = instance.n_unfavorables
    instance.previous_n_disliked_one_offs = instance.n_disliked_one_offs
    instance.previous_n_empty = instance.n_empty
    instance.previous_n_mistemplated = instance.n_mistemplated
    instance.previous_n_disliked_shifts = instance.n_disliked_shifts

    instance.n_unfavorables = instance.slots.exclude(shift__phase__max_time=F('employee__phase_pref__max_time')).count()
    instance.n_disliked_one_offs = instance.slots.filter(is_one_off=True).filter(employee__trade_one_offs=True).count()
    instance.n_empty = instance.slots.filter(employee=None).count()
    #instance.n_mistemplated = instance.slots.filter().mistemplated.count()
    #instance.n_disliked_shifts = instance.slots.with_disliked_shifts().count()

    if user:
        tx = instance.transactions.create(
            user=user,
            delta_n_empty=instance.n_empty - instance.previous_n_empty,
            delta_n_unfavorables=instance.n_unfavorables - instance.previous_n_unfavorables,
            delta_n_disliked_one_offs=instance.n_disliked_one_offs - instance.previous_n_disliked_one_offs,
            delta_n_mistemplated=instance.n_mistemplated - instance.previous_n_mistemplated,
            delta_n_disliked_shifts=instance.n_disliked_shifts - instance.previous_n_disliked_shifts,
        )
        tx.save()

@receiver(post_save, sender=Version)
def version_get_active_templates(sender, instance: Version, **kwargs):
    templates = DayTemplateSet.objects.filter(expiration_date__isnull=False, employee__department=instance.schedule.department)
    instance.template_sets.set(templates)

@receiver(post_save, sender=Version)
def version_assign_template_employees_to_slots(sender, instance: Version, **kwargs):
    for template in instance.template_sets.all().values('day_templates').filter(
            day_templates__state=DayTemplate.States.DEFINED_SLOT):
        workday = instance.workdays.get(sd_id=template.sd_id)
        if not workday.pto_requests.filter(employee=template.employee).exists():
            slot = workday.slots.get(shift=template.shift)
            slot.template_employee = template.employee
            slot.save()

@receiver(post_save, sender=Version)
def version_builds_pay_period_monitors(sender, instance: Version, **kwargs):
    if EmployeePayPeriodMonitor.objects.filter(version=instance).exists() == False:
        print('building pay period monitors')
        for i in set(instance.workdays.values_list('prd_id', flat=True)):
            for empl in instance.schedule.department.employees.all():
                ppm = EmployeePayPeriodMonitor.objects.create(
                    employee=empl,
                    prd_id=i,
                    goal=empl.fte * 80,
                    version=instance
                )
                ppm.save()


@receiver(post_init, sender=EmployeePayPeriodMonitor)
def pay_period_monitor_builds_week_monitors(sender, instance: EmployeePayPeriodMonitor, **kwargs):
    if not instance.version.week_monitors.exists():
        wk1 = instance.version.workdays.first().wk_id
        wk2 = wk1 + 1
        for wk in [wk1, wk2]:
            wkm = instance.version.week_monitors.create(
                wk_id=wk,
                employee=instance.employee,
                goal=instance.goal / 2
            )
            wkm.save()

@receiver(post_save, sender=EmployeePayPeriodMonitor)
def ppm_update_state(sender, instance: EmployeePayPeriodMonitor, **kwargs):
    if instance.hours < instance.goal:
        instance.state = instance.States.SEEKING
    elif instance.hours > instance.goal:
        instance.state = instance.States.POLLING
    else:
        instance.state = instance.States.INACTIVE

@receiver(post_save, sender=EmployeeWeekMonitor)
def wkm_update_state(sender, instance: EmployeeWeekMonitor, **kwargs):
    if instance.hours < instance.goal:
        instance.state = instance.States.SEEKING
    elif instance.hours > instance.goal:
        instance.state = instance.States.POLLING
    else:
        instance.state = instance.States.INACTIVE



