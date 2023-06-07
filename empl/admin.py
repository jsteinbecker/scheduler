from django.contrib import admin
from django.utils.safestring import mark_safe

from .models import Employee
from org.models import Training, Shift
from grappelli.forms import GrappelliSortableHiddenMixin
from scheduler.settings import STATIC_URL

from django import forms

# Register your models here.

class TrainingInline(GrappelliSortableHiddenMixin, admin.TabularInline):
    model = Training
    fields = ['employee','shift','is_available','effective_date','sentiment_qual','sentiment_quant','rank']
    readonly_fields = ['employee','effective_date','rank']
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


    # add class form-row to field 'phase_pref''s grp-related-widget
    def formfield_for_dbfield(self, db_field, **kwargs):
        if db_field.name == "phase_pref":
            kwargs['widget'] = forms.RadioSelect(attrs={'style': 'display: inline-flex; flex-direction: row;'})
        return super().formfield_for_dbfield(db_field, **kwargs)

    def rank(self, obj):
        return f"Ranked # {obj.sentiment_quant + 1}"




@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):

    change_list_template = "admin/change_list_filter_sidebar.html"

    fieldsets = (
        ("Basic Information", {
                        'fields': ('first_name','last_name','fte',),
                        'description': "Basic information about the employee."
                       }),
        ("Department", { 'fields': ("department", "user", "hire_date", "active",),
                            'description': "Department information about the employee."
                        }),
        ("Schedule Handling", {
                        'fields': ("template_size", "phase_pref", "pto_hours_size", "trade_one_offs"),
        }),
    )

    list_display = ['full_name', 'department', 'active', 'fte', 'display_shifts_trained', 'phase_pref', 'template_size', 'pto_hours_size']
    list_editable = ['department', 'fte', 'phase_pref','template_size', 'pto_hours_size']
    list_filter = ['department', 'active', 'fte',]
    search_fields = ['first_name', 'last_name', 'department__name']
    sortable_by = ['full_name', 'department', 'fte']
    readonly_fields = []
    inlines = [TrainingInline]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.filter(active=True).order_by('department','first_name','last_name')

    def phase_pref(self, obj):
        return obj.phase_pref

    phase_pref.short_description = 'Phase Preference'

    full_name = lambda self, obj: obj.__str__()
    full_name.short_description = 'Name'
    display_shifts_trained = lambda self, obj: " | ".join(list(obj.shifts_trained.all().values_list('name',flat=True)))
    display_shifts_trained.short_description = 'Shifts Trained'








