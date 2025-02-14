import uuid

from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext as _
from django.db.models.signals import pre_save
from django.dispatch import receiver


class UserQuerySet(models.QuerySet):
    def active(self):
        return self.filter(is_active=True)

    def inactive(self):
        return self.filter(is_active=False)

    def staff(self):
        return self.filter(is_staff=True)

    def superusers(self):
        return self.filter(is_superuser=True)
    
    def registration_completed(self):
        return self.filter(is_registration_completed=True)

    def registration_not_completed(self):
        return self.filter(is_registration_completed=False)

    def filter_by_date(self, before=None, after=None):
        if before and after:
            return self.filter(date_joined__range=[after, before])

        if before:
            return self.filter(date_joined__lte=before)

        if after:
            return self.filter(date_joined__gte=after)

        return self


class UserManager(BaseUserManager):
    """
    Custom user model manager where email is the unique identifiers
    for authentication instead of usernames.
    """

    def get_queryset(self):
        return UserQuerySet(self.model, using=self._db)

    def create_user(self, email, password, **extra_fields):
        """
        Create and save a User with the given email and password.
        """
        if not email:
            raise ValueError(_("The Email must be set"))
        if not password:
            raise ValueError(_("The Password must be set"))
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, email, password, **extra_fields):
        """
        Create and save a SuperUser with the given email and password.
        """
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError(_("Superuser must have is_staff=True."))
        if extra_fields.get("is_superuser") is not True:
            raise ValueError(_("Superuser must have is_superuser=True."))
        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    objects: UserManager

    class Gender:
        MALE = "Male"
        FEMALE = "Female"
        OTHER = "Other"

        CHOICES = (
            (MALE, _("Male")),
            (FEMALE, _("Female")),
            (OTHER, _("Other")),
        )
        
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    username = None
    email = models.EmailField(_("user email"), max_length=254, unique=True)
    gender = models.CharField(
        max_length=10, choices=Gender.CHOICES, default=Gender.OTHER
    )
    profile_picture = models.ImageField(
        upload_to="profile_pictures", blank=True, null=True
    )
    is_registration_completed = models.BooleanField(default=False)
    

    objects = UserManager()
    USERNAME_FIELD = "email"
    EMAIL_FIELD = "email"
    REQUIRED_FIELDS = []

@receiver(pre_save, sender=User)
def change_user_registation_status(sender, instance: User, **kwargs):
    required_fields = [
        instance.email,
        instance.last_name,
        instance.first_name,
    ]

    if (
        None in required_fields
        or "" in required_fields
    ):
        instance.is_registration_completed = False
    else:
        instance.is_registration_completed = True