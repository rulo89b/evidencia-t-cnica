
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from .forms import TemplateForm
from .models import Template


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
