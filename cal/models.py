import datetime as dt

from django.db import models
from django.db.models import Max, F, Avg, Q
from django.utils.text import slugify

from empl.models import PtoRequest, DayTemplate, Employee
from org.models import Training
from .basemodels import SlotBaseModel, BaseVersionModel


# Create your models here.

class ScheduleManager(models.Manager):
    def create(self, *args, **kwargs):
        if not kwargs.get('slug'):
            kwargs['slug'] = slugify(str(kwargs['year']) + "-sch" + str(kwargs['num']))
        return super().create(*args, **kwargs)

    def get_queryset(self):
        return super().get_queryset().annotate(
            max_date=Max('workday__date')
        ).annotate(
            day_count=F('max_date') - F('start_date')
        )


class Schedule(models.Model):
    year = models.IntegerField()
    num = models.IntegerField(null=True, blank=True)
    department = models.ForeignKey('org.Department', on_delete=models.CASCADE, related_name='schedules')
    slug = models.SlugField(max_length=64)
    shifts = models.ManyToManyField('org.Shift', related_name='schedules')
    employees = models.ManyToManyField('empl.Employee', related_name='schedules')
    pto_requests = models.ManyToManyField('empl.PtoRequest', related_name='schedules')
    start_date = models.DateField()
    day_count = models.IntegerField()

    url = lambda self: f"/org/{self.department.organization.slug}/dept/{self.department.slug}/sch/{self.slug}/"

    def save(self, *args, **kwargs):
        created = self.pk is None
        if not self.slug:
            self.slug = slugify(str(self.year) + "-sch" + str(self.num))
        if created:
            self.day_count = self.department.schedule_week_count * 7
            self.year = self.start_date.year
            self.num = self.department.schedules.filter(year=self.year).count() + 1
            self.slug = slugify(str(self.year) + "-sch" + str(self.num))
        super().save(*args, **kwargs)
        if created:
            self.employees.set(self.department.employees.filter(hire_date__lte=self.start_date))
            self.shifts.set(self.department.shifts.filter(initial_start_date__lte=self.start_date, ))
            for empl in self.employees.all():
                if empl.day_templates.filter(state=DayTemplate.States.TDO).exists():
                    print(f"Creating TDO for {empl}")
            self.versions.create(num=1)
            self.pto_requests.set(PtoRequest.objects.filter(
                employee__in=self.employees.all(),
                date__in=self.versions.first().workdays.values('date')))

    def __str__(self):
        return f"{self.year} {self.num} {self.department}"

    def status(self):
        if self.versions.exists():
            return ["Discarded", "Draft", "Published"][max(list(self.versions.values_list('status', flat=True)))]
        return "NA"


class VersionManager(models.Manager):
    def create(self, *args, **kwargs):
        if not kwargs.get('slug'):
            kwargs['slug'] = slugify(str(kwargs['num']) + "-v" + str(kwargs['schedule'].num))
        return super().create(*args, **kwargs)

    def get_queryset(self):
        return super().get_queryset().annotate(
            n_unfavorables=F('slots__n_unfavorables'),
            n_mistemplated=F('slots__n_mistemplated'),
            n_disliked_one_offs=F('slots__n_disliked_one_offs'),
            n_disliked_shifts=F('slots__n_disliked_shifts'),
            n_empty=F('slots__n_empty'),
        )


class Version(BaseVersionModel):
    num = models.IntegerField()
    schedule = models.ForeignKey('Schedule', on_delete=models.CASCADE, related_name='versions')
    is_best = models.BooleanField(default=False)
    percent = models.FloatField(default=0.0)
    slug = models.SlugField(max_length=64)

    class StatusChoices(models.IntegerChoices):
        DISCARDED = 0, 'Discarded'
        DRAFT = 1, 'Draft'
        PUBLISHED = 2, 'Published'
    status = models.IntegerField(choices=StatusChoices.choices, default=StatusChoices.DRAFT)

    n_unfavorables = models.IntegerField(default=0)
    n_mistemplated = models.IntegerField(default=0)
    n_disliked_one_offs = models.IntegerField(default=0)
    n_disliked_shifts = models.IntegerField(default=0)
    n_empty = models.IntegerField(default=0)

    url = lambda self: f"/org/{self.schedule.department.organization.slug}/" \
                       f"dept/{self.schedule.department.slug}/" \
                       f"sch/{self.schedule.slug}/" \
                       f"v/{self.num}/"
    show_percent = property(lambda self: f"{round(self.percent * 100, 1)}%")
    slots: 'SlotManager' = property(lambda self: Slot.objects.filter(workday__version=self))


class Workday(models.Model):
    date    = models.DateField()
    version = models.ForeignKey('Version', on_delete=models.CASCADE, related_name='workdays')
    sd_id   = models.IntegerField()
    wd_id   = models.IntegerField()
    wk_id   = models.IntegerField()
    prd_id  = models.IntegerField()
    slug    = models.SlugField(max_length=64)

    class Meta:
        ordering = ['date', 'version__num']

    url = property(lambda self: f"/org/{self.version.schedule.department.organization.slug}/" \
                                f"dept/{self.version.schedule.department.slug}/" \
                                f"sch/{self.version.schedule.slug}/" \
                                f"v/{self.version.num}/" \
                                f"wd/{self.date}/")

    letter          = lambda self: "SMTWRFA"[int(self.date.strftime('%w'))]
    weekday         = property(lambda self: int(self.date.strftime('%w')))
    weekday_display = property(lambda self: self.date.strftime('%A')[:3])

    def has_next(self) -> bool:
        return self.version.workdays.filter(sd_id=self.sd_id + 1).exists()

    def get_next(self) -> 'Workday':
        next_wd = self.version.workdays.filter(sd_id=self.sd_id + 1)
        if next_wd.exists():
            return next_wd.first()
        return None

    def get_next_url(self) -> str:
        next_wd = self.version.workdays.filter(sd_id=self.sd_id + 1)
        if next_wd.exists():
            return next_wd.first().url
        return "#"

    def has_previous(self) -> bool:
        return self.version.workdays.filter(sd_id=self.sd_id - 1).exists()

    def get_previous(self) -> 'Workday':
        prev_wd = self.version.workdays.filter(sd_id=self.sd_id - 1)
        if prev_wd.exists():
            return prev_wd.first()
        return None

    def get_previous_url(self) -> str:
        prev_wd = self.version.workdays.filter(sd_id=self.sd_id - 1)
        if prev_wd.exists():
            return prev_wd.first().url
        return "#"

    def save(self, *args, **kwargs):
        created = self.pk is None
        if not self.slug:
            self.slug = slugify(self.date.strftime('%y-%m-%d') + "-v" + str(self.version.num))
        if not self.wk_id:
            self.wk_id = (self.sd_id - 1) // 7
        if not self.prd_id:
            self.prd_id = (self.sd_id - 1) // 14
        if not self.wd_id:
            self.wd_id = int(self.date.strftime('%w'))
        super().save(*args, **kwargs)
        if created:
            for i in self.version.schedule.shifts.filter(weekdays__contains="SMTWRFA"[self.weekday]):
                self.slots.create(shift=i, workday=self)


    @property
    def on_tdo(self):
        from empl.models import Employee, DayTemplate
        tdos = DayTemplate.objects.filter(pk__in=self.version.template_sets.values('day_templates__pk')
                                    ).filter(state=DayTemplate.States.TDO)
        if tdos.exists():
            return Employee.objects.filter(pk__in=tdos.values('employee__pk'))
        return Employee.objects.none()

    @property
    def on_pto(self):
        from empl.models import Employee
        ptos = PtoRequest.objects.filter(date=self.date, employee__in=self.version.schedule.employees.all())
        if ptos.exists():
            return Employee.objects.filter(pk__in=ptos.values('employee__pk'))
        return Employee.objects.none()

    @property
    def on_deck(self):
        on_workday = list(self.slots.filled().values_list('employee__pk', flat=True))
        on_pto = list(self.pto_requests.values_list('employee__pk', flat=True))
        on_tdo = list(self.on_tdo.values_list('pk', flat=True))
        return self.version.schedule.employees.exclude(pk__in=set(on_workday + on_pto + on_tdo))

    @property
    def percent(self):
        if self.slots.count() == 0:
            return 0
        return int(self.slots.filled().count() / self.slots.count() * 100)

    def __str__(self): return f"{self.slug}"


class SlotQuerySet(models.QuerySet):
    def empty(self):
        return self.filter(employee__isnull=True)

    def filled(self):
        return self.exclude(employee__isnull=True)

    def mistemplated(self):
        return self.filter(employee__isnull=False,
                           template_employee__isnull=False)\
                    .exclude(
                        employee=F('template_employee'))

    def fills_with(self) -> "FillsWithManager":
        return FillsWith.objects.filter(slot__in=self)

    def with_disliked_shifts(self):
        return self.filter(employee__trainings__sentiment_qual__lt=3)

    def with_unfavorables(self) -> "SlotManager":
        return self.exclude(shift__phase=F('employee__phase_pref'))

    def mistemplated(self) -> "SlotManager":
        return self.filter(employee__isnull=False, template_employee__isnull=False).exclude(
            employee=F('template_employee'))

    def employees(self) -> "EmployeeManager":
        return Employee.objects.filter(pk__in=self.values('employee__pk'))


class SlotManager(models.Manager):
    def get_queryset(self):
        return SlotQuerySet(self.model, using=self._db)

    def empty(self):
        return self.get_queryset().empty()

    def filled(self):
        return self.get_queryset().filled()

    def mistemplated(self):
        return self.get_queryset().mistemplated()

    @property
    def fills_with(self) -> "FillsWithManager":
        return self.get_queryset().fills_with()

    def with_disliked_shifts(self):
        return self.get_queryset().with_disliked_shifts()

    def unfavorables(self):
        return self.get_queryset().with_unfavorables()

    @property
    def employees(self) -> "EmployeeManager":
        return self.get_queryset().employees()


class Slot(SlotBaseModel):
    shift = models.ForeignKey('org.Shift', on_delete=models.CASCADE, related_name='slots')
    workday = models.ForeignKey('Workday', on_delete=models.CASCADE, related_name='slots')
    employee = models.ForeignKey('empl.Employee', on_delete=models.CASCADE, related_name='slots', null=True, blank=True)
    slug = models.SlugField(max_length=64)
    conflicting_slots = models.ManyToManyField('Slot', related_name='conflicts', blank=True)
    option_count = models.IntegerField(default=0)
    template_employee = models.ForeignKey('empl.Employee', on_delete=models.CASCADE, related_name='templated_to',
                                          null=True, blank=True)
    class SlotStates(models.TextChoices):
        EMPTY = 'E', 'Empty'
        NORMAL = 'N', 'Normal'
        TURNAROUND = 'T', 'Turnaround'
        BLOCKED_BY_PREV = "<", 'Blocked by Previous'
        BLOCKED_BY_NEXT = ">", 'Blocked by Next'
        OVERTIME = 'O', 'Overtime'
        UNFAVORABLE = 'U', 'Unfavorable'
        PTO_CONFLICT = 'P', 'PTO Conflict'
        TDO_CONFLICT = 'D', 'TDO Conflict'
        ONE_OFF = '1', 'One Off'
        MISTEMPLATED = 'M', 'Mistemplated'
        DISLIKED = 'S', 'Disliked'
        TRAINING = 'R', 'Training'

    state = models.JSONField(default=dict, blank=True)
    is_one_off = models.BooleanField(default=False)

    class Meta:
        unique_together = (('shift', 'workday'),
                           ('workday', 'employee'),)
        ordering = ['workday__date', 'shift__start_time']

    url = property(lambda self: f"/org/{self.workday.version.schedule.department.organization.slug}/" \
                                f"dept/{self.workday.version.schedule.department.slug}/" \
                                f"sch/{self.workday.version.schedule.slug}/" \
                                f"v/{self.workday.version.num}/" \
                                f"wd/{self.workday.date}/" \
                                f"slot/{self.shift.name}/")

    def is_not_allowed(self, employee=None):
        if employee is None:
            employee = self.employee
        # Check for any slots that match the conditions
        conflicting_slots = Slot.objects.filter(
            Q(workday=self.workday, workday__sd_id=self.workday.sd_id) |
            Q(workday=self.workday, workday__sd_id=self.workday.sd_id - 1, shift__phase__lt=self.shift.phase.position) |
            Q(workday=self.workday, workday__sd_id=self.workday.sd_id + 1, shift__phase__gt=self.shift.phase.position)
        ).filter(employee=employee,
                 employee__trainings__shift=self.shift,
                 employee__trainings__is_available=True)

        # Exclude the current self itself if it exists in the queryset
        conflicting_slots = conflicting_slots.exclude(id=self.id)

        return conflicting_slots.exists()

    def yield_all_allowed(self):
        for emp in self.workday.version.schedule.employees.all():
            if not self.is_not_allowed(emp):
                yield emp.pk

    def get_allowed(self):
        return Employee.objects.filter(pk__in=self.yield_all_allowed())

    def highest_priority_templates(self):
        from .slot.actions import get_highest_priority_template
        return get_highest_priority_template(self)

    def __str__(self):
        return f"{self.workday.date.month}/{self.workday.date.day}[{self.shift.name}]({self.employee.initials if self.employee else '-'})"

    objects = SlotManager()




    def set_conflicting_slots(self):
        conflicting = self.workday.get_previous().slots.filter(shift__phase__gt=self.shift.time_phase)
        for conflict in conflicting:
            self.conflicting_slots.add(conflict)
            conflict.conflicting_slots.add(self)


class FWStates(models.TextChoices):
    ALLOWED = 'A', 'Allowed'
    WEEK = 'W', 'Blocked by Week FTE'
    PERIOD = 'P', 'Blocked by Period FTE'
    SAME_WD = 'D', 'Blocked by Other on Day'
    PREV_WD = 'V', 'Blocked by Other on Conflicting'
    NEXT_WD = 'N', 'Blocked by Other on Conflicting'
    TDO = 'T', 'Blocked by TDO'
    PTO = 'O', 'Blocked by PTO'


class FillsWithManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().all()


class AllowedFillsWithManager(models.Manager):

    def get_queryset(self):
        return super().get_queryset().exclude(
            state__contains=FWStates.WEEK).exclude(
            state__contains=FWStates.PERIOD).exclude(
            state__contains=FWStates.SAME_WD).exclude(
            state__contains=FWStates.PREV_WD).exclude(
            state__contains=FWStates.NEXT_WD).exclude(
            state__contains=FWStates.TDO).exclude(
            state__contains=FWStates.PTO)


class FillsWith(models.Model):
    employee = models.ForeignKey('empl.Employee', on_delete=models.CASCADE, related_name='fills_with')
    slot = models.ForeignKey('Slot', on_delete=models.CASCADE, related_name='fills_with')
    hours_in_week = models.IntegerField(default=0)

    class States(models.TextChoices):
        ALLOWED = 'A', 'Allowed'
        WEEK = 'W', 'Blocked by Week FTE'
        PERIOD = 'P', 'Blocked by Period FTE'
        SAME_WD = 'D', 'Blocked by Other on Day'
        PREV_WD = 'V', 'Blocked by Other on Conflicting'
        NEXT_WD = 'N', 'Blocked by Other on Conflicting'
        TDO = 'T', 'Blocked by TDO'
        PTO = 'O', 'Blocked by PTO'
    state = models.CharField(max_length=10, choices=States.choices,
                             default=(States.ALLOWED))

    state_data = models.JSONField(default=dict, blank=True)

    checks_ok = property(lambda self: self.state == Slot.SlotStates.NORMAL)

    class Meta:
        ordering = ('state',)

    def __str__(self): return f"{self.employee} fills with {self.slot}"

    objects = FillsWithManager()
    allowed = AllowedFillsWithManager()


class Transaction(models.Model):
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE, related_name='transactions')
    event_time = models.DateTimeField(auto_now_add=True)
    version = models.ForeignKey('Version', on_delete=models.CASCADE, related_name='transactions')
    delta_n_unfavorables = models.IntegerField(default=0)
    delta_n_mistemplated = models.IntegerField(default=0)
    delta_n_disliked_one_offs = models.IntegerField(default=0)
    delta_n_disliked_shifts = models.IntegerField(default=0)
    delta_n_empty = models.IntegerField(default=0)

    class Meta:
        ordering = ('-event_time',)

    def __str__(self): return f"{self.employee} {self.slot} {self.hours} {self.date}"
