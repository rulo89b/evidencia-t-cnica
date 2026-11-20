
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db import transaction
from django.http import Http404
from django.shortcuts import (
    get_object_or_404,
    redirect,
    render,
)
from django.views.decorators.http import require_http_methods

from .forms import GroupForm
from .models import Group, GroupMember
from .services import create_group


@login_required
def group_list(request):
    memberships = (
        GroupMember.objects.filter(user=request.user)
        .select_related("group")
        .order_by("group__name")
    )

    return render(
        request,
        "grupos/group_list.html",
        {"memberships": memberships},
    )


@login_required
@require_http_methods(["GET", "POST"])
def group_create(request):
    if request.method == "POST":
        form = GroupForm(request.POST)

        if form.is_valid():
            group = create_group(
                user=request.user,
                name=form.cleaned_data["name"],
                description=form.cleaned_data["description"],
            )

            return redirect(
                "grupos:group_detail",
                pk=group.pk,
            )
    else:
        form = GroupForm()

    return render(
        request,
        "grupos/group_form.html",
        {
            "form": form,
            "title": "Crear grupo",
        },
    )


@login_required
def group_detail(request, pk):
    membership = get_object_or_404(
        GroupMember.objects.select_related("group"),
        group_id=pk,
        user=request.user,
    )

    members = (
        GroupMember.objects.filter(group_id=pk)
        .select_related("user")
        .order_by("user__username")
    )

    return render(
        request,
        "grupos/group_detail.html",
        {
            "group": membership.group,
            "membership": membership,
            "members": members,
        },
    )


@login_required
@require_http_methods(["GET", "POST"])
def group_update(request, pk):
    membership = get_object_or_404(
        GroupMember.objects.select_related("group"),
        group_id=pk,
        user=request.user,
    )

    if membership.role != GroupMember.Role.ADMIN:
        raise Http404("Grupo no encontrado.")

    group = membership.group

    if request.method == "POST":
        form = GroupForm(
            request.POST,
            instance=group,
        )

        if form.is_valid():
            with transaction.atomic():
                form.save()

            return redirect(
                "grupos:group_detail",
                pk=group.pk,
            )
    else:
        form = GroupForm(instance=group)

    return render(
        request,
        "grupos/group_form.html",
        {
            "form": form,
            "title": "Editar grupo",
        },
    )
