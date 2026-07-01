from django.urls import path

from .views.project import create_project_view

urlpatterns = [
    path("<slug:slug>/create/",create_project_view,name="create-project"),
]