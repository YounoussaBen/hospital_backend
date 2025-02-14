import logging

from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.tokens import RefreshToken


logger = logging.getLogger(__name__)
User = get_user_model()


def get_token_for_user(user):
    return (AccessToken.for_user(user), RefreshToken.for_user(user))
