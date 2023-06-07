from django import forms
from django.forms import formset_factory
from .models import Employee, PtoRequest

class DayOffForm (forms.Form):
    is_off = forms.BooleanField()
    day_id = forms.IntegerField(widget=forms.HiddenInput())


class PtoForm(forms.Form):
    start_date = forms.DateField()
    end_date = forms.DateField(required=False)
    is_range = forms.BooleanField(required=False)
    employee = forms.ModelChoiceField(queryset=Employee.objects.all(), widget=forms.HiddenInput())


    is_range.widget_attrs({'_': 'on mutation of anything '
                                    'if is_range is true, '\
                                        'remove .hidden from #id_end_date '\
                                    'else add .hidden to #id_end_date end'})
    end_date.widget_attrs({'class': 'hidden'})
    end_date.validators.append(lambda x, start_date: x > start_date)


    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        if end_date and start_date > end_date:
            raise forms.ValidationError('Start date must be before end date')
        return cleaned_data

    def save(self, employee):
        start_date = self.cleaned_data.get('start_date')
        end_date = self.cleaned_data.get('end_date')
        if end_date:
            delta = end_date - start_date
            for i in range(delta.days + 1):
                PtoRequest.objects.create(employee=employee, date=start_date + dt.timedelta(days=i))
        else:
            PtoRequest.objects.create(employee=employee, date=start_date)


