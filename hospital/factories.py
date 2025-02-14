# tests/factories.py
import factory
from account.factories import UserFactory
from .models import DoctorNote, ActionableStep


class DoctorNoteFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = DoctorNote

    doctor = factory.SubFactory(UserFactory, role='doctor')
    patient = factory.SubFactory(UserFactory, role='patient')
    note_text = factory.Faker('sentence')

class ActionableStepFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ActionableStep

    note = factory.SubFactory(DoctorNoteFactory)
    step_type = 'checklist'
    description = factory.Faker('sentence')
    schedule = {}
    status = 'pending'