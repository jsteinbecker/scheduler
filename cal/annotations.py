from django.db.models import Sum

from sch.models import *


# for Employee EMP, get their slots in Version VER,
# group the slots by Slot.workday.week_id, and aggregate the Sum of the Slot.shift.hours
# for each week_id, get the sum of the hours


def empl_version_hours_by_week(emp, ver):
    """
    Annotate EMPLOYEE sum(HOURS) in VERSION grouped by WEEK
    """
    return Slot.objects \
        .filter(employee=emp, workday__version=ver) \
        .values('workday__wk_id') \
        .annotate(
        hours=Sum('shift__hours')).order_by('workday__wk_id')


def empl_version_hours_by_period(emp, ver):
    return Slot.objects \
        .filter(employee=emp, workday__version=ver) \
        .values('workday__prd_id') \
        .annotate(
        hours=Sum('shift__hours')).order_by('workday__prd_id')
