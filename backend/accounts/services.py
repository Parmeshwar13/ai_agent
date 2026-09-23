"""Account creation. Organization bootstrap stays here so registration is atomic."""

from django.db import transaction

from accounts.models import User
from organizations.services import create_organization


@transaction.atomic
def register_user(*, email, password, first_name, last_name="", organization_name=""):
    user = User.objects.create_user(
        email=email,
        password=password,
        first_name=first_name.strip(),
        last_name=(last_name or "").strip(),
    )
    name = (organization_name or "").strip() or f"{user.first_name}'s workspace"
    organization = create_organization(owner=user, name=name, description="")
    return user, organization
