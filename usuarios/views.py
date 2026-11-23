
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.utils import timezone

from servicios.models import Job, Template
from grupos.models import GroupMember, GroupInvitation

from .forms import RegisterForm


def register(request):
    if request.user.is_authenticated:
        return redirect("usuarios:home")

    if request.method == "POST":
        form = RegisterForm(request.POST)

        if form.is_valid():
            form.save()
            return redirect("usuarios:login")

    else:
        form = RegisterForm()

    return render(
        request,
        "usuarios/register.html",
        {"form": form},
    )


@login_required
def home(request):
    user = request.user

    my_jobs = Job.objects.filter(
        assigned_to=user
    )

    memberships = GroupMember.objects.filter(
        user=user
    )

    context = {
        "active_jobs_count": my_jobs.filter(
            status__in=[
                Job.Status.PENDING,
                Job.Status.IN_PROGRESS,
            ]
        ).count(),

        "completed_jobs_count": my_jobs.filter(
            status=Job.Status.COMPLETED
        ).count(),

        "templates_count": Template.objects.filter(
            owner=user,
            deleted_at__isnull=True,
        ).count(),

        "groups_count": memberships.count(),

        "admin_groups_count": memberships.filter(
            role=GroupMember.Role.ADMIN
        ).count(),

        "pending_invitations_count": (
            GroupInvitation.objects.filter(
                invited_user=user,
                status=GroupInvitation.Status.PENDING,
                expires_at__gt=timezone.now(),
            ).count()
        ),
    }

    return render(
        request,
        "usuarios/home.html",
        context,
    )
