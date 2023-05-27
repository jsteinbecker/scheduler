from django import forms
from django.forms import formset_factory
from .models import Employee, PtoRequest

class DayOffForm (forms.Form):
    is_off = forms.BooleanField()
    day_id = forms.IntegerField(widget=forms.HiddenInput())

