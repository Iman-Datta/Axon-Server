from django.urls import path
from .views import ticket_activity_list, project_activity_list

urlpatterns = [
    path("project/<int:ticket_id>/", ticket_activity_list, name="get-ticket-activities"),
    path("project/", project_activity_list, name="get-project-activities"),
]