from django.urls import path

from . import views


app_name = 'empl'

urlpatterns = [

    path('<emp_id>/', views.empl_detail_view, name='detail'),

    path('<emp_id>/template-set/', views.empl_template_set, name='template-set'),
    path('<emp_id>/template-set/delete/', views.empl_template_set_del, name='template-set-delete'),
    path('<emp_id>/template-set/switch-template-size/', views.empl_switch_template_size, name='template-set-switch-size'),
    path('<emp_id>/template-set/<sd_id>/', views.empl_day_template_partial, name='template-set-slot'),
    path('<emp_id>/template-set/<sd_id>/change/', views.empl_day_template_change, name='template-set-slot-change'),

    path('<emp_id>/pto-requests/', views.PtoViews.empl_list, name='pto-list'),
    path('<emp_id>/pto-requests/<date>/add/', views.PtoViews.add, name='pto-add'),
    path('<emp_id>/pto-requests/<date>/delete/', views.PtoViews.delete, name='pto-delete'),
]