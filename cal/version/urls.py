from django.urls import path
from sch.models import Schedule, Workday, Version, Slot
from .actions import empl_phase_string


app_name = 'version_actions'

urlpatterns = [

    path('<emp_id>/phase-string/', empl_phase_string, name='empl-phase-string'),

]
