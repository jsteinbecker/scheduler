from django.contrib import admin
from django.urls import path
from .views import OrgViews, DeptViews, ShiftViews
from cal.views import SchViews
from django.urls import include

app_name = 'org'

urlpatterns = [
    path('', OrgViews.redirect_to_org, name="org-detail"),
    path('<org_id>/', OrgViews.org_detail_view, name="org-detail"),
    path('<org_id>/dept/<dept_id>/', DeptViews.dept_detail_view, name="dept-detail"),
    path('<org_id>/dept/<dept_id>/shift/<sft_id>/', ShiftViews.shift_detail_view, name='shift-detail'),

    path('<org_id>/dept/<dept_id>/sch/', include('cal.urls', namespace='cal')),
    path('<org_id>/dept/<dept_id>/empl/', include('empl.urls', namespace='empl')),
]
