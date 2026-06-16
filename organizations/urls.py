from django.urls import path

from view.organization import (create_org, my_org, update_org,delete_org,)

urlpatterns = [
    path("/create", create_org, name="create-org"),
    path("my/", my_org, name="my-org"),
    path("<slug:slug>/", update_org, name="update-org"),
    path("<slug:slug>/delete/", delete_org, name="delete-org"),
]