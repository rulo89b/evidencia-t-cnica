
from django.db import transaction

from .models import Group, GroupMember


@transaction.atomic
def create_group(*, user, name, description=""):
    group = Group.objects.create(
        name=name,
        description=description,
        created_by=user,
    )

    GroupMember.objects.create(
        group=group,
        user=user,
        role=GroupMember.Role.ADMIN,
    )

    return group
