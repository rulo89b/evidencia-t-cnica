
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
]
