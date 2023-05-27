from django.db import models, IntegrityError
from django.utils.text import slugify
import datetime as dt
from empl.models import TemplateSlot, PtoRequest


# Create your models here.


class Schedule(models.Model):
    year = models.IntegerField()
    num = models.IntegerField()
    department = models.ForeignKey('org.Department', on_delete=models.CASCADE)
    slug = models.SlugField(max_length=64)
    shift_list = models.ManyToManyField('org.Shift', related_name='schedules')
    employee_list = models.ManyToManyField('empl.Employee', related_name='schedules')
    tdoset_list = models.ManyToManyField('empl.TemplatedDayOffSet', related_name='schedules')
    pto_list = models.ManyToManyField('empl.PtoRequest', related_name='schedules')
    start_date = models.DateField()
    day_count = models.IntegerField()

    url = lambda self: f"/org/{self.department.organization.slug}/dept/{self.department.slug}/sch/{self.slug}/"

    def save(self, *args, **kwargs):
        created = self.pk is None
        if not self.slug:
            self.slug = slugify(str(self.year) + "-sch" + str(self.num))
        if created:
            self.day_count = self.department.schedule_week_count * 7
        super().save(*args,**kwargs)
        if created:
            self.employee_list.set(self.department.employees.filter(hire_date__lte=self.start_date, active=True))
            self.shift_list.set(self.department.shifts.filter(initial_start_date__lte=self.start_date,))
            for empl in self.employee_list.all():
                if empl.templated_day_off_sets.filter(active=True).exists():
                    self.tdoset_list.add(empl.templated_day_off_sets.get(active=True))
            self.versions.create(num=1)
            self.pto_list.set(PtoRequest.objects.filter(
                                    employee__in=self.employee_list.all(),
                                    date__in=self.versions.first().workdays.values('date')))

    def __str__(self): return f"{self.year} {self.num} {self.department}"

    def status(self):
        if self.versions.exists():
            return ["Discarded","Draft","Published"][max(list(self.versions.values_list('status',flat=True)))]
        return "NA"


class Version(models.Model):
    num = models.IntegerField()
    schedule = models.ForeignKey('Schedule', on_delete=models.CASCADE, related_name='versions')
    is_best = models.BooleanField(default=False)
    percent = models.FloatField(default=0.0)
    slug = models.SlugField(max_length=64)
    class StatusChoices(models.IntegerChoices):
        DISCARDED = 0, 'Discarded'
        DRAFT     = 1, 'Draft'
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
    show_percent =  property(lambda self: f"{round(self.percent*100,1)}%")
    slots: 'SlotManager' = property(lambda self: Slot.objects.filter(workday__version=self))

    class Actions:

        def set_templates(self,instance):
            n = 0
            for slot in instance.slots:
                if slot.template_employee:
                    slot.set_employee(slot.template_employee)
                    n += 1
            return n, instance


        def solve(self,instance):
            n = 0
            for slot in instance.slots.empty():
                if slot.option_count >= 1:
                    slot.actions.solve(slot)
                    n += 1
            print(n)
            return n, instance
    actions = Actions()


    def save(self,*args,**kwargs):
        created = self.pk is None
        if not self.slug:
            self.slug = slugify(self.schedule.slug + "-v" + str(self.num))
        if not created:
            self.percent = self.slots.filter(employee__isnull=False).count() / self.slots.count()
        super().save(*args,**kwargs)
        if created:
            print(self.schedule.day_count)
            date_list = [self.schedule.start_date + dt.timedelta(days=i) for i in range(self.schedule.day_count)]
            sd_id = 1
            for i in date_list:
                self.workdays.create(date=i, sd_id=sd_id)
                sd_id += 1

    def __str__(self): return f"{self.slug}"


class Workday(models.Model):

    date = models.DateField()
    version = models.ForeignKey('Version', on_delete=models.CASCADE, related_name='workdays')
    sd_id = models.IntegerField()
    wd_id = models.IntegerField()
    wk_id = models.IntegerField()
    prd_id = models.IntegerField()
    slug = models.SlugField(max_length=64)

    class Meta:
        ordering = ['date', 'version__num']


    url = property(lambda self: f"/org/{self.version.schedule.department.organization.slug}/" \
                       f"dept/{self.version.schedule.department.slug}/" \
                       f"sch/{self.version.schedule.slug}/" \
                       f"v/{self.version.num}/" \
                       f"wd/{self.date}/")

    letter = lambda self: "SMTWRFA"[int(self.date.strftime('%w'))]
    weekday = property(lambda self:int(self.date.strftime('%w')))
    weekday_display = property(lambda self:self.date.strftime('%A')[:3])


    def get_next(self) -> 'Workday':
        next_wd = self.version.workdays.filter(sd_id=self.sd_id+1)
        if next_wd.exists():
            return next_wd.first()
        return None
    def get_next_url(self) -> str:
        next_wd = self.version.workdays.filter(sd_id=self.sd_id+1)
        if next_wd.exists():
            return next_wd.first().url
        return "#"

    def get_previous(self) -> 'Workday':
        prev_wd = self.version.workdays.filter(sd_id=self.sd_id-1)
        if prev_wd.exists():
            return prev_wd.first()
        return None

    def get_previous_url(self) -> str:
        prev_wd = self.version.workdays.filter(sd_id=self.sd_id-1)
        if prev_wd.exists():
            return prev_wd.first().url
        return "#"

    def save(self,*args,**kwargs):
        created = self.pk is None
        if not self.slug:
            self.slug = slugify(self.date.strftime('%y-%m-%d') + "-v" + str(self.version.num))
        if not self.wk_id:
            self.wk_id = (self.sd_id - 1) // 7
        if not self.prd_id:
            self.prd_id = (self.sd_id - 1 ) // 14
        if not self.wd_id:
            self.wd_id = int(self.date.strftime('%w'))
        super().save(*args,**kwargs)
        if created:
            for i in self.version.schedule.shift_list.filter(weekdays__contains="SMTWRFA"[self.weekday]):
                self.slots.create(shift=i, workday=self)

    @property
    def pto_requests(self):
        from empl.models import PtoRequest
        return PtoRequest.objects.filter(date=self.date)

    @property
    def percent(self):
        if self.slots.count() == 0:
            return 0
        return int(self.slots.filled().count() / self.slots.count() * 100)

    def __str__(self): return f"{self.slug}"


class SlotManager(models.QuerySet):
    def empty(self):
        return self.filter(employee=None)
    def filled(self):
        return self.exclude(employee=None)
    def fills_with(self):
        return FillsWith.objects.filter(slot__in=self)
    def with_disliked_shifts(self):
        return self.filter(employee__trainings__sentiment_qual__lt=3)


class Slot(models.Model):

    shift = models.ForeignKey('org.Shift', on_delete=models.CASCADE, related_name='slots')
    workday = models.ForeignKey('Workday', on_delete=models.CASCADE, related_name='slots')
    employee = models.ForeignKey('empl.Employee', on_delete=models.CASCADE, related_name='slots', null=True,blank=True)
    slug = models.SlugField(max_length=64)
    conflicting_slots = models.ManyToManyField('Slot', related_name='conflicts', blank=True)
    option_count = models.IntegerField(default=0)
    template_employee = models.ForeignKey('empl.Employee', on_delete=models.CASCADE, related_name='templated_to', null=True,blank=True)
    class SlotStates(models.TextChoices):
        NORMAL = 'N', 'Normal'
        TURNAROUND = 'T', 'Turnaround'
        OVERTIME = 'O', 'Overtime'
        PTO_CONFLICT = 'P', 'PTO Conflict'
        TDO_CONFLICT = 'D', 'TDO Conflict'
        ONE_OFF = '1', 'One Off'
    state = models.CharField(max_length=1, choices=SlotStates.choices, default=SlotStates.NORMAL)
    is_one_off = models.BooleanField(default=False)

    class Meta:
        unique_together = (('shift', 'workday'),
                           ('workday','employee'),)
        ordering = ['workday__date', 'shift__start_time']


    url = property(lambda self: f"/org/{self.workday.version.schedule.department.organization.slug}/" \
                       f"dept/{self.workday.version.schedule.department.slug}/" \
                       f"sch/{self.workday.version.schedule.slug}/" \
                       f"v/{self.workday.version.num}/" \
                       f"wd/{self.workday.date}/" \
                       f"slot/{self.shift.name}/")

    class Actions:

        def solve(self,instance):
            instance.save()
            if instance.employee is None:
                employee = instance.fills_with.first().employee if instance.fills_with.exists() else None
                print(employee)
                if employee:
                    instance.set_employee(employee)
            instance.save()
            if instance.employee is not None:
                print(instance, instance.employee)
                return 1, instance

    actions = Actions()

    def on_tdo(self):
        sd_id = self.workday.sd_id
        tdo = []
        for employee in self.workday.version.schedule.tdoset_list.values_list('employee__slug','days'):
            if employee[1][sd_id-1] == 'T':
                tdo.append(employee[0])
        return self.workday.version.schedule.employee_list.filter(slug__in=tdo)

    def save(self, *args, **kwargs):
        from empl.models import PtoRequest
        created = self.pk is None
        if not self.slug:
            self.slug = slugify(self.workday.slug + "-" + self.shift.slug)
        if created:
            template_employee = TemplateSlot.objects.filter(
                slot_set__active=True, sd_id=self.workday.sd_id, shift=self.shift)
            if template_employee.exists():
                self.template_employee = template_employee.first().slot_set.employee
        if self.employee:
            if self.workday.get_previous():
                if self.workday.get_previous().slots.filter(employee=self.employee).exists():
                    has_previous = True
                else: has_previous = False
            else: has_previous = False
            if self.workday.get_next():
                if self.workday.get_next().slots.filter(employee=self.employee).exists():
                    has_next = True
                else: has_next = False
            else: has_next = False
            if has_previous: self.is_one_off = False
            elif has_next: self.is_one_off = False
            else: self.is_one_off = True
        if not self.employee: self.is_one_off = False
        try:
            super().save(*args,**kwargs)
        except IntegrityError:
            self.workday.slots.filter(employee=self.employee).exclude(pk=self.pk).update(employee=None)
            super().save(*args,**kwargs)
        if created:
            pto_reqs = PtoRequest.objects.filter(date=self.workday.date)
            trained = self.shift.trained.all().exclude(pk__in=pto_reqs.values('employee'))
            current = self.workday.version.schedule.employee_list.all()
            for empl in current.intersection(trained):
                fills_with =FillsWith.objects.create(employee=empl, slot=self)
                fills_with.save()
            if self.workday.sd_id != 1:
                conflicting = self.workday.get_previous().slots.filter(shift__phase__gt=self.shift.phase)
                for conflict in conflicting:
                    self.conflicting_slots.add(conflict)
                    conflict.conflicting_slots.add(self)
        self.option_count = self.fills_with.count()

    def __str__(self): return f"{self.workday.date.month}/{self.workday.date.day}[{self.shift.name}]({self.employee.initials if self.employee else '-'})"

    objects = SlotManager.as_manager()

    def set_employee(self, employee):
        from_employee = self.employee
        to_employee = employee
        self.employee = employee
        self.save()
        self.fills_with.all().update()

    def set_conflicting_slots(self):
        conflicting = self.workday.get_previous().slots.filter(shift__phase__gt=self.shift.time_phase)
        for conflict in conflicting:
            self.conflicting_slots.add(conflict)
            conflict.conflicting_slots.add(self)


class FillsWithManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().all()

    @property
    def allowed(self):
        return self.get_queryset().filter(
            exceeds_week_fte=False,
            exceeds_period_fte=False,
            other_on_day=False,
            other_on_conflicting=False)


class FillsWith(models.Model):

    employee = models.ForeignKey('empl.Employee', on_delete=models.CASCADE, related_name='fills_with')
    slot = models.ForeignKey('Slot', on_delete=models.CASCADE, related_name='fills_with')
    hours_in_week = models.IntegerField(default=0)
    hours_in_period = models.IntegerField(default=0)
    hours_needed_in_period = models.IntegerField(default=0)
    hours_needed_in_week = models.IntegerField(default=0)
    other_on_day = models.BooleanField(default=False)
    exceeds_week_fte = models.BooleanField(default=False)
    exceeds_period_fte = models.BooleanField(default=False)
    other_on_conflicting = models.BooleanField(default=False)
    is_allowed = models.BooleanField(default=True)
    is_assigned = models.BooleanField(default=False)
    has_tdo = models.BooleanField(default=False)
    has_pto = models.BooleanField(default=False)

    checks_ok = property(lambda self: not self.other_on_day \
                                      and not self.exceeds_week_fte \
                                      and not self.exceeds_period_fte \
                                      and not self.other_on_conflicting\
                                      and not self.has_tdo \
                                      and not self.has_pto )

    class Meta:
        unique_together = ('employee','slot')
        ordering = ('-hours_needed_in_period',)


    def save(self, *args, **kwargs):
        from django.db.models import Sum
        created = self.pk is None
        if PtoRequest.objects.filter(employee=self.employee, date=self.slot.workday.date).exists():
            self.has_pto = True
        tdo_set = self.slot.workday.version.schedule.tdoset_list.filter(employee=self.employee)
        if tdo_set.exists():
            if tdo_set.filter(days__contains=self.slot.workday.sd_id).exists():
                self.has_tdo = True
        self.hours_in_week = sum(list(Slot.objects.filter(
            workday__version=self.slot.workday.version,
            employee=self.employee,
            workday__wk_id=self.slot.workday.wk_id,).values_list('shift__hours', flat=True)))
        self.hours_in_period = sum(list(Slot.objects.filter(
            workday__version=self.slot.workday.version,
            employee=self.employee,
            workday__prd_id=self.slot.workday.prd_id,).values_list('shift__hours', flat=True)))
        self.hours_needed_in_period = (self.employee.fte * 80 ) - self.hours_in_period
        self.hours_needed_in_week = (self.employee.fte * 40 ) - self.hours_in_week
        if self.hours_in_week > self.employee.fte * 40 - self.slot.shift.hours:
            self.exceeds_week_fte = True
        else:
            self.exceeds_week_fte = False
        if self.hours_in_period > self.employee.fte * 80 - self.slot.shift.hours:
            self.exceeds_period_fte = True
        else:
            self.exceeds_period_fte = False
        if self.slot.conflicting_slots.filter(employee=self.employee).exists():
            self.other_on_conflicting = True
        else:
            self.other_on_conflicting = False
        if self.slot.workday.slots.filter(employee=self.employee).exclude(pk=self.slot.pk).exists():
            self.other_on_day = True
        else:
            self.other_on_day = False
        if self.other_on_day or self.exceeds_week_fte or self.exceeds_period_fte or self.other_on_conflicting:
            self.is_allowed = False
        else:
            self.is_allowed = True
        super().save(*args,**kwargs)

    def __str__(self): return f"{self.employee} fills with {self.slot}"

    objects = FillsWithManager()
