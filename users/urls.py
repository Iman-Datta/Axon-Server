
from django.urls import path
from .views import register_view, verify_email_view, refresh_token_view, login_view, logout_view,me_view, google_login_view, google_callback_view, github_login_view, github_callback_view, check_username_view, update_username_view

urlpatterns = [
    path("register/", register_view),
    path("verify-email/", verify_email_view),
    path("refresh/",refresh_token_view),
    path("login/", login_view),
    path("logout/", logout_view),

    # Google OAuth
    path("google/", google_login_view,name="google-login"),
    path("google/callback/",google_callback_view,name="google-callback"),

    # GitHub OAuth
    path("github/",github_login_view),
    path("github/callback/",github_callback_view),

    path("profile/check-username/", check_username_view),
    path("profile/username/", update_username_view),
    path("me/",me_view),
]