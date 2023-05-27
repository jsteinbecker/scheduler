from django import forms
from django.contrib import admin

from .models import Organization, Department, Shift, Training


class ShiftForm(forms.ModelForm):

    on_weekdays = forms.MultipleChoiceField(
        choices=Shift.WeekdayChoices.choices,
        widget=forms.CheckboxSelectMultiple,
    )

    class Meta:
        model = Shift
        fields = '__all__'
        exclude = ('slug','weekdays')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.weekdays:
            self.fields['on_weekdays'].initial = self.instance.weekdays.split(',')
        request = kwargs.get('request')
        if request:
            self.fields['department'].queryset = Department.objects.filter(
                organization__in=request.user.organizations.all())
        else:
            self.fields['department'].queryset = Department.objects.all()


    def save(self, commit=True):
        instance = super().save(commit=False)
        on_weekdays = self.cleaned_data.get('on_weekdays')
        instance.weekdays = ','.join(on_weekdays)
        if commit:
            instance.save()
        return instance
