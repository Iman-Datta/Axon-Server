from django.urls import path

from .views.epic import (create_epic,update_epic,list_epics,delete_epic)

rlpatterns = [
    path("", list_epics, name="list_epics"),
    path("", create_epic, name="create_epic"),          # POST
    path("<int:epic_id>/", update_epic, name="update_epic"),   # PATCH
    path("<int:epic_id>/", delete_epic, name="delete_epic"),   # DELETE
]