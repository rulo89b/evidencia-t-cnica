
from django.urls import path

from . import views


app_name = "grupos"

urlpatterns = [
    path(
        "grupos/",
        views.group_list,
        name="group_list",
    ),
    path(
        "grupos/nuevo/",
        views.group_create,
        name="group_create",
    ),
    path(
        "grupos/<uuid:pk>/",
        views.group_detail,
        name="group_detail",
    ),
    path(
        "grupos/<uuid:pk>/editar/",
        views.group_update,
        name="group_update",
    ),

    path(
        "grupos/<uuid:pk>/invitar/",
        views.group_invite,
        name="group_invite",
    ),
    path(
        "invitaciones/",
        views.invitation_list,
        name="invitation_list",
    ),
    path(
        "invitaciones/<uuid:pk>/responder/",
        views.invitation_respond,
        name="invitation_respond",
    ),

]
