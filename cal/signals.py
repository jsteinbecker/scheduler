from empl.models import PtoRequest
from .models import Slot, FillsWith, Workday, Version
from empl.models import TemplatedDayOffSet
from django.db.models.signals import post_save, pre_save, m2m_changed, post_init
from django.dispatch import receiver, Signal
from django.db.models import Sum, Avg, Max



@receiver(post_save,sender=Slot)
def slot_informs_workday_of_fill(sender, instance:Slot, **kwargs):
    if instance.employee:
        slots = instance.workday.slots.exclude(pk=instance.pk)
        for slot in slots:
            slot.fills_with.all().update(other_on_day=True)
        if instance.workday.slots.exclude(pk=instance.pk).filter(employee=instance.employee).exists():
            print("WARNING: OTHER WORKDAY WITH EMPLOYEE EXISTS")

@receiver(post_save,sender=Slot)
def slot_checks_for_turnaround(sender, instance:Slot, **kwargs):
    if instance.employee:
        if instance.conflicts.filter(employee=instance.employee).exists():
            instance.state = instance.SlotStates.TURNAROUND
            conflict = instance.conflicts.filter(employee=instance.employee).first()
            conflict.state = conflict.SlotStates.TURNAROUND

@receiver(post_save,sender=Slot)
def slot_check_adjacent_one_off_state(sender, instance:Slot, **kwargs):
    if instance.employee:
        if instance.workday.get_previous():
            if instance.workday.get_previous().slots.filter(employee=instance.employee).exists():
                instance.workday.get_previous().slots.filter(employee=instance.employee).update(is_one_off=False)
        if instance.workday.get_next():
            if instance.workday.get_next().slots.filter(employee=instance.employee).exists():
                instance.workday.get_next().slots.filter(employee=instance.employee).update(is_one_off=False)

@receiver(post_save,sender=Slot)
def slot_disallows_turnaround_fills(sender, instance:Slot, **kwargs):
    if instance.employee:
        instance.conflicting_slots.fills_with().filter(employee=instance.employee).update(other_on_conflicting=True)

@receiver(post_save,sender=Slot)
def slot_checks_for_pto(sender, instance:Slot, **kwargs):
    if instance.employee:
        if PtoRequest.objects.filter(date=instance.workday.date, employee=instance.employee).exists():
            instance.state = instance.SlotStates.PTO_CONFLICT

@receiver(post_save,sender=Workday)
def workday_checks_for_pto(sender, instance:Workday, created, **kwargs):
    if created:
        for slot in instance.slots.all():
            if slot.employee:
                if PtoRequest.objects.filter(date=instance.date, employee=slot.employee).exists():
                    slot.state = slot.SlotStates.PTO_CONFLICT
                    slot.save()

@receiver(pre_save, sender=Version)
def version_update_stats(sender, instance:Version, **kwargs):
    max_percent = instance.schedule.versions.aggregate(max_percent=Max('percent'))['max_percent']
    if instance.percent == max_percent:
        instance.is_best = True
    else:
        instance.is_best = False
    instance.n_unfavorables = instance.slots.with_disliked_shifts().count()
    instance.n_disliked_one_offs = instance.slots.filter(is_one_off=True).filter(employee__trade_one_offs=True).count()
    instance.n_empty = instance.slots.filter(employee=None).count()


