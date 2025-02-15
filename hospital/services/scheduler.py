from datetime import datetime, timedelta
from typing import Dict, Optional
from celery import shared_task
from django.utils import timezone
from hospital.models import ActionableStep

class SchedulerService:
    """Service to handle scheduling and managing actionable steps."""
    
    @staticmethod
    def create_schedule(frequency: str, duration: int) -> Dict:
        """
        Create a schedule configuration for an actionable step.
        
        Args:
            frequency: How often the step should be performed (e.g., 'daily', 'weekly')
            duration: How long the schedule should continue (in days)
            
        Returns:
            Dict containing schedule configuration
        """
        now = timezone.now()
        return {
            "frequency": frequency,
            "duration": duration,
            "start_date": now.isoformat(),
            "end_date": (now + timedelta(days=duration)).isoformat(),
            "completed_dates": [],
            "missed_dates": []
        }
    
    @staticmethod
    def update_schedule(schedule: Dict, check_in_date: Optional[datetime] = None) -> Dict:
        """
        Update a schedule based on check-in status.
        
        Args:
            schedule: The current schedule configuration
            check_in_date: The date of check-in (defaults to now)
            
        Returns:
            Updated schedule configuration
        """
        if check_in_date is None:
            check_in_date = timezone.now()
            
        schedule['completed_dates'].append(check_in_date.isoformat())
        
        # If there were any missed dates before this check-in, extend the end date
        missed_count = len(schedule.get('missed_dates', []))
        if missed_count > 0:
            end_date = datetime.fromisoformat(schedule['end_date'])
            schedule['end_date'] = (end_date + timedelta(days=missed_count)).isoformat()
            
        return schedule

@shared_task
def schedule_check_reminder(step_id: str) -> None:
    """
    Celery task to check if a reminder needs to be sent and schedule the next one.
    
    Args:
        step_id: The ID of the ActionableStep to check
    """
    try:
        step = ActionableStep.objects.get(id=step_id)
        if step.status != 'pending':
            return
            
        schedule = step.schedule
        if not schedule:
            return
            
        now = timezone.now()
        start_date = datetime.fromisoformat(schedule['start_date'])
        end_date = datetime.fromisoformat(schedule['end_date'])
        
        if now > end_date:
            step.status = 'completed'
            step.save()
            return
            
        # Check if today's reminder was missed
        today = now.date()
        if schedule['frequency'] == 'daily':
            if today not in [datetime.fromisoformat(d).date() for d in schedule['completed_dates']]:
                schedule['missed_dates'].append(now.isoformat())
                step.schedule = schedule
                step.save()
        
        # Schedule next check based on frequency
        next_check = now + timedelta(days=1)  # Default to daily
        schedule_check_reminder.apply_async(
            args=[step_id],
            eta=next_check
        )
        
    except ActionableStep.DoesNotExist:
        pass  # Step was deleted or doesn't exist
    except Exception as e:
        print(f"Error in schedule_check_reminder: {e}")