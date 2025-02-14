# account/urls.py
from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import SignupView, UserprofileView

urlpatterns = [
    # Signup endpoint
    path("signup/", SignupView.as_view(), name="account_signup"),
    
    # Login endpoint (JWT token obtain)
    path("login/", TokenObtainPairView.as_view(), name="account_login"),
    
    # Token refresh endpoint
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    
    # Profile management endpoint (already implemented)
    path("user/", UserprofileView.as_view(), name="account_userprofile"),
]
