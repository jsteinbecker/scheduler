from django.contrib import admin
from .models import Schedule, Version, Workday, FillsWith, Slot
from django.contrib import admin
from django.db.models import Count, F
from django.utils.html import format_html


@admin.register(Schedule)
class ScheduleAdmin(admin.ModelAdmin):
    fieldsets = (
        (None, {
            'fields': ('year','num','department','slug',),
            'description': "Basics",
            'classes': ('grp-collapse',),
        }),
    )

    list_display_links = ['slug',]
    list_display = ['year','num','department','slug',]
    list_editable = ['year','num',]
    list_filter = ['department',]

class WorkdayInline(admin.StackedInline):
    model = Workday
    extra = 0
    fieldsets = (
        (None, {
            'fields': ('date','version',),
            'classes': ('grp-collapse',),
        }),
        ("ID Tags", {
            'fields': ('prd_id','wk_id','sd_id','percent',),
            'classes': ('grp-collapse',),
        }),
    )

    readonly_fields = ('percent','prd_id','wk_id','sd_id','date','version',)

    def employee_percentage(self, instance):
        total_slots = instance.workday.slots.count()
        filled_slots = instance.workday.slots.filter(employee__isnull=False).count()
        percentage = (filled_slots / total_slots) * 100 if total_slots != 0 else 0
        return f'{percentage:.2f}%'

    employee_percentage.short_description = 'Employee Percentage'


@admin.register(Version)
class VersionAdmin(admin.ModelAdmin):
    list_display = ['schedule',]
    list_filter = ['schedule',]
    search_fields = ['schedule__year', 'schedule__num', 'version']
    inlines = [WorkdayInline,]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.filter(schedule__department__organization__linked_accounts=request.user)



