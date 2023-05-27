from django.urls import path

from . import views


app_name = 'empl'

urlpatterns = [

    path('<emp_id>/', views.empl_detail_view, name='detail'),
    path('<emp_id>/new-tdoset/', views.empl_tdoset_new, name='tdoset-new'),
    path('<emp_id>/tdoset/<tdoset_date>/', views.empl_tdoset_view, name='tdoset'),
    path('<emp_id>/template-set/new/', views.empl_new_templates, name='template-set-new'),
    path('<emp_id>/template-set/new/swap/', views.empl_switch_template_size, name='template-set-swap'),
]