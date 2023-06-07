from django.db import models, IntegrityError
from django.db.models import Avg, Max, F, Value, OuterRef, Subquery, Q
import datetime as dt
from django.utils.text import slugify

from empl.models import Employee, DayTemplateSet


class SlotBaseModel(models.Model):
    """
    Base Model for all Slot Models
    ==============================
    """

    class Meta:
        abstract = True
        ordering = ['workday', 'start_time', 'version', 'employee',]
    class Actions:

        @staticmethod
        def solve(instance):
            instance.save() # type: Slot

            if instance.employee is None:
                on_deck = instance.workday.on_deck.values_list('pk', flat=True)
                on_pto = instance.workday.pto_requests.values_list('pk', flat=True)
                on_tdo = instance.workday.on_tdo.values_list('pk', flat=True)
                employees = Employee.objects.filter(pk__in=on_deck).exclude(
                    pk__in=on_pto).exclude(pk__in=on_tdo).order_by('trainings__sentiment_quant')
                for employee in employees:
                    if instance.workday.version.pay_period_monitors.filter(employee=employee,
                                                                           state='S',
                                                                           prd_id=instance.workday.prd_id).exists():
                        instance.set_employee(employee)
                        instance.save()

                        return 1, instance

                return 0, instance


    actions = Actions()


    def clear_employee(self):
        self.previous_employee = self.employee
        self.employee = None
        self.state['is_empty'] = True

    def check_employee(self, employee):
        if self.workday.pto_requests.filter(employee=employee).exists():
            return False
        if self.workday.on_tdo.filter(pk=employee.pk).exists():
            return False
        if self.workday.on_deck.filter(pk=employee.pk).exists():
            return True
        return False

    def set_employee(self, employee):
        from empl.models import EmployeePayPeriodMonitor

        from_employee = self.employee
        to_employee = employee

        if to_employee == None:
            self.clear_employee()
            return

        if self.workday.pto_requests.filter(employee=to_employee).exists():
            try:
                print("Trying to assign employee to slot that has a PTO Request for that day.")
                return
            except Exception("Cannot assign employee to slot that has a PTO Request for that day."):
                return

        if from_employee != None \
                and from_employee == self.template_employee \
                and to_employee != from_employee:
            raise Exception("Cannot assign employee to slot "
                            "that is templated to another employee "
                            "and no legitimate reason to break template.")

        # Perform Assignment
        if from_employee:
            if from_employee != to_employee:
                self.employee = to_employee
                self.save()
                self.fills_with.all().update()
        self.employee = to_employee
        if self.employee:
            self.state['is_empty'] = False

        # Get or Create PPM and Link Slot
        ppm = EmployeePayPeriodMonitor.objects.get_or_create(
            employee=to_employee, prd_id=self.workday.prd_id, version=self.workday.version, goal=to_employee.fte * 80)[
            0]
        ppm.slots.add(self)
        ppm.save()

        # Clear One-Off Status of Surrounding Slots
        if self.workday.has_previous():
            prev_slot = self.workday.get_previous().slots.filter(employee=to_employee)
            if prev_slot.exists():
                self.state['is_one_off'] = False
                self.is_one_off = False
        if self.workday.has_next():
            next_slot = self.workday.get_next().slots.filter(employee=to_employee)
            if next_slot.exists():
                self.state['is_one_off'] = False
                self.is_one_off = False

        self.save()
        self.fills_with.all().update()

    def save(self, *args, **kwargs):

        created = self.pk is None

        # Create Slug if None
        if not self.slug:
            self.slug = slugify(self.workday.slug + "-" + self.shift.slug)

        def create():
            from cal.models import DayTemplate
            # Find Active D-Directed Template
            template_employee = DayTemplate.objects.filter(
                state=DayTemplate.States.DEFINED_SLOT,
                collection__expiration_date__isnull=True,
                sd_id=self.workday.sd_id,
                shift=self.shift)
            if template_employee.exists():
                self.template_employee = template_employee.first().employee

        if created: create()

        def update_state():

            self.option_count = self.fills_with.count()
            if self.employee:
                SS = self.SlotStates
                if self.employee.trainings.filter(sentiment_qual__lt=3).exists():
                    self.state['is_untrained'] = True
                if self.workday.pto_requests.filter(employee=self.employee).exists():
                    self.state['is_pto_conflict'] = True
                if self.workday.on_tdo:
                    self.state['is_tdo_conflict'] = True

            def update_fills_with_conflict_slots():
                for fw in self.workday.slots.exclude(pk=self.pk).fills_with().filter(employee=self.employee):
                    fw.other_on_day = True
                    fw.is_allowed = False
                    fw.save()
                for fw in self.conflicting_slots.fills_with.filter(employee=self.employee):
                    fw.other_on_conflicting = True
                    fw.is_allowed = False
                    fw.save()

            update_fills_with_conflict_slots()

        if self.pk: update_state()

        if not self.employee:
            self.is_one_off = False

        try: super().save(*args, **kwargs)
        except IntegrityError:
            self.workday.slots.filter(employee=self.employee).exclude(pk=self.pk).update(employee=None)
            super().save(*args, **kwargs)

        def post_save_create():
            from cal.models import PtoRequest, FillsWith

            pto_reqs = PtoRequest.objects.filter(date=self.workday.date)
            # tdos = self.workday.version.template_sets.templates.filter(sd_id=self.workday.sd_id, state='T').values('employee')
            trained = self.shift.trained.all().exclude(pk__in=pto_reqs.values('employee'))
            current = self.workday.version.schedule.employees.all()

            for empl in current.intersection(trained):
                fills_with = FillsWith.objects.create(employee=empl, slot=self)
                fills_with.save()
            if self.workday.sd_id != 1:
                conflicting = self.workday.get_previous().slots.filter(shift__phase__gt=self.shift.phase)
                for conflict in conflicting:
                    self.conflicting_slots.add(conflict)
                    conflict.conflicting_slots.add(self)
                    conflict.save()

        if created: post_save_create()


    def check_slot(self, attr):
        def template_mismatch():
            if self.template_employee and self.employee:
                if self.template_employee == self.employee:
                    return
                elif self.template_employee != self.employee:
                    raise ValueError("Template Mismatch")
            return ValueError("Template Mismatch")

        if attr == 'template': return template_mismatch()


class BaseVersionModel(models.Model):
    class Meta:
        abstract = True

    class Actions:
        """VERSION ACTIONS:
        =======================

        ``set_templates``:  Assigns the schedule 'skeleton' based on the departments templates

        ``solve``:          Solves the schedule by assigning employees to slots
        """

        def set_templates(self, instance):
            from cal.models import PtoRequest
            n = 0
            for slot in instance.slots.empty():
                if slot.template_employee:
                    if PtoRequest.objects.filter(employee=slot.template_employee, date=slot.workday.date).exists():
                        pass
                    else:
                        slot.set_employee(slot.template_employee)
                        n += 1
            return n, instance

        @staticmethod
        def slot_in_generic_templates(instance: 'Version'):
            from cal.models import DayTemplate, Training
            n = 0
            templates = DayTemplate.objects.filter(
                collection__expiration_date__isnull=True,
                employee__in=instance.schedule.employees.all(),
                state=DayTemplate.States.GENERIC_SLOT)
            print(templates.count())
            for template in templates.order_by('?'):
                sd_id = template.sd_id
                shifts = template.shift_options.all()

                slots = instance.slots.empty().filter(workday__sd_id=sd_id, shift__in=shifts)
                slots = slots.annotate(
                    sentiment=Subquery(
                        Training.objects.filter(employee=template.employee, shift=OuterRef('shift'))[:1].values(
                            'sentiment_qual')
                    )
                )
                print(slots.order_by('-sentiment').values('slug', 'sentiment'))
                if slots.exists():
                    slot = slots.order_by('sentiment').first()
                    slot.set_employee(template.employee)
                    n += 1

            return n, instance

        @staticmethod
        def solve(instance, user, iterations=10):
            """VERSION-SOLVE
            =======================
            Solves the Versions empty slots by assigning employees to them"""
            n = 0
            for i in range(iterations):
                print(f'iteration #{i}')
                print(user)
                print(instance.slots.empty().count())
                empty_slots = instance.slots.filter(employee__isnull=True).order_by('n_options')
                for slot in empty_slots:
                    slot.actions.solve(slot)
                    if slot.employee is not None:
                        n += 1
            print(n)
            return n, instance

    actions = Actions()

    def save(self, *args, **kwargs):
        created = self.pk is None
        if not self.slug:
            self.slug = slugify(self.schedule.slug + "-v" + str(self.num))
        if not created:
            if self.slots.count() != 0:
                self.percent = self.slots.filter(employee__isnull=False).count() / self.slots.count()
            max_percent = self.schedule.versions.aggregate(max_percent=Max('percent'))['max_percent']
            if self.percent == max_percent:
                self.is_best = True
            else:
                self.is_best = False

        self.previous_n_unfavorables = self.n_unfavorables or None

        from cal.models import Slot

        self.n_unfavorables = self.slots.filter(state__is_unfavorable=True).count()

        self.previous_n_mistemplated = self.n_mistemplated or None
        self.n_mistemplated = self.slots.filter(state__is_mistemplated=True).count()

        self.previous_n_disliked_one_offs = self.n_disliked_one_offs or None
        self.n_disliked_one_offs = self.slots.filter(state__is_one_off=True).count()

        self.previous_n_disliked_shifts = self.n_disliked_shifts or None
        self.n_disliked_shifts = self.slots.filter(state__is_disliked=True).count()

        self.previous_n_empty = self.n_empty or None
        self.n_empty = self.slots.filter(employee__isnull=True).count()

        super().save(*args, **kwargs)

        if created:
            from empl.models import EmployeePayPeriodMonitor
            print(self.schedule.day_count)

            date_list = [ self.schedule.start_date \
                          + dt.timedelta(days=i) \
                          for i in range(self.schedule.day_count) ]
            sd_id = 1

            for i in date_list:
                self.workdays.create(date=i, sd_id=sd_id)
                sd_id += 1

            prd_id_values = set(self.workdays.values_list('prd_id', flat=True))

            for prd_id in prd_id_values:
                for employee in self.schedule.employees.all():

                    ppm = EmployeePayPeriodMonitor.objects.create(
                        employee=employee,
                        prd_id=prd_id,
                        version=self,
                        goal=employee.fte * 80,
                        hours=0)
                    ppm.save()

            for ts in DayTemplateSet.objects.filter(employee__department=self.schedule.department):
                self.template_sets.add(ts)

            self.save()


    def __str__(self):
        return f"{self.slug}"
