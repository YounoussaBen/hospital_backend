from rest_framework import serializers
from .models import DoctorNote, ActionableStep, DoctorPatientAssignment
from account.serializers import UserSerializer
from account.models import User
from django.shortcuts import get_object_or_404

# Serializer to display a patient's selected doctors
class PatientDoctorAssignmentSerializer(serializers.ModelSerializer):
    doctor = UserSerializer(read_only=True)

    class Meta:
        model = DoctorPatientAssignment
        fields = ('doctor',)

# Serializer to display a doctor's assigned patients
class DoctorPatientAssignmentSerializer(serializers.ModelSerializer):
    patient = UserSerializer(read_only=True)
    notes = serializers.SerializerMethodField()

    class Meta:
        model = DoctorPatientAssignment
        read_only_fields = ("created", "updated")
        exclude = ("is_deleted", 'doctor')

    def get_notes(self, obj):
        doctor = obj.doctor
        patient = obj.patient
        notes_qs = DoctorNote.objects.filter(doctor=doctor, patient=patient)
        return DoctorNoteSerializer(notes_qs, many=True, context=self.context).data
    

# Serializer to select or deselect doctors for a patient
class DoctorSelectionActionSerializer(serializers.Serializer):
    doctor_ids = serializers.ListField(
        child=serializers.UUIDField(help_text="The UUID of a doctor."),
        help_text="List of doctor IDs to select or deselect."
    )
    action = serializers.ChoiceField(
        choices=[("select", "Select"), ("deselect", "Deselect")],
        help_text="Action to perform: 'select' to add doctors, 'deselect' to remove doctors."
    )

    def create(self, validated_data):
        doctor_ids = validated_data['doctor_ids']
        action = validated_data['action']
        request = self.context.get('request')
        if not request:
            raise serializers.ValidationError("Request context is missing.")
        patient = request.user

        # Process each doctor based on the action.
        for doctor_id in doctor_ids:
            # Ensure the doctor exists and has the proper role.
            doctor = get_object_or_404(User, id=doctor_id, role='doctor')
            if action == 'select':
                DoctorPatientAssignment.objects.get_or_create(patient=patient, doctor=doctor)
            elif action == 'deselect':
                DoctorPatientAssignment.objects.filter(patient=patient, doctor=doctor).delete()

        # Return the updated list of assignments for the patient.
        return DoctorPatientAssignment.objects.filter(patient=patient)
    
        
class ActionableStepSerializer(serializers.ModelSerializer):
    class Meta:
        model = ActionableStep
        read_only_fields = ("created", "updated")
        exclude = ("is_deleted",)

class DoctorNoteSerializer(serializers.ModelSerializer):
    actionable_steps = ActionableStepSerializer(many=True, read_only=True)

    class Meta:
        model = DoctorNote
        read_only_fields = ("created", "updated", "doctor")
        exclude = ("is_deleted",)
