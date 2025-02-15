# tests/test_endpoints.py
import uuid

from datetime import datetime
from unittest.mock import patch, MagicMock
from django.urls import reverse
from rest_framework import status

from django.test import TestCase
from django.utils import timezone

from hospital.models import DoctorNote, ActionableStep, DoctorPatientAssignment
from hospital.services.llm import LLMService
from hospital.services.scheduler import SchedulerService
from config.testing.base import BaseAPITest

from account.factories import UserFactory
class DoctorPatientEndpointsTest(BaseAPITest):
    def setUp(self):
        self.doctor = UserFactory(role='doctor', email='doctor@example.com', first_name='Doc', last_name='Tor')
        self.patient = UserFactory(role='patient', email='patient@example.com', first_name='Pat', last_name='Ient')
        self.other_doctor = UserFactory(role='doctor', email='otherdoc@example.com', first_name='Other', last_name='Doc')
        super().setUp()

    def test_doctor_list_authenticated(self):
        url = reverse("doctor_list")
        # Authenticate as any user (e.g. a patient)
        self.client.force_authenticate(user=self.patient)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_patient_select_doctor_valid_selection(self):
        url = reverse("patient_select_doctor")
        self.client.force_authenticate(user=self.patient)
        data = {
            "doctor_ids": [str(self.doctor.id)],
            "action": "select"
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Check that the returned assignments include our selected doctor
        self.assertTrue(any(item["doctor"]["id"] == str(self.doctor.id) for item in response.data))
        # Also verify the assignment exists in the database
        self.assertTrue(
            DoctorPatientAssignment.objects.filter(doctor=self.doctor, patient=self.patient).exists()
        )

    def test_patient_select_doctor_invalid_user_role(self):
        url = reverse("patient_select_doctor")
        # Authenticate as a doctor (not a patient)
        self.client.force_authenticate(user=self.doctor)
        data = {
            "doctor_ids": [str(self.doctor.id)],
            "action": "select"
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_patient_select_doctor_invalid_doctor_id(self):
        url = reverse("patient_select_doctor")
        self.client.force_authenticate(user=self.patient)
        invalid_uuid = str(uuid.uuid4())  # Random UUID that does not exist
        data = {
            "doctor_ids": [invalid_uuid],
            "action": "select"
        }
        response = self.client.post(url, data, format="json")
        # Expect a 404 error because the doctor cannot be found.
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_patient_select_doctor_deselect(self):
        url = reverse("patient_select_doctor")
        self.client.force_authenticate(user=self.patient)
        # First, select the doctor.
        data_select = {
            "doctor_ids": [str(self.doctor.id)],
            "action": "select"
        }
        response_select = self.client.post(url, data_select, format="json")
        self.assertEqual(response_select.status_code, status.HTTP_200_OK)
        self.assertTrue(
            DoctorPatientAssignment.objects.filter(doctor=self.doctor, patient=self.patient).exists()
        )

        # Then, deselect the doctor.
        data_deselect = {
            "doctor_ids": [str(self.doctor.id)],
            "action": "deselect"
        }
        response_deselect = self.client.post(url, data_deselect, format="json")
        self.assertEqual(response_deselect.status_code, status.HTTP_200_OK)
        self.assertFalse(
            DoctorPatientAssignment.objects.filter(doctor=self.doctor, patient=self.patient).exists()
        )

    def test_patient_doctor_list_accessible_to_patient(self):
        url = reverse("patient_doctor_list")
        self.client.force_authenticate(user=self.patient)
        # Initially, the patient has no assignments.
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 0)

        # Create an assignment and try again.
        DoctorPatientAssignment.objects.create(doctor=self.doctor, patient=self.patient)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)

    def test_patient_doctor_list_not_accessible_to_non_patient(self):
        url = reverse("patient_doctor_list")
        # Authenticate as a doctor, which should not be allowed.
        self.client.force_authenticate(user=self.doctor)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


    def test_doctor_patient_list_accessible_to_doctor(self):
        url = reverse("doctor_patient_list")
        self.client.force_authenticate(user=self.doctor)
        # Initially, no patients assigned.
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 0)

        # Create an assignment and try again.
        DoctorPatientAssignment.objects.create(doctor=self.doctor, patient=self.patient)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)

    def test_doctor_patient_list_not_accessible_to_non_doctor(self):
        url = reverse("doctor_patient_list")
        # Authenticate as a patient.
        self.client.force_authenticate(user=self.patient)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
class LLMServiceTest(TestCase):
    """Unit tests for the LLM service."""
    
    def setUp(self):
        self.llm_service = LLMService()
        self.sample_note = "Patient needs to take aspirin daily for 7 days and get blood work done."
    
    @patch('httpx.AsyncClient.post')
    async def test_extract_actionable_steps_success(self, mock_post):
        # Mock successful API response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "candidates": [{
                "content": {
                    "parts": [{
                        "text": '{"checklist": [{"description": "Get blood work done"}], "plan": [{"description": "Take aspirin", "frequency": "daily", "duration": 7}]}'
                    }]
                }
            }]
        }
        mock_post.return_value = mock_response
        
        checklist, plan = await self.llm_service.extract_actionable_steps(self.sample_note)
        
        self.assertEqual(len(checklist), 1)
        self.assertEqual(len(plan), 1)
        self.assertEqual(checklist[0]["description"], "Get blood work done")
        self.assertEqual(plan[0]["description"], "Take aspirin")
    
    @patch('httpx.AsyncClient.post')
    async def test_extract_actionable_steps_api_error(self, mock_post):
        # Mock API error
        mock_post.side_effect = Exception("API Error")
        
        checklist, plan = await self.llm_service.extract_actionable_steps(self.sample_note)
        
        self.assertEqual(len(checklist), 0)
        self.assertEqual(len(plan), 0)

class SchedulerServiceTest(TestCase):
    """Unit tests for the scheduler service."""
    
    def setUp(self):
        self.scheduler = SchedulerService()
    
    def test_create_schedule(self):
        schedule = self.scheduler.create_schedule("daily", 7)
        
        self.assertEqual(schedule["frequency"], "daily")
        self.assertEqual(schedule["duration"], 7)
        self.assertTrue("start_date" in schedule)
        self.assertTrue("end_date" in schedule)
        self.assertEqual(schedule["completed_dates"], [])
        self.assertEqual(schedule["missed_dates"], [])
    
    def test_update_schedule(self):
        initial_schedule = self.scheduler.create_schedule("daily", 7)
        check_in_date = timezone.now()
        
        updated_schedule = self.scheduler.update_schedule(initial_schedule, check_in_date)
        
        self.assertEqual(len(updated_schedule["completed_dates"]), 1)
        self.assertEqual(
            datetime.fromisoformat(updated_schedule["completed_dates"][0]).date(),
            check_in_date.date()
        )

class DoctorNoteIntegrationTest(BaseAPITest):
    """Integration tests for the doctor note creation and processing flow."""
    
    def setUp(self):
        self.doctor = UserFactory(role='doctor')
        self.patient = UserFactory(role='patient')
        self.assignment = DoctorPatientAssignment.objects.create(
            doctor=self.doctor,
            patient=self.patient
        )
        super().setUp()
    
    @patch('hospital.services.llm.LLMService.extract_actionable_steps')
    @patch('hospital.tasks.schedule_check_reminder.delay')
    def test_create_note_with_steps(self, mock_schedule_task, mock_extract_steps):
        # Mock LLM response
        mock_extract_steps.return_value = (
            [{"description": "Get blood work"}],
            [{"description": "Take medication", "frequency": "daily", "duration": 7}]
        )
        
        url = reverse("doctor_note_create")
        
        self.client.force_authenticate(user=self.doctor)
        
        response = self.client.post(url, {
            'patient': str(self.patient.id),
            'noteText': 'Test note content'
        })
        self.assertEqual(response.status_code, 201)
        
        # Verify steps were created
        note = DoctorNote.objects.get(id=response.data['id'])
        steps = ActionableStep.objects.filter(note=note)
        
        self.assertEqual(steps.count(), 2)
        self.assertTrue(steps.filter(description="Get blood work").exists())
        self.assertTrue(steps.filter(description="Take medication").exists())
        
        # Verify scheduling task was called (e.g., for planned medication step)
        self.assertEqual(mock_schedule_task.call_count, 1)
