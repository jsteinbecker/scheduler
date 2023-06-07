from django.core.validators import MinValueValidator, MaxValueValidator, BaseValidator
from django.db import models
import datetime as dt
from django.utils.text import slugify
from .basemodels import ShiftBaseModel, DepartmentBaseModel

# Create your models here.
class Organization(models.Model):
    full_name = models.CharField(max_length=128, null=True)
    name      = models.CharField(max_length=64)
    slug      = models.SlugField(max_length=64, unique=True)
    linked_accounts = models.ManyToManyField('auth.User', related_name='organizations')


    def save(self,*args,**kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args,**kwargs)

    def __str__(self): return f"{self.name}"


class Department(DepartmentBaseModel):
    full_name = models.CharField(max_length=128, null=True)
    name = models.CharField(max_length=64)
    slug = models.SlugField(max_length=64)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='departments')
    schedule_week_count = models.IntegerField()
    initial_start_date = models.DateField()
    max_retrograde_hours = models.IntegerField(default=2)
    image_url = models.CharField(max_length=200, null=True, default="/static/img/ui/rph-workspace.png")

    url = property(lambda self: f"/org/{self.organization.slug}/dept/{self.slug}/")
    day_range = property(lambda self: range(1 , self.schedule_week_count * 7 + 1))
    schedule_day_count = property(lambda self: self.schedule_week_count * 7)

    class Meta:
        unique_together = ('organization','slug')

    def __str__(self): return f"{self.name} ({self.organization})"



    def get_next_start_date(self):
        if self.schedules.count() == 0:
            return self.initial_start_date
        return self.schedules.last().start_date + dt.timedelta(days=self.schedule_day_count)

    def start_dates(self):
        for i in range(100):
            yield self.initial_start_date + dt.timedelta(days=i*self.schedule_day_count)

    def start_dates_from_year(self, year):
        for i in self.start_dates():
            if i.year == year:
                yield i


class Training(models.Model):
    """
    Training(shift, employee, effective_date, )
    """

    shift = models.ForeignKey('org.Shift', on_delete=models.CASCADE, related_name='trainings')
    employee = models.ForeignKey('empl.Employee', on_delete=models.CASCADE, related_name='trainings')
    effective_date = models.DateField(auto_now_add=True)
    is_available = models.BooleanField(default=True)
    class QualitativeRating(models.IntegerChoices):
        STRONGLY_DISLIKE = 5
        DISLIKE = 4
        NEUTRAL = 3
        PREFER = 2
        STRONGLY_PREFER = 1
    sentiment_qual = models.PositiveSmallIntegerField(default=3, choices=QualitativeRating.choices,
                                                      help_text="The 'in general' value for how "
                                                                "the employee feels about this shift, "
                                                                "regardless of how they feel about other shifts.")
    sentiment_quant = models.PositiveSmallIntegerField(default=0,
                                                       help_text="The 'in comparison' value for how the employee "
                                                                 "feels about this shift, asking them to rank this "
                                                                 "shift against other shifts.")

    class Meta:
        ordering = ('-sentiment_qual', 'sentiment_quant')

    def __str__(self): return f"{self.shift}:{self.employee} TRAINING"


class TimePhase(models.Model):
    """
    TimePhase(name, full_name, position, max_time, organization)
    """

    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='time_phases', null=True)
    name = models.CharField(max_length=64)
    full_name = models.CharField(max_length=128, null=True)
    position = models.SmallIntegerField()
    max_time = models.TimeField()


    def __str__(self): return f"{self.name}"

    def save(self,*args,**kwargs):
        if not self.position:
            self.position = self.organization.time_phases.count() + 1
        super().save(*args,**kwargs)


class Shift(ShiftBaseModel):
    class WeekdayChoices(models.TextChoices):
        SUN = 'S', 'Sunday'
        MON = 'M', 'Monday'
        TUE = 'T', 'Tuesday'
        WED = 'W', 'Wednesday'
        THU = 'R', 'Thursday'
        FRI = 'F', 'Friday'
        SAT = 'A', 'Saturday'
    weekdays = models.CharField(max_length=7, choices=WeekdayChoices.choices, default="S,M,T,W,R,F,A")
    name = models.CharField(max_length=64)
    slug = models.SlugField(max_length=64, unique=True)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name="shifts")
    start_time = models.TimeField(default=dt.time(7))
    hours = models.IntegerField(choices=[(i,i) for i in range(2,14,2)],
                                default=10,
                                validators=[MinValueValidator(2), MaxValueValidator(24)])
    trained = models.ManyToManyField('empl.Employee', through='Training', related_name='shifts_trained')
    initial_start_date = models.DateField(default=dt.date(2017,1,1))
    phase = models.ForeignKey(TimePhase, on_delete=models.CASCADE, related_name='shifts', null=True)
    on_holidays = models.BooleanField(default=True)


    url = property(lambda self: f"/org/{self.department.organization.slug}/dept/{self.department.slug}/shift/{self.slug}")


    def __str__(self): return f"{self.name}"


class DepartmentNotification(models.Model):
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='notifications')
    level = models.CharField(max_length=64, choices=[('info','info'),('warning','warning'),('error','error')])
    message = models.TextField()
    date = models.DateField(auto_now_add=True)

    def __str__(self): return f"{self.department}:{self.message}"
