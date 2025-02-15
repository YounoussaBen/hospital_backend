import json
import uuid
from datetime import datetime
from unittest.mock import patch, AsyncMock, MagicMock

from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from asgiref.sync import async_to_sync

from config.testing.base import BaseAPITest
from account.factories import UserFactory
from hospital.models import DoctorPatientAssignment, DoctorNote, ActionableStep
from hospital.services.llm import LLMService
from hospital.services.scheduler import SchedulerService

# ------------------------------
# Tests for the Doctor List Endpoint
# ------------------------------
class TestDoctorListEndpoint(BaseAPITest):
    def setUp(self):
        super().setUp()
        self.patient = UserFactory(role='patient')
        self.doctor1 = UserFactory(role='doctor')
        self.doctor2 = UserFactory(role='doctor')
        self.client.force_authenticate(user=self.patient)

    def test_doctor_list_paginated(self):
        url = reverse("doctor_list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Check if response is paginated.
        if "results" in response.data:
            self.assertIn("count", response.data)
            self.assertEqual(response.data["count"], 2)
            self.assertEqual(len(response.data["results"]), 2)
        else:
            self.assertEqual(len(response.data), 2)

# ------------------------------
# Tests for the Patient Select Doctor Endpoint
# ------------------------------
class TestPatientSelectDoctorEndpoint(BaseAPITest):
    def setUp(self):
        super().setUp()
        self.patient = UserFactory(role='patient')
        self.doctor = UserFactory(role='doctor')
        self.other_doctor = UserFactory(role='doctor')
        self.client.force_authenticate(user=self.patient)

    def test_select_doctor_success(self):
        url = reverse("patient_select_doctor")
        data = {"doctor_ids": [str(self.doctor.id)], "action": "select"}
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Handle paginated and non-paginated responses.
        assignments = response.data["results"] if "results" in response.data else response.data
        self.assertTrue(
            any(assignment["doctor"]["id"] == str(self.doctor.id) for assignment in assignments)
        )
        self.assertTrue(
            DoctorPatientAssignment.objects.filter(doctor=self.doctor, patient=self.patient).exists()
        )

    def test_select_doctor_invalid_role(self):
        # Authenticate as a doctor rather than a patient.
        self.client.force_authenticate(user=self.doctor)
        url = reverse("patient_select_doctor")
        data = {"doctor_ids": [str(self.doctor.id)], "action": "select"}
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            response.data["detail"], "Only patients can manage doctor selections."
        )

    def test_select_doctor_invalid_doctor_id(self):
        url = reverse("patient_select_doctor")
        invalid_uuid = str(uuid.uuid4())
        data = {"doctor_ids": [invalid_uuid], "action": "select"}
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_deselect_doctor(self):
        url = reverse("patient_select_doctor")
        # First, select a doctor.
        data_select = {"doctor_ids": [str(self.doctor.id)], "action": "select"}
        response_select = self.client.post(url, data_select, format="json")
        self.assertEqual(response_select.status_code, status.HTTP_200_OK)
        self.assertTrue(
            DoctorPatientAssignment.objects.filter(doctor=self.doctor, patient=self.patient).exists()
        )
        # Then, deselect the same doctor.
        data_deselect = {"doctor_ids": [str(self.doctor.id)], "action": "deselect"}
        response_deselect = self.client.post(url, data_deselect, format="json")
        self.assertEqual(response_deselect.status_code, status.HTTP_200_OK)
        self.assertFalse(
            DoctorPatientAssignment.objects.filter(doctor=self.doctor, patient=self.patient).exists()
        )

# ------------------------------
# Tests for the Patient Doctor List Endpoint
# ------------------------------
class TestPatientDoctorListEndpoint(BaseAPITest):
    def setUp(self):
        super().setUp()
        self.patient = UserFactory(role='patient')
        self.doctor = UserFactory(role='doctor')
        self.client.force_authenticate(user=self.patient)
        # Create a doctor-patient assignment.
        DoctorPatientAssignment.objects.create(doctor=self.doctor, patient=self.patient)

    def test_patient_doctor_list_success(self):
        url = reverse("patient_doctor_list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        assignments = response.data["results"] if "results" in response.data else response.data
        self.assertEqual(len(assignments), 1)

    def test_patient_doctor_list_invalid_role(self):
        # Authenticate as doctor to check for forbidden access.
        self.client.force_authenticate(user=self.doctor)
        url = reverse("patient_doctor_list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

# ------------------------------
# Tests for the Doctor Patient List Endpoint
# ------------------------------
class TestDoctorPatientListEndpoint(BaseAPITest):
    def setUp(self):
        super().setUp()
        self.doctor = UserFactory(role='doctor')
        self.patient = UserFactory(role='patient')
        self.client.force_authenticate(user=self.doctor)
        DoctorPatientAssignment.objects.create(doctor=self.doctor, patient=self.patient)

    def test_doctor_patient_list_success(self):
        url = reverse("doctor_patient_list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        assignments = response.data["results"] if "results" in response.data else response.data
        self.assertEqual(len(assignments), 1)

    def test_doctor_patient_list_invalid_role(self):
        self.client.force_authenticate(user=self.patient)
        url = reverse("doctor_patient_list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

# ------------------------------
# Tests for the Doctor Note Create Endpoint
# ------------------------------
class TestDoctorNoteCreateEndpoint(BaseAPITest):
    def setUp(self):
        super().setUp()
        self.doctor = UserFactory(role='doctor', email='doc@example.com')
        self.patient = UserFactory(role='patient', email='patient@example.com')
        # Create an assignment so that the note can be submitted.
        DoctorPatientAssignment.objects.create(doctor=self.doctor, patient=self.patient)

    @patch("hospital.views.process_doctor_note.delay")
    def test_create_doctor_note_success(self, mock_delay):
        self.client.force_authenticate(user=self.doctor)
        url = reverse("doctor_note_create")
        note_text = "This is a test note."
        data = {"patient": str(self.patient.id), "note_text": note_text}
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        note = DoctorNote.objects.get(id=response.data["id"])
        self.assertEqual(note.note_text, note_text)
        # Assert that the asynchronous task was triggered.
        mock_delay.assert_called_once()

    def test_create_doctor_note_invalid_role(self):
        self.client.force_authenticate(user=self.patient)
        url = reverse("doctor_note_create")
        data = {"patient": str(self.patient.id), "note_text": "Test note"}
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data["detail"], "Only doctors can submit notes.")

    def test_create_doctor_note_without_assignment(self):
        # Remove the assignment.
        DoctorPatientAssignment.objects.all().delete()
        self.client.force_authenticate(user=self.doctor)
        url = reverse("doctor_note_create")
        data = {"patient": str(self.patient.id), "note_text": "Test note"}
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data["detail"], "This patient is not assigned to you.")

    def test_create_doctor_note_missing_note_text(self):
        self.client.force_authenticate(user=self.doctor)
        url = reverse("doctor_note_create")
        data = {"patient": str(self.patient.id)}
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["detail"], "The noteText field is required.")

# ------------------------------
# Tests for the Actionable Step Endpoints (List and Update)
# ------------------------------
class TestActionableStepEndpoints(BaseAPITest):
    def setUp(self):
        super().setUp()
        self.patient = UserFactory(role='patient')
        self.doctor = UserFactory(role='doctor')
        # Create a doctor note and a pending actionable step.
        self.note = DoctorNote.objects.create(
            doctor=self.doctor,
            patient=self.patient,
            note_text="Test note"
        )
        self.action_step = ActionableStep.objects.create(
            note=self.note,
            step_type="checklist",
            description="Initial task"
        )
        self.client.force_authenticate(user=self.patient)

    def test_get_actionable_steps(self):
        url = reverse("actionable_step_list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        steps = response.data["results"] if "results" in response.data else response.data
        # Should only return pending actionable steps.
        self.assertEqual(len(steps), 1)
        self.assertEqual(steps[0]["description"], "Initial task")

    def test_update_actionable_step_status(self):
        url = reverse("actionable_step_update", args=[self.action_step.id])
        data = {"status": "completed"}
        response = self.client.patch(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.action_step.refresh_from_db()
        self.assertEqual(self.action_step.status, "completed")
