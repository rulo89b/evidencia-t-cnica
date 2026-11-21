
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

    path(
        "plantillas/<uuid:pk>/",
        views.template_detail,
        name="template_detail",
    ),
    path(
        "plantillas/<uuid:pk>/fotos/nueva/",
        views.template_photo_create,
        name="template_photo_create",
    ),
    path(
        "plantillas/<uuid:pk>/fotos/<uuid:photo_pk>/editar/",
        views.template_photo_update,
        name="template_photo_update",
    ),
    path(
        "plantillas/<uuid:pk>/fotos/<uuid:photo_pk>/eliminar/",
        views.template_photo_delete,
        name="template_photo_delete",
    ),
    path(
        "plantillas/<uuid:pk>/fotos/<uuid:photo_pk>/mover/",
        views.template_photo_move,
        name="template_photo_move",
    ),

    path(
        "trabajos/",
        views.job_list,
        name="job_list",
    ),
    path(
        "trabajos/nuevo/",
        views.job_create,
        name="job_create",
    ),
    path(
        "trabajos/<uuid:pk>/",
        views.job_detail,
        name="job_detail",
    ),

    path(
        "trabajos/<uuid:pk>/fotos/<uuid:slot_pk>/capturar/",
        views.job_photo_capture,
        name="job_photo_capture",
    ),
    path(
        "trabajos/<uuid:pk>/finalizar/",
        views.job_complete,
        name="job_complete",
    ),

    path(
        "trabajos/grupos/<uuid:group_pk>/nuevo/",
        views.group_job_create,
        name="group_job_create",
    ),

    path(
        "trabajos/grupos/<uuid:group_pk>/",
        views.group_job_list,
        name="group_job_list",
    ),
    path(
        "trabajos/grupos/<uuid:group_pk>/<uuid:job_pk>/",
        views.group_job_detail,
        name="group_job_detail",
    ),
    path(
        "trabajos/grupos/<uuid:group_pk>/<uuid:job_pk>/reasignar/",
        views.group_job_reassign,
        name="group_job_reassign",
    ),


]
