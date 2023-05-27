import datetime

from django.db import models
from django.utils.text import slugify

# Create your models here.


class EmployeeManager(models.Manager):
    def get_queryset(self):  return super().get_queryset().all()
    def active(self):  return self.get_queryset().filter(active=True)
    def prn(self):  return self.get_queryset().filter(fte=0.0)
    def part_time(self):  return self.get_queryset().filter(fte__lt=1.0, fte__gt=0.0)
    def full_time(self):  return self.get_queryset().filter(fte=1.0)


class Employee(models.Model):
    first_name = models.CharField(max_length=64)
    last_name = models.CharField(max_length=64)
    initials = models.CharField(max_length=3)
    slug = models.SlugField(max_length=64, unique=True)
    department = models.ForeignKey('org.Department', on_delete=models.CASCADE, related_name='employees')
    linked_account = models.OneToOneField('auth.User', related_name='employee', on_delete=models.SET_NULL, null=True)
    fte = models.FloatField(default=1.0)
    hire_date = models.DateField(default=datetime.date(2018,4,11))
    active = models.BooleanField(default=True)
    phase_pref = models.ForeignKey('org.TimePhase', on_delete=models.SET_NULL, null=True, related_name='employees')
    class TemplateSizeChoices(models.IntegerChoices):
        WEEKS_2 = 2
        WEEKS_3 = 3
    template_size = models.IntegerField(choices=TemplateSizeChoices.choices, default=TemplateSizeChoices.WEEKS_2)
    trade_one_offs = models.BooleanField(default=True)


    url = property(lambda self: f"/org/{self.department.organization.slug}/dept/{self.department.slug}/empl/{self.slug}")

    def __str__(self): return f"{self.first_name} {self.last_name}"

    def save(self,*args,**kwargs):
        if not self.slug:
            self.slug = slugify(f"{self.first_name} {self.last_name}")
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

class TemplatedDayOff(models.Model):
    employee = models.ForeignKey('Employee', on_delete=models.CASCADE, related_name='templated_days_off')
    effective_date = models.DateField(auto_now_add=True)
    active = models.BooleanField(default=True)
    day_id = models.IntegerField()

    def __str__(self): return f"{self.employee} TDO"

    class Meta:
        unique_together = ('employee','day_id','active')

    def save(self,*args,**kwargs):
        if self.pk:
            if self.employee.templated_days_off.filter(active=True).count() > 1:
                self.employee.templated_days_off.filter(active=True).exclude(pk=self.pk).update(active=False)
        super().save(*args,**kwargs)


class TemplatedDayOffSet(models.Model):
    employee = models.ForeignKey('Employee', on_delete=models.CASCADE, related_name='templated_day_off_sets')
    effective_date = models.DateField(auto_now_add=True)
    active = models.BooleanField(default=True)
    days = models.CharField(max_length=7*12)

    week_repr = property(lambda self: [self.days[i:i+7] for i in range(0,len(self.days),7)])
    day_list = property(lambda self: [i+1 for i in range(len(self.days)) if self.days[i] == 'T'])

    def __str__(self): return f"{self.employee} TDOSet"

    def save(self,*args,**kwargs):
        if not self.days:
            n = self.employee.department.schedule_week_count * 7
            self.days = 'F' * n
        if self.employee.templated_day_off_sets.filter(active=True).count() > 1:
            self.employee.templated_day_off_sets.filter(active=True).update(active=False)
        super().save(*args,**kwargs)



    def add_day(self, day_id):
        self.days = self.days[:day_id-1] + 'T' + self.days[day_id:]
        self.save()


class PtoManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().all()


class PtoRequest(models.Model):
    employee = models.ForeignKey('Employee', on_delete=models.CASCADE, related_name='pto_requests')
    date = models.DateField()
    violated = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    workdays = models.ManyToManyField('cal.Workday', related_name='pto_requests')

    def __str__(self): return f"PTOReq: {self.employee}({self.date})"

    class Meta:
        unique_together = ('employee','date')


class TemplateSlotSet(models.Model):
    employee = models.ForeignKey('Employee', on_delete=models.CASCADE, related_name='template_slot_sets')
    effective_date = models.DateField(auto_now_add=True)
    active = models.BooleanField(default=True)


    def __str__(self): return f"{self.employee} {self.effective_date}"

    def save(self, *args, **kwargs):
        created = self.pk is None
        super().save(*args,**kwargs)
        if created:
            self.assignments = {i:None for i in range(1, self.employee.department.schedule_week_count*7+1)}
            self.save()

    class Meta:
        unique_together = ('employee','effective_date','active')


class GenericSlotTemplate(models.Model):
    sd_id = models.IntegerField()
    slot_set = models.ForeignKey('TemplateSlotSet', on_delete=models.CASCADE, related_name='templates')

    class Meta:
        abstract = True
        unique_together = ('sd_id','slot_set')
        ordering = ('sd_id',)

    def __str__(self): return f"{self.slot_set.employee} D#{self.sd_id}"

class TemplateSlot(GenericSlotTemplate):
    shift = models.ForeignKey('org.Shift', on_delete=models.CASCADE, related_name='templates', null=True)

