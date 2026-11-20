from django.contrib import messages

from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError, PermissionDenied
from django.db import transaction
from django.http import Http404
from django.utils import timezone
from django.shortcuts import (
    get_object_or_404,
    redirect,
    render,
)
from django.views.decorators.http import require_http_methods, require_POST

from .forms import GroupForm, GroupInvitationForm
from .models import Group, GroupMember, GroupInvitation
from .services import (
    create_group,
    invite_user_to_group,
    accept_group_invitation,
    reject_group_invitation,
)


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


@login_required
@require_http_methods(["GET", "POST"])
def group_invite(request, pk):

    membership = get_object_or_404(
        GroupMember,
        group_id=pk,
        user=request.user,
        role=GroupMember.Role.ADMIN,
    )

    if request.method == "POST":
        form = GroupInvitationForm(request.POST)

        if form.is_valid():
            try:
                invite_user_to_group(
                    group=membership.group,
                    invited_by=request.user,
                    email=form.cleaned_data["email"],
                )
            except ValidationError as error:
                form.add_error(None, error)
            else:
                messages.success(
                    request,
                    "Invitación creada correctamente.",
                )
                return redirect(
                    "grupos:group_detail",
                    pk=pk,
                )
    else:
        form = GroupInvitationForm()

    return render(
        request,
        "grupos/group_invite.html",
        {
            "form": form,
            "group": membership.group,
        },
    )


@login_required
def invitation_list(request):

    invitations = (
        GroupInvitation.objects.filter(
            invited_user=request.user,
            status=GroupInvitation.Status.PENDING,
        )
        .select_related("group", "invited_by")
        .order_by("-created_at")
    )

    return render(
        request,
        "grupos/invitation_list.html",
        {"invitations": invitations},
    )


@login_required
@require_POST
def invitation_respond(request, pk):

    invitation = get_object_or_404(
        GroupInvitation,
        pk=pk,
        invited_user=request.user,
    )

    action = request.POST.get("action")

    try:
        if action == "accept":
            accept_group_invitation(
                invitation=invitation,
                user=request.user,
            )
            messages.success(
                request,
                "Te has unido al grupo.",
            )

        elif action == "reject":
            reject_group_invitation(
                invitation=invitation,
                user=request.user,
            )
            messages.success(
                request,
                "Invitación rechazada.",
            )

        else:
            messages.error(
                request,
                "Acción no válida.",
            )

    except ValidationError as error:
        messages.error(
            request,
            "; ".join(error.messages),
        )

    return redirect("grupos:invitation_list")
