import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone
from config.utils.models import BaseModel
from django_cryptography.fields import encrypt

class DoctorPatientAssignment(BaseModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='assignments'
    )
    doctor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='patients'
    )
    assigned_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.patient.get_full_name()} assigned to {self.doctor.get_full_name()}"

class DoctorNote(BaseModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    doctor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='doctor_notes'
    )
    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='patient_notes'
    )
    note_text = encrypt(models.TextField())
    def __str__(self):
        return f"Note by {self.doctor.email} for {self.patient.email}"

class ActionableStep(BaseModel):
    TYPE_CHOICES = (
        ('checklist', 'Checklist'),
        ('plan', 'Plan'),
    )

    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    note = models.ForeignKey(
        DoctorNote, on_delete=models.CASCADE, related_name='actionable_steps'
    )
    step_type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    description = models.TextField()
    schedule = models.JSONField(blank=True, null=True)  # Store scheduling details (e.g., frequency, duration)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')

    def __str__(self):
        return f"{self.step_type} - {self.description[:20]}..."
