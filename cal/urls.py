from django.urls import path
from .models import Schedule, Workday, Version, Slot

from .views import SchViews, VerViews, DayViews, SlotViews


app_name = 'cal'

urlpatterns = [

        path('', SchViews.sch_list_view, name='sch-list'),
        path('new/', SchViews.new_schedule_view, name='new-sch'),
        path('<sch_id>/', SchViews.sch_detail_view, name='sch-detail'),
        path('<sch_id>/data/emp-n-pto/<emp_id>/', SchViews.Data.sch_empl_pto_count, name='sch-data-emp-n-pto'),
        path('<sch_id>/edit-pto/<emp_id>/', SchViews.empl_pto_view, name='sch-emp-pto'),
        path('<sch_id>/edit-pto/<emp_id>/<day>/', SchViews.empl_pto_view_day_partial, name='sch-emp-pto-day'),
        path('<sch_id>/delete/', SchViews.del_schedule, name='sch-delete'),

        path('<sch_id>/v/new/', VerViews.new_version_view, name='new-ver'),
        path('<sch_id>/v/<ver_id>/', VerViews.ver_detail_view, name='ver-detail'),
        path('<sch_id>/v/<ver_id>/views/unfavorables/', VerViews.ver_unfavorables, name='ver-unfavorables'),
        path('<sch_id>/v/<ver_id>/actions/assign-templates/', VerViews.ver_assign_templates, name='ver-assign-templates'),
        path('<sch_id>/v/<ver_id>/actions/solve/', VerViews.ver_solve, name='ver-solve'),
        path('<sch_id>/v/<ver_id>/actions/retry-one-offs/', VerViews.ver_clear_one_offs_and_retry, name='ver-oneoff-retry'),
        path('<sch_id>/v/<ver_id>/actions/reset/', VerViews.ver_clear_all, name='ver-reset'),
        path('<sch_id>/v/<ver_id>/emp/<emp_id>/', VerViews.empl_ver_view, name='ver-empl'),
        path('<sch_id>/v/<ver_id>/wd/<wd_id>/', DayViews.workday_detail_view, name='wd-detail'),
        path('<sch_id>/v/<ver_id>/wd/<wd_id>/slot/<slot_id>/', SlotViews.slot_detail_view, name='slot-detail'),
        path('<sch_id>/v/<ver_id>/wd/<wd_id>/slot/<slot_id>/assign/<emp_id>/', SlotViews.assign_slot, name='slot-assign')
    ]