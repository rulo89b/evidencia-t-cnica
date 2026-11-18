
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.views.decorators.http import require_http_methods, require_POST
from django.http import HttpResponseBadRequest

from .forms import TemplateForm, TemplatePhotoForm
from .models import Template, TemplatePhoto
from .services import (
    create_template_photo,
    delete_template_photo,
    move_template_photo,
)


@login_required
def template_list(request):
    templates = Template.objects.filter(
        owner=request.user,
        deleted_at__isnull=True,
    ).order_by("-created_at")

    return render(
        request,
        "servicios/template_list.html",
        {"templates": templates},
    )


@login_required
@require_http_methods(["GET", "POST"])
def template_create(request):

    if request.method == "POST":
        form = TemplateForm(request.POST)

        if form.is_valid():
            template = form.save(commit=False)
            template.owner = request.user
            template.save()

            return redirect("servicios:template_list")

    else:
        form = TemplateForm()

    return render(
        request,
        "servicios/template_form.html",
        {
            "form": form,
            "title": "Nueva plantilla",
        },
    )


@login_required
@require_http_methods(["GET", "POST"])
def template_update(request, pk):

    template = get_object_or_404(
        Template,
        pk=pk,
        owner=request.user,
        deleted_at__isnull=True,
    )

    if request.method == "POST":
        form = TemplateForm(
            request.POST,
            instance=template,
        )

        if form.is_valid():
            form.save()

            return redirect("servicios:template_list")

    else:
        form = TemplateForm(instance=template)

    return render(
        request,
        "servicios/template_form.html",
        {
            "form": form,
            "title": "Editar plantilla",
        },
    )


@login_required
@require_http_methods(["GET", "POST"])
def template_delete(request, pk):

    template = get_object_or_404(
        Template,
        pk=pk,
        owner=request.user,
        deleted_at__isnull=True,
    )

    if request.method == "POST":
        template.deleted_at = timezone.now()

        template.save(
            update_fields=["deleted_at", "updated_at"]
        )

        return redirect("servicios:template_list")

    return render(
        request,
        "servicios/template_confirm_delete.html",
        {"template": template},
    )


@login_required
def template_detail(request, pk):

    template = get_object_or_404(
        Template,
        pk=pk,
        owner=request.user,
        deleted_at__isnull=True,
    )

    return render(
        request,
        "servicios/template_detail.html",
        {
            "template": template,
            "photos": template.photos.all(),
        },
    )


@login_required
@require_http_methods(["GET", "POST"])
def template_photo_create(request, pk):

    template = get_object_or_404(
        Template,
        pk=pk,
        owner=request.user,
        deleted_at__isnull=True,
    )

    if request.method == "POST":
        form = TemplatePhotoForm(request.POST)

        if form.is_valid():
            create_template_photo(
                template=template,
                **form.cleaned_data,
            )

            return redirect(
                "servicios:template_detail",
                pk=template.pk,
            )

    else:
        form = TemplatePhotoForm()

    return render(
        request,
        "servicios/template_photo_form.html",
        {
            "template": template,
            "form": form,
            "title": "Agregar fotografía",
        },
    )


@login_required
@require_http_methods(["GET", "POST"])
def template_photo_update(request, pk, photo_pk):

    photo = get_object_or_404(
        TemplatePhoto,
        pk=photo_pk,
        template_id=pk,
        template__owner=request.user,
        template__deleted_at__isnull=True,
    )

    if request.method == "POST":
        form = TemplatePhotoForm(
            request.POST,
            instance=photo,
        )

        if form.is_valid():
            form.save()

            return redirect(
                "servicios:template_detail",
                pk=pk,
            )

    else:
        form = TemplatePhotoForm(instance=photo)

    return render(
        request,
        "servicios/template_photo_form.html",
        {
            "template": photo.template,
            "form": form,
            "title": "Editar fotografía",
        },
    )


@login_required
@require_http_methods(["GET", "POST"])
def template_photo_delete(request, pk, photo_pk):

    photo = get_object_or_404(
        TemplatePhoto,
        pk=photo_pk,
        template_id=pk,
        template__owner=request.user,
        template__deleted_at__isnull=True,
    )

    if request.method == "POST":
        delete_template_photo(photo=photo)

        return redirect(
            "servicios:template_detail",
            pk=pk,
        )

    return render(
        request,
        "servicios/template_photo_confirm_delete.html",
        {"photo": photo},
    )


@login_required
@require_POST
def template_photo_move(request, pk, photo_pk):

    photo = get_object_or_404(
        TemplatePhoto,
        pk=photo_pk,
        template_id=pk,
        template__owner=request.user,
        template__deleted_at__isnull=True,
    )

    direction = request.POST.get("direction")

    if direction not in ("up", "down"):
        return HttpResponseBadRequest(
            "Movimiento inválido."
        )

    move_template_photo(
        photo=photo,
        direction=direction,
    )

    return redirect(
        "servicios:template_detail",
        pk=pk,
    )
