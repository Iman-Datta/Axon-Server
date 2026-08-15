
from django.urls import path
from .views import register_view, verify_magiclink_view, refresh_token_view, login_view, logout_view,me_view, google_login_view, google_callback_view, github_login_view, github_callback_view, check_username_view, update_username_view, send_otp_view, verify_email_otp_view, github_connect_view, complete_profile_view, public_profile_view, workspace_detail_view, update_profile_view, update_profile_password_view, my_overview, my_work_tickets, update_profile_avatar

urlpatterns = [
    # Core auth
    path("register/", register_view),
    path("refresh/",refresh_token_view),
    path("login/", login_view),
    path("logout/", logout_view),

    # Email
    path("verify-email/", verify_magiclink_view),
    path("email/send-otp/", send_otp_view),
    path("email/verify-otp/", verify_email_otp_view),

    # Google OAuth
    path("google/", google_login_view,name="google-login"),
    path("google/callback/",google_callback_view,name="google-callback"),

    # GitHub OAuth
    path("github/",github_login_view),
    path("github/callback/",github_callback_view),
    path("github/connect/", github_connect_view),

    # Profile
    path("profile/check-username/", check_username_view),
    path("profile/username/", update_username_view),
    path("me/",me_view),
    path("profile/complete/",complete_profile_view),
    path("profile/update", update_profile_view, name="update-profile"),
    path("profile/password", update_profile_password_view, name="update-password"),
    path("my/overview/", my_overview, name="my_overview"),
    path("profile/avtar/update/", update_profile_avatar),
    path("my/work/", my_work_tickets, name="my-work-tickets"),
    path("<str:username>/",public_profile_view,name="public-profile"),

    # Workspace
    path("workspaces/<slug:slug>/", workspace_detail_view),
]