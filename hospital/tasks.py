from celery import shared_task
from django.db import transaction
from .models import DoctorNote, ActionableStep
from .services.llm import LLMService
from .services.scheduler import SchedulerService, schedule_check_reminder

from asgiref.sync import async_to_sync

@shared_task
def process_doctor_note(note_id: str) -> None:
    """
    Process a doctor's note to extract actionable steps via LLM integration.
    Cancels any previous pending actionable steps for the patient.
    """
    try:
        note = DoctorNote.objects.get(id=note_id)
    except DoctorNote.DoesNotExist:
        return

    # Cancel previous pending actionable steps for this patient
    ActionableStep.objects.filter(
        note__patient=note.patient, 
        status='pending'
    ).update(status='cancelled')

    llm_service = LLMService()
    scheduler_service = SchedulerService()
    
    # Synchronously call the asynchronous method
    checklist_items, plan_items = async_to_sync(llm_service.extract_actionable_steps)(note.note_text)
    
    with transaction.atomic():
        # Create checklist items (one-time tasks)
        for item in checklist_items:
            ActionableStep.objects.create(
                note=note,
                step_type='checklist',
                description=item['description'],
            )
        
        # Create plan items (scheduled tasks)
        for item in plan_items:
            schedule = scheduler_service.create_schedule(
                frequency=item.get('frequency', 'daily'),
                duration=item.get('duration', 7)
            )
            
            step = ActionableStep.objects.create(
                note=note,
                step_type='plan',
                description=item['description'],
                schedule=schedule
            )
            
            # Schedule the reminder task
            schedule_check_reminder.delay(str(step.id))