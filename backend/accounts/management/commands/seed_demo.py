"""Create a development demo account. Never runs unless explicitly invoked."""

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from accounts.models import User
from organizations.models import OrganizationRole
from organizations.services import create_organization


class Command(BaseCommand):
    help = "Create the development demo user and workspace. Refuses to run when DEBUG is off."

    def handle(self, *args, **options):
        if not settings.DEBUG:
            raise CommandError("seed_demo is only available when DEBUG is true.")

        email = User.objects.normalize_email(settings.DEMO_EMAIL)
        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                "first_name": "Avery",
                "last_name": "Chen",
                "is_active": True,
            },
        )
        if created:
            user.set_password(settings.DEMO_PASSWORD)
            user.save(update_fields=["password"])
            self.stdout.write(self.style.SUCCESS(f"Created demo user {email}"))
        else:
            self.stdout.write(f"Demo user {email} already exists")

        if not user.organization_memberships.filter(role=OrganizationRole.OWNER).exists():
            create_organization(
                owner=user,
                name=settings.DEMO_ORGANIZATION,
                description="Demo workspace for exploring Orbit Phase 1.",
            )
            self.stdout.write(self.style.SUCCESS(f"Created organization {settings.DEMO_ORGANIZATION}"))
        else:
            self.stdout.write("Demo user already owns an organization")
