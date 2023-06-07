import datetime

from django.db import models
import datetime as dt
from django.utils.text import slugify


class EmployeeQuerySet(models.QuerySet):
    def active(self):  return self.filter(active=True)
    def prn(self) -> "EmployeeManager" :  return self.filter(fte=0.0)
    def part_time(self):  return self.filter(fte__lt=1.0, fte__gt=0.0)
    def full_time(self):  return self.filter(fte=1.0)

class EmployeeManager(models.Manager):
    def get_queryset(self):  return EmployeeQuerySet(self.model, using=self._db)
    def active(self):  return self.get_queryset().active()
    def prn(self) :  return self.get_queryset().prn()
    def part_time(self):  return self.get_queryset().part_time()
    def full_time(self):  return self.get_queryset().full_time()


class Employee(models.Model):
    """
    Employee(first_name, last_name, initials, department, fte, hire_date, active, phase_pref, template_size)
    """
    first_name = models.CharField(max_length=64)
    last_name  = models.CharField(max_length=64)
    name       = models.CharField(max_length=128, null=True)
    initials   = models.CharField(max_length=3)
    user       = models.OneToOneField('auth.User', on_delete=models.SET_NULL, null=True, related_name='profile')
    slug       = models.SlugField(max_length=64, unique=True)
    department = models.ForeignKey('org.Department', on_delete=models.CASCADE, related_name='employees')
    fte        = models.FloatField(default=1.0)
    hire_date  = models.DateField(default=datetime.date(2018,4,11))
    active     = models.BooleanField(default=True)
    phase_pref = models.ForeignKey('org.TimePhase', on_delete=models.SET_NULL, null=True, related_name='employees',
                                   help_text="The time phase that the employee prefers to work.")
    std_slot_size = models.IntegerField(default=10, help_text="The Hour value of a standard shift, this ensures that employees are "
                                                                "Scheduled the amount of hours they deserve.")
    pto_hours_size = models.IntegerField(default=10, help_text="The Hour value of a PTO day, this ensures that employees are "
                                                              "Scheduled the amount of hours they deserve.")
    class TemplateSizeChoices(models.IntegerChoices):
        WEEKS_2 = 2, "2-Week Cycle"
        WEEKS_3 = 3, "3-Week Cycle"
    template_size = models.IntegerField(choices=TemplateSizeChoices.choices, default=TemplateSizeChoices.WEEKS_2,
                                        help_text="Template Size determines the frequency of repetition on "
                                                   "assigning a template to schedule." \
                                                   "If the employee is to work every other weekend, " \
                                                   "for example, a 2-week size would be appropriate.")
    trade_one_offs = models.BooleanField(default=True)

    url = property(lambda self: f"/org/{self.department.organization.slug}/dept/{self.department.slug}/empl/{self.slug}")

    def __str__(self): return f"{self.first_name} {self.last_name[0]}"

    def save(self,*args,**kwargs):
        if not self.slug:
            self.slug = slugify(f"{self.first_name} {self.last_name}")
        if not self.name:
            self.name = f"{self.first_name} {self.last_name}"
        if self.initials == '':
            initials = f"{self.first_name[0]}{self.last_name[0]}"
            if self.department.employees.filter(initials=initials):
                i = 2
                while self.department.employees.filter(initials=f"{initials}+{i}").count() > 0:
                    i += 1
                initials = f"{initials}{i}"
            self.initials = initials
        super().save(*args,**kwargs)

    objects = EmployeeManager()


class PtoManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().all()

    def employees(self):
        return self.get_queryset().values('employee').distinct()


class PtoRequest(models.Model):
    employee    = models.ForeignKey('Employee', on_delete=models.CASCADE, related_name='pto_requests')
    date        = models.DateField()
    violated    = models.BooleanField(default=False)
    created_at  = models.DateTimeField(auto_now_add=True)
    workdays    = models.ManyToManyField('cal.Workday', related_name='pto_requests')
    wk_id       = models.IntegerField(null=True)
    prd_id      = models.IntegerField(null=True)


    def __str__(self): return f"PTOReq: {self.employee}({self.date})"

    class Meta:
        unique_together = ('employee','date'),

    objects = PtoManager()

    def save(self,*args,**kwargs):
        if not self.wk_id:
            self.wk_id = self.date.strftime("%-U")
        if not self.prd_id:
            self.prd_id = int(self.date.strftime("%-U")) // 2 + 1
        super().save(*args,**kwargs)


class DayTemplateManager(models.Manager):
    def get_queryset(self):  return super().get_queryset().all()
    def primary(self):  return self.get_queryset().filter(primary_cycle=True)
    def secondary(self):  return self.get_queryset().filter(primary_cycle=False)


class DayTemplate(models.Model):
    employee        = models.ForeignKey('Employee', on_delete=models.CASCADE, related_name='day_templates')
    sd_id           = models.IntegerField()
    primary_cycle   = models.BooleanField(default=False)
    class States(models.TextChoices):
        BASE_AVAILABLE  = "A", "Base Available"
        DEFINED_SLOT    = 'D', "Defined Slot"
        GENERIC_SLOT    = 'G', "Generic Slot"
        TDO             = "T", "Templated Day Off"
    state           = models.CharField(max_length=1, choices=States.choices, default=States.BASE_AVAILABLE)
    shift           = models.ForeignKey('org.Shift', on_delete=models.CASCADE, null=True, related_name='day_templates')
    shift_options   = models.ManyToManyField('org.Shift', related_name='day_template_options')
    collection      = models.ForeignKey('DayTemplateSet', on_delete=models.CASCADE, null=True, related_name='day_templates')
    cycle_analog_of = models.ForeignKey('self', related_name='analogs', on_delete=models.CASCADE, null=True)

    def __str__(self): return f"{self.employee} DT"

    class Meta:
        unique_together = ('employee','sd_id','collection')

    def change_state(self):
        if self.state == 'A': self.state = 'D'
        elif self.state == 'D': self.state = 'G'; self.shift = None
        elif self.state == 'G': self.state = 'T'; self.shift_options.clear()
        elif self.state == 'T': self.state = 'A'

    objects = DayTemplateManager()


class DayTemplateSetManager(models.Manager):
    def get_queryset(self):  return super().get_queryset().all()
    def current(self):  return self.get_queryset().filter(expiration_date__isnull=True)
    def future(self):  return self.get_queryset().filter(expiration_date__gt=dt.date.today())
    def past(self):  return self.get_queryset().filter(expiration_date__lt=dt.date.today())

    def templates(self):
        return self.get_queryset().values('versions__day_templates__pk').distinct()

class DayTemplateSet(models.Model):
    employee        = models.ForeignKey('Employee', on_delete=models.CASCADE, related_name='day_template_sets')
    effective_date  = models.DateField(auto_now_add=True)
    expiration_date = models.DateField(null=True)
    is_active       = models.BooleanField(default=True)
    versions        = models.ManyToManyField('cal.Version', related_name='template_sets')

    class Meta:
        unique_together = ('employee','effective_date')

    def __str__(self): return f"{self.employee} DTSet"

    objects = DayTemplateSetManager()


class EmployeePayPeriodMonitorQuerySet(models.QuerySet):
    def seeking(self):  return self.filter(state='S')
    def inactive(self):  return self.filter(state='I')
    def polling(self):  return self.filter(state='P')


class EmployeePayPeriodMonitorManager(models.Manager):
    def get_queryset(self):  return EmployeePayPeriodMonitorQuerySet(self.model, using=self._db)
    def seeking(self):  return self.get_queryset().seeking()
    def inactive(self):  return self.get_queryset().inactive()
    def polling(self):  return self.get_queryset().polling()


class EmployeePayPeriodMonitor(models.Model):
    employee = models.ForeignKey('Employee', on_delete=models.CASCADE, related_name='pay_period_monitors')
    version = models.ForeignKey('cal.Version', on_delete=models.CASCADE, related_name='pay_period_monitors')
    prd_id = models.SmallIntegerField()
    class States(models.TextChoices):
        SEEKING = "S", "Seeking"
        INACTIVE = "I", "Inactive"
        POLLING = "P", "Polling"
    state = models.CharField(max_length=1, choices=States.choices, default=States.SEEKING)
    goal = models.PositiveSmallIntegerField(default=80)
    hours = models.IntegerField(default=0)
    slots = models.ManyToManyField('cal.Slot', related_name='prd_monitors')

    def __str__(self): return f"{self.employee} PPM"

    def save(self,*args,**kwargs):
        if not self.prd_id:
            self.prd_id = int(self.version.workdays.first().date.strftime("%-U")) // 2 + 1
        super().save(*args,**kwargs)
        if not self.week_monitors.exists():
            wk_id1 = self.prd_id * 2 - 1
            wk_id2 = self.prd_id * 2
            self.week_monitors.create(wk_id=wk_id1, goal=self.goal // 2, employee=self.employee, version=self.version)
            self.week_monitors.create(wk_id=wk_id2, goal=self.goal // 2, employee=self.employee, version=self.version)


    def state_icon(self):
        if self.state == 'S': return "mdi:eye"
        elif self.state == 'I': return "mdi:eye-off"
        elif self.state == 'P': return "solar:hand-stars-bold"

    objects = EmployeePayPeriodMonitorManager()





class EmployeeWeekMonitor(models.Model):
    employee = models.ForeignKey('Employee', on_delete=models.CASCADE, related_name='week_monitors')
    version = models.ForeignKey('cal.Version', on_delete=models.CASCADE, related_name='week_monitors')
    wk_id = models.SmallIntegerField()
    goal = models.PositiveSmallIntegerField(default=40)
    hours = models.IntegerField(default=0)
    class States(models.TextChoices):
        SEEKING = "S", "Seeking"
        INACTIVE = "I", "Inactive"
        POLLING = "P", "Polling"
    state = models.CharField(max_length=1, choices=States.choices, default=States.SEEKING)
    slots = models.ManyToManyField('cal.Slot', related_name='wk_monitors')
    period_monitor = models.ForeignKey('EmployeePayPeriodMonitor', on_delete=models.CASCADE, related_name='week_monitors', null=True)

    def __str__(self): return f"{self.employee} WKM {self.version.schedule.year}.{self.wk_id}"



    def state_icon(self):
        if self.state == 'S': return "mdi:eye"
        elif self.state == 'I': return "mdi:eye-off"
        elif self.state == 'P': return "solar:hand-stars-bold"
