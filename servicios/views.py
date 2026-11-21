
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.core.exceptions import PermissionDenied, ValidationError
from django.utils import timezone
from django.views.decorators.http import require_http_methods, require_POST
from django.http import HttpResponseBadRequest

from grupos.models import GroupMember
from .forms import TemplateForm, TemplatePhotoForm, JobForm, JobPhotoForm, GroupJobForm
from .models import Template, TemplatePhoto, Job, JobPhotoSlot
from .services import (
    create_template_photo,
    delete_template_photo,
    move_template_photo,
    create_job,
    capture_job_photo,
    complete_job,
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


@login_required
def job_list(request):

    jobs = Job.objects.filter(
        assigned_to=request.user,
    ).select_related(
        "template",
        "group",
    ).order_by("-created_at")

    return render(
        request,
        "servicios/job_list.html",
        {"jobs": jobs},
    )


@login_required
@require_http_methods(["GET", "POST"])
def job_create(request):

    if request.method == "POST":
        form = JobForm(
            request.POST,
            user=request.user,
        )

        if form.is_valid():

            try:
                job = create_job(
                    user=request.user,
                    **form.cleaned_data,
                )

            except ValidationError as error:
                form.add_error(None, error)

            except PermissionDenied as error:
                form.add_error(None, str(error))

            else:
                return redirect(
                    "servicios:job_detail",
                    pk=job.pk,
                )

    else:
        form = JobForm(user=request.user)

    return render(
        request,
        "servicios/job_form.html",
        {"form": form},
    )


@login_required
def job_detail(request, pk):

    job = get_object_or_404(
        Job.objects.select_related(
            "template",
            "group",
        ),
        pk=pk,
        assigned_to=request.user,
    )

    slots = list(job.photo_slots.all())

    required_slots = [
        slot for slot in slots
        if slot.is_required
    ]

    required_total = len(required_slots)

    required_captured = sum(
        slot.is_captured
        for slot in required_slots
    )

    progress = (
        round(required_captured / required_total * 100)
        if required_total
        else 100
    )

    return render(
        request,
        "servicios/job_detail.html",
        {
            "job": job,
            "slots": slots,
            "required_total": required_total,
            "required_captured": required_captured,
            "progress": progress,
        },
    )


@login_required
@require_http_methods(["GET", "POST"])
def job_photo_capture(request, pk, slot_pk):

    slot = get_object_or_404(
        JobPhotoSlot.objects.select_related("job"),
        pk=slot_pk,
        job_id=pk,
        job__assigned_to=request.user,
    )

    if slot.job.status not in (
        Job.Status.PENDING,
        Job.Status.IN_PROGRESS,
    ):
        return HttpResponseBadRequest(
            "Este trabajo no admite nuevas capturas."
        )

    if request.method == "POST":
        form = JobPhotoForm(
            request.POST,
            request.FILES,
        )

        if form.is_valid():
            try:
                capture_job_photo(
                    slot=slot,
                    user=request.user,
                    photo=form.cleaned_data["photo"],
                )
            except ValidationError as error:
                form.add_error(None, error)
            else:
                return redirect(
                    "servicios:job_detail",
                    pk=pk,
                )
    else:
        form = JobPhotoForm()

    return render(
        request,
        "servicios/job_photo_form.html",
        {
            "form": form,
            "slot": slot,
            "job": slot.job,
        },
    )


@login_required
@require_POST
def job_complete(request, pk):

    job = get_object_or_404(
        Job,
        pk=pk,
        assigned_to=request.user,
    )

    try:
        complete_job(job=job, user=request.user)

    except ValidationError as error:
        messages.error(request, "; ".join(error.messages))

    else:
        messages.success(
            request,
            "El trabajo se ha completado correctamente.",
        )

    return redirect(
        "servicios:job_detail",
        pk=pk,
    )


@login_required
@require_http_methods(["GET", "POST"])
def group_job_create(request, group_pk):

    membership = get_object_or_404(
        GroupMember.objects.select_related("group"),
        group_id=group_pk,
        user=request.user,
        role=GroupMember.Role.ADMIN,
    )

    group = membership.group

    if request.method == "POST":
        form = GroupJobForm(
            request.POST,
            user=request.user,
            group=group,
        )

        if form.is_valid():
            try:
                job = create_job(
                    user=request.user,
                    group=group,
                    template=form.cleaned_data["template"],
                    assigned_to=form.cleaned_data["assigned_to"],
                    site_name=form.cleaned_data["site_name"],
                    notes=form.cleaned_data["notes"],
                    due_date=form.cleaned_data["due_date"],
                )

            except ValidationError as error:
                form.add_error(None, error)

            except PermissionDenied as error:
                form.add_error(None, str(error))

            else:
                return redirect(
                    "grupos:group_detail",
                    pk=group.pk,
                )

    else:
        form = GroupJobForm(
            user=request.user,
            group=group,
        )

    return render(
        request,
        "servicios/group_job_form.html",
        {
            "form": form,
            "group": group,
        },
    )
