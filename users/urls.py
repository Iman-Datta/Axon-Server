
from django.urls import path
from .views import register_view, verify_email_view, refresh_token_view

urlpatterns = [
    path("register/", register_view),
    path("verify-email/", verify_email_view),
    path("refresh_token/",refresh_token_view),
]
