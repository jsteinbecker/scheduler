from django.contrib import admin
from django.utils.safestring import mark_safe

from .models import Schedule, Version, Workday, FillsWith, Slot, Transaction
from django.contrib import admin
from django.db.models import Count, F
from django.utils.html import format_html

class CalInlines:
    class WorkdayInline(admin.TabularInline):
        model = Workday
        extra = 0
        fieldsets = (
            (None, {
                'fields': ('date', 'version',),
                'classes': ('grp-collapse',),
            }),
            ("ID Tags", {
                'fields': ('ids', 'percent',),
                'classes': ('grp-collapse',),
            }),
        )

        readonly_fields = ('percent', 'date', 'version', 'ids')

        def ids(self, instance):
            return mark_safe( f"<i style='font-size:7pt; font-weight:200;'>"
                              f"PayPrd {instance.prd_id} <br/> Wk {instance.wk_id} <br/> Day {instance.sd_id}"
                              f"</i>" )

        ids.short_description = 'ID Tags'

        def employee_percentage(self, instance):
            total_slots = instance.workday.slots.count()
            filled_slots = instance.workday.slots.filter(employee__isnull=False).count()
            percentage = (filled_slots / total_slots) * 100 if total_slots != 0 else 0
            return f'{percentage:.2f}%'

        employee_percentage.short_description = 'Employee Percentage'

    class VersionInline(admin.TabularInline):
        model = Version
        extra = 0
        fields = ('slug', 'num', 'percent_display')
        readonly_fields = ('slug', 'num','percent_display')
        show_change_link = True

        def percent_display(self, obj):
            return f'{obj.percent * 100:.1f}%'

        percent_display.short_description = 'Percent Filled'

@admin.register(Schedule)
class ScheduleAdmin(admin.ModelAdmin):
    fieldsets = (
        ("Basics", {
            'fields': ('year','num_display','department',),
            'description': "Basic information about the schedule.",
            'classes': ('grp-collapse',),
        }),
        ("ID", {
            'fields': ('slug_display',),
            'classes': ('grp-collapse',),
        }),
        ("Versions", {
            'fields': ('version_count',),
        }),
        ("View on Site", {
            'fields': ('view_on_site',),
            'classes': ('grp-collapse',),
        })
    )

    def version_count(self, obj):
        return obj.versions.count()

    readonly_fields = ('slug_display','version_count','num_display','view_on_site')
    def slug_display(self, obj):
        return obj.slug.upper()

    slug_display.short_description = 'Slug (ID)'

    def view_on_site(self, obj):
        return format_html(f"<a href='{obj.url()}' target='_blank'>View on Site</a>")

    list_display_links = ['slug',]
    list_display = ['slug','year','num_display','department',]
    list_filter = ['department',]
    inlines = [CalInlines.VersionInline,]

    def num_display(self, obj):
        return f"#{obj.num}"

    num_display.short_description = 'Schedule Number'


@admin.register(Version)
class VersionAdmin(admin.ModelAdmin):
    list_display = ['schedule','num','percent_display','is_best']
    list_filter = ['schedule__department','schedule',]
    search_fields = ['schedule__department','schedule__year', 'schedule__num', 'version']
    inlines = [CalInlines.WorkdayInline,]

    def percent_display(self, obj):
        return f'{obj.percent * 100:.1f}%'

    percent_display.short_description = 'Percent Filled'





