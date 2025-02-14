from django.urls import path
from .views import (
    DoctorListView,
    PatientSelectDoctorView,
    DoctorPatientListView,
    DoctorNoteCreateView,
    ActionableStepListView,
    ActionableStepUpdateView,
    PatientDoctorListView,
)

urlpatterns = [
    path('doctors/', DoctorListView.as_view(), name='doctor_list'),
    path('patients/select-doctor/', PatientSelectDoctorView.as_view(), name='patient_select_doctor'),
    path('patients/doctors/', PatientDoctorListView.as_view(), name='patient_doctor_list'),
    path('doctors/patients/', DoctorPatientListView.as_view(), name='doctor_patient_list'),
    path('notes/', DoctorNoteCreateView.as_view(), name='doctor_note_create'),
    path('reminders/', ActionableStepListView.as_view(), name='actionable_step_list'),
    path('reminders/<uuid:pk>/', ActionableStepUpdateView.as_view(), name='actionable_step_update'),
]
