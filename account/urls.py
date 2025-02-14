from django.urls import path

from . import views


urlpatterns = [
    path(
        "user/", views.UserprofileView.as_view(), name="account_userprofile"
    ),
]
