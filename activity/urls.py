from django.urls import path
from .views import get_all_activities

urlpatterns = [
    path("", get_all_activities, name="get-all-activities"),
]