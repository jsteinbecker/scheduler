from django.dispatch import receiver
from django.db.models.signals import post_save, pre_save, m2m_changed, post_init, post_delete
from django.db.models import Sum
from .models import PtoRequest
from org.models import DepartmentNotification
from cal.models import Slot, Workday, FillsWith


@receiver(post_save, sender=PtoRequest)
def ptoreq_informs_schedule_elems(sender, instance, **kwargs):
    sch = Workday.objects.filter(date=instance.date, version__schedule__department=instance.employee.department).first().version.schedule
    if sch:
        if instance not in sch.pto_list.all():
            sch.pto_list.add(instance)
    if instance.employee:
        if Slot.objects.filter(employee=instance.employee, workday__date=instance.date).exists():
            alert = DepartmentNotification.objects.create(
                department=instance.employee.department,
                message="{} has requested PTO on {} but is already scheduled to work that day".format(
                                        instance.employee.__str__(),
                                        instance.date.strftime("%m/%d/%Y")
                                    )
                                )
            alert.save()
        FillsWith.objects.filter(slot__workday__date=instance.date, slot__employee=instance.employee).update(has_pto=True)

@receiver(post_save, sender=PtoRequest)
def ptoreq_associate_with_workdays(sender, instance, **kwargs):
    if instance.employee:
        if Workday.objects.filter(date=instance.date, version__schedule__department=instance.employee.department).exists():
            instance.workdays.set(Workday.objects.filter(date=instance.date, version__schedule__department=instance.employee.department))

@receiver(post_save, sender=PtoRequest)
def ptoreq_updates_slot_state(sender, instance, **kwargs):
    if instance.employee:
        if Slot.objects.filter(employee=instance.employee, workday__date=instance.date).exists():
            Slot.objects.filter(employee=instance.employee, workday__date=instance.date).update(state=Slot.SlotStates.PTO_CONFLICT)

@receiver(post_save, sender=PtoRequest)
def ptoreq_updates_fills_with(sender, instance, **kwargs):
    if instance.employee:
        FillsWith.objects.filter(slot__workday__date=instance.date, slot__employee=instance.employee).update(has_pto=True)

@receiver(post_delete, sender=PtoRequest)
def ptoreq_informs_schedule_elems_deletion(sender, instance, **kwargs):
    sch = Workday.objects.filter(date=instance.date, version__schedule__department=instance.employee.department).first().version.schedule
    if sch:
        if instance in sch.pto_list.all():
            sch.pto_list.remove(instance)
        FillsWith.objects.filter(slot__workday__date=instance.date, slot__employee=instance.employee).update(has_pto=False)