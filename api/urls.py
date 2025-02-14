from django.urls import include, path

urlpatterns = [
    path("account/", include("account.urls")),
    path("hospital/", include("hospital.urls")),
]
