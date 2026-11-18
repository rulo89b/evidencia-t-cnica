
from django.urls import path

from . import views


app_name = "servicios"

urlpatterns = [
    path(
        "plantillas/",
        views.template_list,
        name="template_list",
    ),
    path(
        "plantillas/nueva/",
        views.template_create,
        name="template_create",
    ),
    path(
        "plantillas/<uuid:pk>/editar/",
        views.template_update,
        name="template_update",
    ),
    path(
        "plantillas/<uuid:pk>/eliminar/",
        views.template_delete,
        name="template_delete",
    ),
]
