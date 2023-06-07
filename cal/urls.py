from django.urls import path, include
from .models import Schedule, Workday, Version, Slot

from .views import SchViews, VerViews, DayViews, SlotViews
from .version.actions import solve_version


app_name = 'cal'

urlpatterns = [

        path('', SchViews.sch_list_view, name='sch-list'),
        path('new/', SchViews.new_schedule_view, name='new-sch'),

        path('<sch_id>/', SchViews.sch_detail_view, name='sch-detail'),
        path('<sch_id>/prn-employees/', SchViews.define_prn_employee_requested_hours, name='sch-prn-empls'),
        path('<sch_id>/data/emp-n-pto/<emp_id>/', SchViews.Data.sch_empl_pto_count, name='sch-data-emp-n-pto'),
        path('<sch_id>/edit-pto/<emp_id>/', SchViews.empl_pto_view, name='sch-emp-pto'),
        path('<sch_id>/edit-pto/<emp_id>/<day>/', SchViews.empl_pto_view_day_partial, name='sch-emp-pto-day'),
        path('<sch_id>/delete/', SchViews.del_schedule, name='sch-delete'),

        path('<sch_id>/v/new/', VerViews.new_version_view, name='new-ver'),

        path('<sch_id>/v/<ver_id>/', VerViews.ver_detail_view, name='ver-detail'),
        path('<sch_id>/v/<ver_id>/delete/', VerViews.del_version, name='ver-delete'),
        path('<sch_id>/v/<ver_id>/views/unfavorables/', VerViews.ver_unfavorables, name='ver-unfavorables'),

        path('<sch_id>/v/<ver_id>/actions/', include('cal.version.urls', namespace='ver-actions')),

        path('<sch_id>/v/<ver_id>/actions/assign-templates/', VerViews.ver_assign_templates, name='ver-assign-templates'),
        path('<sch_id>/v/<ver_id>/actions/assign-generics/', VerViews.ver_assign_generic_templates, name='ver-assign-generics'),
        path('<sch_id>/v/<ver_id>/actions/solve/', solve_version, name='ver-solve'),
        path('<sch_id>/v/<ver_id>/actions/resolve-pto/', VerViews.ver_fix_pto, name='ver-fix-pto'),
        path('<sch_id>/v/<ver_id>/actions/retry-one-offs/', VerViews.ver_clear_one_offs_and_retry, name='ver-oneoff-retry'),
        path('<sch_id>/v/<ver_id>/actions/reset/', VerViews.ver_clear_all, name='ver-reset'),
        path('<sch_id>/v/<ver_id>/emp/<emp_id>/', VerViews.empl_ver_view, name='ver-empl'),

        path('<sch_id>/v/<ver_id>/wd/<wd_id>/', DayViews.workday_detail_view, name='wd-detail'),
        path('<sch_id>/v/<ver_id>/wd/<wd_id>/table/', DayViews.workday_table_view, name='wd-detail-table'),

        path('<sch_id>/v/<ver_id>/wd/<wd_id>/slot/<slot_id>/', SlotViews.slot_detail_view,  name='slot-detail'),
        path('<sch_id>/v/<ver_id>/wd/<wd_id>/slot/<slot_id>/assign/<emp_id>/', SlotViews.assign_slot,  name='slot-assign')
    ]