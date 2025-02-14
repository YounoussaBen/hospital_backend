from celery import shared_task
from .models import DoctorNote, ActionableStep
from django.db import transaction

@shared_task
def process_doctor_note(note_id):
    """
    Processes a doctor's note to extract actionable steps via LLM integration.
    Cancels any previous pending actionable steps for the patient.
    """
    try:
        note = DoctorNote.objects.get(id=note_id)
    except DoctorNote.DoesNotExist:
        return

    # Cancel previous pending actionable steps for this patient
    ActionableStep.objects.filter(note__patient=note.patient, status='pending').update(status='cancelled')

    # Simulate LLM extraction; replace with a real API call as needed
    extracted_steps = simulate_llm_extraction(note.note_text)

    with transaction.atomic():
        for step in extracted_steps.get('checklist', []):
            ActionableStep.objects.create(
                note=note,
                step_type='checklist',
                description=step,
            )
        for step in extracted_steps.get('plan', []):
            ActionableStep.objects.create(
                note=note,
                step_type='plan',
                description=step,
                schedule={"frequency": "daily", "duration": 7}  # Example scheduling data
            )

def simulate_llm_extraction(note_text):
    """
    Simulate LLM extraction of actionable steps.
    Replace this function with a real LLM integration.
    """
    return {
        "checklist": ["Buy the prescription"],
        "plan": ["Take medication X daily for 7 days"]
    }
