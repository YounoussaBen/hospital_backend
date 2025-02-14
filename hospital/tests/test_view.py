# tests/test_endpoints.py
import uuid

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from hospital.models import DoctorPatientAssignment
from account.factories import UserFactory


class DoctorPatientEndpointsTest(APITestCase):
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