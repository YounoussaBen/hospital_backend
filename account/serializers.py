from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers

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
