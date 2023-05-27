from django.shortcuts import render, reverse
from django.http import HttpResponseRedirect

from cal.models import Workday
from .models import Organization, Department, Shift
# Create your views here.

class OrgViews:

    @staticmethod
    def redirect_to_org(request):
        if request.user.is_authenticated:
            if Organization.objects.filter(linked_accounts=request.user).exists():
                org = Organization.objects.get(linked_accounts=request.user)
                return HttpResponseRedirect(reverse('org:org-detail', args=(org.slug,)))

        return HttpResponseRedirect('/')

    @staticmethod
    def org_detail_view(request, org_id):
        org = Organization.objects.get(slug=org_id)
        return render(request, 'org/org-detail.pug', {
            'organization': org,
            'departments': org.departments.all(),
            'shifts': Shift.objects.filter(department__organization=org),
        })


class DeptViews:

    @staticmethod
    def dept_detail_view(request, org_id, dept_id):
        dept = Department.objects.get(slug=dept_id)
        return render(request, 'dept/dept-detail.pug', {
            'department': dept,
            'shifts': dept.shifts.all(),
        })

class ShiftViews:

    @staticmethod
    def shift_detail_view(request, org_id, dept_id, sft_id):
        shift = Shift.objects.get(slug=sft_id)
        weekdays = shift.weekdays.split(',')
        return render(request, 'sft/shift-detail.pug', {
            'shift': shift,
            'weekdays': weekdays,
        })

