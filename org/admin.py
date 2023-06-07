from django.contrib import admin
from django.utils.safestring import mark_safe

from .models import Organization, Department, Shift, Training, TimePhase, DepartmentNotification

from grappelli.forms import GrappelliSortableHiddenMixin
from grappelli.urls_docs import urlpatterns as grappelli_docs_urlpatterns

from django import forms
from .forms import ShiftForm


class INLINES:
    class DeptNotificationInline(admin.StackedInline):
        model = DepartmentNotification
        extra = 0
        readonly_fields = ['department',]


    class DepartmentInline(admin.TabularInline):
        model = Department
        fields = ['name','full_name','schedule_week_count','initial_start_date']
        show_change_link = True
        extra = 0
        classes = ['collapse']



    class TimePhaseInlines(GrappelliSortableHiddenMixin, admin.TabularInline):
        fields = ['name','full_name','max_time' ,'organization','position','position_display']
        readonly_fields = ['organization','position_display']
        model = TimePhase
        extra = 0
        sortable_field_name = "position"
        verbose_name_plural = mark_safe('Time Phase Groups <br/> '
                                        '<span style="font-size: 0.95em; color: #777; font-style:italic;">'
                                        'Drag and drop to sort. Time phases are used to prevent employees from'
                                        'being scheduled into turnarounds.'
                                        '</span>')

        def position_display(self, obj):
            if obj.position == 0:
                return '1st'
            elif obj.position == 1:
                return '2nd'
            elif obj.position == 2:
                return '3rd'
            else:
                return f'{obj.position}th'

        position_display.short_description = 'Position'






@admin.register(Organization)
class OrgAdmin(admin.ModelAdmin):

    fields = ['name','full_name',]
    list_display = ['name','full_name','all_departments']
    list_editable = ['full_name']
    readonly_fields = ['all_departments']
    inlines = [
        INLINES.TimePhaseInlines,
        INLINES.DepartmentInline,
    ]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.filter(departments__employees=request.user.profile)

    def all_departments(self, obj):
        return " ✦ ".join(list(obj.departments.all().values_list('name',flat=True)))

from empl.models import Employee


class EmployeeInlines(admin.StackedInline):
    model = Employee
    radio_fields = {'phase_pref': admin.HORIZONTAL}
    fieldsets = (
        (None, {'fields': ('first_name','last_name','department','active','phase_pref', 'fte',)}),
    )
    readonly_fields = ['department','active']
    show_change_link = True
    extra = 0

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'department':
            kwargs['queryset'] = Department.objects.filter(organization__in=request.user.organizations.all())
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def get_formset(self, request, obj=None, **kwargs):
        formset = super().get_formset(request, obj, **kwargs)
        formset.form.base_fields['phase_pref'].widget.attrs['class'] = 'form-row'
        return formset

class ShiftInlines(admin.TabularInline):
    model = Shift
    fields = ['name','department','start_time','hours','phase']
    readonly_fields = ['department','phase']
    extra = 0
    show_change_link = True
    show_full_result_count = True


    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'department':
            kwargs['queryset'] = Department.objects.filter(organization__in=request.user.organizations.all())
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

@admin.register(Department)
class DeptAdmin(admin.ModelAdmin):

    fields = ['name','full_name','organization',
              'schedule_week_count','initial_start_date','image_url']
    readonly_fields = ['shifts']
    list_display = ['__str__','full_name','organization','schedule_week_count','initial_start_date']
    list_editable = ['full_name','schedule_week_count','initial_start_date']
    inlines = [
        EmployeeInlines,
        ShiftInlines,
    ]

@admin.register(TimePhase)
class TimePhaseAdmin(admin.ModelAdmin):

    def timeframe(self, obj):
        return f"until {obj.max_time.strftime('%H:%M')}"

    def shifts(self, obj):
        return ", ".join(list(obj.shifts.all().values_list('name',flat=True)))

    def get_rank(self, obj):
        return obj.position + 1

    fields = ['organization','name','full_name','max_time','position',]
    sortable_by = ['max_time']
    list_display = ['name','full_name','timeframe','shifts']
    readonly_fields = ['shifts']
    inlines = [ShiftInlines,]





class TrainingInline(admin.TabularInline):
    model = Training
    fields = ['employee','shift','is_available', 'sentiment_qual', 'sentiment_quant']
    extra = 1

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'employee':
            shift_id = request.resolver_match.kwargs['object_id']
            shift = Shift.objects.get(id=shift_id)
            kwargs['queryset'] = Employee.objects.filter(department=shift.department)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

@admin.register(Shift)
class ShiftAdmin(admin.ModelAdmin):

    def from_department(self, obj):
        return obj.department.organization.name + " / " + obj.department.name

    def on_weekdays(self, obj):
        return obj.weekdays

    list_display = ['name','slug','from_department','start_time','hours','on_weekdays','phase']
    list_editable = ['start_time','hours','phase']
    list_filter = ['department',]
    readonly_fields = ['slug']
    form = ShiftForm
    inlines = [TrainingInline,]



