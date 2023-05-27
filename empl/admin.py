from django.contrib import admin
from .models import Employee
from org.models import Training, Shift

from django import forms

# Register your models here.

class TrainingInline(admin.TabularInline):
    model = Training
    fields = ['employee','shift','is_available','effective_date','sentiment_qual','sentiment_quant']
    readonly_fields = ['employee','effective_date']
    show_change_link = True
    extra = 0
    sortable_by = ['sentiment_quant']
    sortable_field_name = 'sentiment_quant'


    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "shift":
            employee_id = request.resolver_match.kwargs.get('object_id')
            employee = Employee.objects.filter(id=employee_id)
            if employee.exists():
                kwargs["queryset"] = Shift.objects.filter(department=employee.first().department)
            else:
                kwargs['queryset'] = Shift.objects.none()
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


    def get_formset(self, request, obj=None, **kwargs):
        formset = super().get_formset(request, **kwargs)
        if obj:
            formset = super().get_formset(request, obj, **kwargs)
            formset.form.base_fields['is_available'].initial = True
        return formset



@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    change_list_template = "admin/change_list_filter_sidebar.html"

    fields = ['first_name','last_name','department','active','fte','phase_pref']
    list_display = ['__str__', 'department', 'active', 'fte', 'display_shifts_trained', 'phase_pref']
    list_editable = ['department', 'fte', 'phase_pref']
    list_filter = ['department', 'active', 'fte',]
    readonly_fields = []
    inlines = [TrainingInline]

    display_shifts_trained = lambda self, obj: " | ".join(list(obj.shifts_trained.all().values_list('name',flat=True)))
    display_shifts_trained.short_description = 'Shifts Trained'








