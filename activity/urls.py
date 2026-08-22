from django.urls import path
from .views import ticket_activity_list

urlpatterns = [
    path("ticket/<int:ticket_id>/", ticket_activity_list, name="get-ticket-activities"),
]