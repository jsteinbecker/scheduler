from unittest import TestCase
from empl.tests import NCMCTestCase
from sch.models import Version, Department, Employee, Schedule, Workday, Slot

class TestSlotBaseModel(NCMCTestCase):

    def setUp(self):
        super().setUp()

    def test_check_slot(self):
        cpht = Department.objects.get(name='CPhT')
        sch = cpht.schedules.create(start_date='2023-02-05')
        sch.save()
        ver = sch.versions.first()

        slots = ver.slots.all()
        day_slot_cts = []
        for slot in slots:
            day_slot_cts.append(slot.fills_with.count())
        print(day_slot_cts)

        slot_with_template = slots[18]
        print(slot_with_template)

        josh = Employee.objects.get(first_name='Josh')
        sabrina = Employee.objects.get(first_name='Sabrina')

        slot_with_template.template_employee = Employee.objects.first()
        slot_with_template.employee = sabrina
        print(josh, josh.shifts_trained.all())

        print('-'*30)
        slot_with_template.save()
        print("TEMPLATED:", slot_with_template.template_employee)
        print("ACTUAL:", slot_with_template.employee)

        slot_with_template.save()

        try: slot_with_template.check_slot('template')
        except Exception as e:
            print(f"*** {e} ***")
            assert str(e) == 'Template Mismatch'
            print('-'*30)

        print()






