from django.contrib import admin
from .models import Organization, Department, Shift, Training, TimePhase, DepartmentNotification

from django import forms
from .forms import ShiftForm

class DeptNotificationInline(admin.StackedInline):
    model = DepartmentNotification
    extra = 0
    readonly_fields = ['department',]

class DepartmentInline(admin.TabularInline):
    model = Department
    fields = ['name','full_name','schedule_week_count','initial_start_date']

    show_change_link = True
    extra = 0

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.filter(organization__in=request.user.organizations.all())

class UserLinkInline(admin.TabularInline):
    model = Organization.linked_accounts.through
    fields = ['user', ]
    extra = 1

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.filter(organization__in=request.user.organizations.all())

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'organization':
            kwargs['queryset'] = Organization.objects.filter(linked_accounts=request.user)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    # make assigned links readonly while leaving the new ones editable
    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ['user', ]
        else:
            return []

class TimePhaseInlines(admin.TabularInline):
    fields = ['name','full_name','max_hour','organization']
    readonly_fields = ['organization']
    model = TimePhase
    extra = 0


@admin.register(Organization)
class OrgAdmin(admin.ModelAdmin):
    fields = ['name','full_name','all_departments']
    list_display = ['name','full_name','all_departments']
    list_editable = ['full_name']
    readonly_fields = ['all_departments']
    inlines = [TimePhaseInlines, UserLinkInline, DepartmentInline,]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.filter(linked_accounts=request.user)

    def all_departments(self, obj):
        return str(list(obj.departments.all().values_list('name',flat=True)))

from empl.models import Employee
class EmployeeInlines(admin.StackedInline):
    model = Employee
    fields = ['first_name','last_name','department','active','phase_pref', 'fte',]
    readonly_fields = ['department']
    show_change_link = True
    extra = 0

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.filter(department__organization__in=request.user.organizations.all())

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'department':
            kwargs['queryset'] = Department.objects.filter(organization__in=request.user.organizations.all())
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

class ShiftInlines(admin.TabularInline):
    model = Shift
    fields = ['name','department','start_time','hours','phase']
    readonly_fields = ['department','phase']
    extra = 0
    show_change_link = True
    show_full_result_count = True

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.filter(department__organization__in=request.user.organizations.all())

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'department':
            kwargs['queryset'] = Department.objects.filter(organization__in=request.user.organizations.all())
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

@admin.register(Department)
class DeptAdmin(admin.ModelAdmin):

    fields = ['name','full_name','organization',
              'template_week_count_part_time',
              'template_week_count_full_time',
              'schedule_week_count','initial_start_date','image_url']
    readonly_fields = ['shifts']
    list_display = ['__str__','full_name','organization','schedule_week_count','initial_start_date']
    list_editable = ['full_name','schedule_week_count','initial_start_date']
    inlines = [DeptNotificationInline, EmployeeInlines, ShiftInlines,]

@admin.register(TimePhase)
class TimePhaseAdmin(admin.ModelAdmin):

    def timeframe(self, obj):
        return f"until {obj.max_hour}:00"

    def shifts(self, obj):
        return ", ".join(list(obj.shifts.all().values_list('name',flat=True)))

    fields = ['organization','name','full_name','max_hour',]
    list_display = ['name','full_name','timeframe','shifts']
    readonly_fields = ['shifts']



class TrainingInline(admin.TabularInline):
    model = Training
    fields = ['employee','shift','is_available', 'sentiment_qual', 'sentiment_quant']
    extra = 1

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.filter(employee__department__organization__linked_accounts=request.user)

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















