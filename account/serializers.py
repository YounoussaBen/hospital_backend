from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from .models import User


class UserSerializer(serializers.ModelSerializer):
    profile_picture = Base64ImageField(required=False)

    class Meta:
        model = User
        exclude = ["password", "user_permissions", "groups", "is_superuser"]
        read_only_fields = [
            "last_login",
            "date_joined",
            "is_active",
            "is_staff",
            "email",
        ]
        extra_kwargs = {"password": {"write_only": True}}


class SignupSerializer(serializers.ModelSerializer):
    # Accept a full name and split into first and last names
    name = serializers.CharField(write_only=True)
    password = serializers.CharField(write_only=True, style={"input_type": "password"})
    profile_picture = Base64ImageField(
        required=False,
        help_text="Base64 encoded image string. Example: '/9j/4AAQSkZJRgABAQAAAQABAAD...'"
    )
    
    # Validate that role is one of the allowed values
    role = serializers.ChoiceField(choices=User.ROLE_CHOICES)

    class Meta:
        model = User
        fields = ("id", "email", "name", "password", "role", "profile_picture")
        extra_kwargs = {"email": {"validators": [UniqueValidator(queryset=User.objects.all())]}}

    def create(self, validated_data):
        # Remove fields that will be passed separately to avoid duplication
        full_name = validated_data.pop("name")
        name_parts = full_name.split(" ", 1)
        validated_data["first_name"] = name_parts[0]
        validated_data["last_name"] = name_parts[1] if len(name_parts) > 1 else ""
        
        # Pop email and password to avoid passing them twice
        email = validated_data.pop("email")
        password = validated_data.pop("password")
        
        # Use the manager to create the user
        user = User.objects.create_user(email=email, password=password, **validated_data)
        return user