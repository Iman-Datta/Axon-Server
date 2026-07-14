from django.urls import path

from .views.organization import (create_org, my_org, update_org,delete_org,org_detail_view)
from .views.member import (list_members,add_member,update_member_role,remove_member,leave_org,)

urlpatterns = [
    path("create/", create_org, name="create-org"),
    path("my/", my_org, name="my-org"),
    path("<slug:slug>/update", update_org, name="update-org"),
    path("<slug:slug>/delete/", delete_org, name="delete-org"),
    path("<slug:slug>/",org_detail_view,name="organization-detail"),

    path("<slug:slug>/members/", list_members),
    path("<slug:slug>/members/add/", add_member),
    path("<slug:slug>/members/<int:member_id>/role/", update_member_role),
    path("<slug:slug>/members/<int:member_id>/remove/", remove_member),
    path("<slug:slug>/leave/", leave_org),
]