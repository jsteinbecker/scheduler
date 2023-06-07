from django.db import models
from django.utils.text import slugify


class DepartmentBaseModel (models.Model):

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args,**kwargs)


class ShiftManager (models.Manager):
    def excluded_on_weekday(self, weekday_id):
        return self.get_queryset().exclude(weekdays="SMTWRFSA"[weekday_id])


class ShiftBaseModel (models.Model):

    class Meta:
        abstract = True
    def save(self, *args, **kwargs):

        if not self.slug:
            self.slug = slugify(f"{self.name}-{self.department.name}")
        if not self.phase:
            self.phase = self._get_phase(self.start_time)

        super().save(*args, **kwargs)

    def _get_phase(self, date):
        phase = self.department.organization.time_phases.filter(max_time__gte=self.start_time).order_by('max_time')
        if phase.exists():
            return phase.first()

    def __str__(self):
        return self.name

    objects = ShiftManager()

