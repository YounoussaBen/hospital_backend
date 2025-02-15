from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from account.models import User
from account.serializers import UserSerializer
from .models import DoctorNote, ActionableStep, DoctorPatientAssignment
from .serializers import (
    DoctorNoteSerializer,
    ActionableStepSerializer,
    DoctorSelectionActionSerializer,
    DoctorPatientAssignmentSerializer,
    PatientDoctorAssignmentSerializer
)
from .tasks import process_doctor_note

# List available doctors (for patients)
class DoctorListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserSerializer

    def get_queryset(self):
        return User.objects.filter(role='doctor')

# Endpoint for a patient to select a doctor
class PatientSelectDoctorView(generics.CreateAPIView):
    """
    Endpoint for a patient to select or deselect doctors.
    After processing, returns the list of doctors currently selected.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = DoctorSelectionActionSerializer

    def post(self, request, *args, **kwargs):
        if request.user.role != 'patient':
            return Response(
                {'detail': 'Only patients can manage doctor selections.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Pass the request in the serializer context so that it can access the patient.
        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        # The create() method returns a queryset of updated assignments.
        assignments = serializer.save()
        
        # Serialize the assignments to display the selected doctors.
        output_serializer = PatientDoctorAssignmentSerializer(assignments, many=True)
        return Response(output_serializer.data, status=status.HTTP_200_OK)

# Endpoint for a patient to view their selected doctors
class PatientDoctorListView(generics.ListAPIView):
    """
    Endpoint for a patient to view their selected doctors.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = PatientDoctorAssignmentSerializer

    def get_queryset(self):
        if self.request.user.role != 'patient':
            raise PermissionDenied("Only patients can view their selected doctors.")
        return DoctorPatientAssignment.objects.filter(patient=self.request.user)
    
# Endpoint for a doctor to view their assigned patients
class DoctorPatientListView(generics.ListAPIView):
    """
    Endpoint for a doctor to view their assigned patients.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = DoctorPatientAssignmentSerializer

    def get_queryset(self):
        if self.request.user.role != 'doctor':
            raise PermissionDenied("Only doctors can view their assigned patients.")
        return DoctorPatientAssignment.objects.filter(doctor=self.request.user)

# Endpoint for doctors to submit a note (triggers LLM processing)
class DoctorNoteCreateView(generics.CreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = DoctorNoteSerializer

    def post(self, request, *args, **kwargs):
        if request.user.role != 'doctor':
            return Response(
                {'detail': 'Only doctors can submit notes.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        patient_id = request.data.get('patient')
        patient = get_object_or_404(User, id=patient_id, role='patient')
        
        # Check that the patient is assigned to this doctor.
        assignment_exists = DoctorPatientAssignment.objects.filter(
            doctor=request.user, patient=patient
        ).exists()
        if not assignment_exists:
            return Response(
                {'detail': 'This patient is not assigned to you.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        note_text = request.data.get('note_text')
        if note_text is None:
            return Response(
                {'detail': 'The noteText field is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        doctor_note = DoctorNote.objects.create(
            doctor=request.user,
            patient=patient,
            note_text=note_text
        )
        # Trigger asynchronous LLM processing to extract actionable steps.
        process_doctor_note.delay(str(doctor_note.id))
        
        serializer = self.get_serializer(doctor_note)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


# Endpoint for patients to retrieve their actionable steps (reminders)
class ActionableStepListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ActionableStepSerializer

    def get_queryset(self):
        if self.request.user.role == 'patient':
            return ActionableStep.objects.filter(note__patient=self.request.user, status='pending')
        return ActionableStep.objects.none()

# Endpoint to update the status of an actionable step (e.g., mark as completed)
class ActionableStepUpdateView(generics.UpdateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ActionableStepSerializer
    queryset = ActionableStep.objects.all()

    def patch(self, request, *args, **kwargs):
        return self.partial_update(request, *args, **kwargs)
