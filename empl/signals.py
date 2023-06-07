from django.dispatch import receiver
from django.db.models.signals import post_save, pre_save, m2m_changed, post_init, post_delete
from django.db.models import Sum, F
from django.utils import timezone
from django.utils.text import slugify

from .models import PtoRequest, Employee, DayTemplateSet, DayTemplate
from org.models import DepartmentNotification
from cal.models import Slot, Workday, FillsWith


@receiver(post_init, sender=Employee)
def employee_validate_on_init(sender, instance: Employee, **kwargs):
    if instance.name and not instance.first_name and not instance.last_name:
        instance.first_name, instance.last_name = instance.name.split(' ')
    if instance.first_name and instance.last_name and not instance.name:
        instance.name = f"{instance.first_name} {instance.last_name}"
    if not instance.initials:
        if instance.name:
            initials = f"{instance.name[0]}{instance.name.split(' ')[1][0]}"
            if instance.department.employees.filter(initials=initials):
                i = 2
                while instance.department.employees.filter(initials=f"{initials}+{i}").count() > 0:
                    i += 1
                initials = f"{initials}{i}"
            instance.initials = initials
    if not instance.slug:
        instance.slug = slugify(f"{instance.first_name} {instance.last_name}")

@receiver(post_save, sender=DayTemplateSet)
def build_template_set(sender, instance: DayTemplateSet, created, **kwargs):
    if created:
        cycle_ratio  = instance.employee.department.schedule_day_count // (instance.employee.template_size * 7)
            # typically 2, 3
        cycle_size  = instance.employee.department.schedule_day_count // cycle_ratio
            # typically 14, 21
        cycle_count = instance.employee.department.schedule_day_count // cycle_size

        for i in range(1, instance.employee.department.schedule_day_count+1):
            if i <= cycle_size:
                dt = DayTemplate.objects.create(sd_id=i, employee=instance.employee, primary_cycle=True)
                dt.save()
                instance.day_templates.add(dt)
            else:
                dt = DayTemplate.objects.create(sd_id=i, employee=instance.employee)
                dt.save()
                instance.day_templates.add(dt)
        for p in instance.day_templates.filter(primary_cycle=True):
            for i in range(1, cycle_count):
                sd_id = p.sd_id + (i * cycle_size)
                p.analogs.add(instance.day_templates.get(sd_id=sd_id))

@receiver(post_save, sender=DayTemplate)
def template_updates_analogs(sender, instance: DayTemplate, **kwargs):
    if instance.primary_cycle:
        for analog in instance.analogs.all():
            analog.shift = instance.shift
            analog.shift_options.set(instance.shift_options.all())
            analog.state = instance.state
            analog.save()

@receiver(post_save, sender=PtoRequest)
def pto_request_gathers_basic_info(sender, instance: PtoRequest, **kwargs):
    if instance.pk:
        if not instance.wk_id:
            instance.wk_id = instance.date.strftime("%-U")
        if not instance.prd_id:
            instance.prd_id = int(instance.date.strftime("%-U")) // 2 + 1


@receiver(post_save, sender=PtoRequest)
def ptoreq_informs_schedule_elems(sender, instance, **kwargs):
    sch = Workday.objects.filter(date=instance.date, version__schedule__department=instance.employee.department)
    if sch.exists():
        sch = sch.first().version.schedule
        if instance not in sch.pto_requests.all():
            sch.pto_requests.add(instance)
    if instance.employee:
        if Slot.objects.filter(employee=instance.employee, workday__date=instance.date).exists():
            alert = DepartmentNotification.objects.create(
                department=instance.employee.department,
                message="{} has requested PTO on {} but is already scheduled to work that day".format(
                                        instance.employee.__str__(),
                                        instance.date.strftime("%m/%d/%Y")
                                    ))
            alert.save()
        FillsWith.objects.filter(
            slot__workday__date=instance.date,
            slot__employee=instance.employee).update(state=F('state') + FillsWith.States.PTO)

@receiver(post_save, sender=PtoRequest)
def ptoreq_associate_with_workdays(sender, instance, **kwargs):
    if instance.employee:
        if Workday.objects.filter(date=instance.date, version__schedule__department=instance.employee.department).exists():
            instance.workdays.set(Workday.objects.filter(date=instance.date, version__schedule__department=instance.employee.department))

@receiver(post_save, sender=PtoRequest)
def ptoreq_updates_slot_state(sender, instance, **kwargs):
    if instance.employee:
        if Slot.objects.filter(employee=instance.employee, workday__date=instance.date).exists():
            Slot.objects.filter(employee=instance.employee, workday__date=instance.date).update(state__is_pto_conflict=True)

@receiver(post_save, sender=PtoRequest)
def ptoreq_updates_fills_with(sender, instance, **kwargs):
    if instance.employee:
        FillsWith.objects.filter(
            slot__workday__date=instance.date,
            slot__employee=instance.employee).update(state=F('state')+FillsWith.States.PTO)

@receiver(post_delete, sender=PtoRequest)
def ptoreq_informs_schedule_elems_deletion(sender, instance, **kwargs):
    sch = Workday.objects.filter(date=instance.date, version__schedule__department=instance.employee.department).first().version.schedule
    if sch:
        if instance in sch.pto_requests.all():
            sch.pto_requests.remove(instance)

@receiver(post_save, sender=DayTemplateSet)
def template_update_active(sender, instance: DayTemplateSet, **kwargs):
    if instance.is_active:
        if instance.expiration_date:
            if instance.expiration_date < timezone.now().date():
                instance.is_active = False
                instance.save()