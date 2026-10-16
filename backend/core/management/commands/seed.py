import os

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand
from django.db import transaction

from core.ingestion.models import District

User = get_user_model()

ADMIN_GROUP = "admin"


class Command(BaseCommand):
    help = "Seed the admin role, initial admin user"

    @transaction.atomic
    def handle(self, *args, **options):
        group, _ = Group.objects.get_or_create(name=ADMIN_GROUP)

        username = os.environ.get("SEED_ADMIN_USERNAME", "admin")
        password = os.environ.get("SEED_ADMIN_PASSWORD", "admin")

        user, created = User.objects.get_or_create(username=username)
        if created:
            user.set_password(password)
            user.save()
            self.stdout.write(self.style.SUCCESS(f"Created user '{username}'"))
        else:
            self.stdout.write(f"User '{username}' already exists")

        user.groups.add(group)
        self.stdout.write(self.style.SUCCESS(f"User '{username}' has role '{ADMIN_GROUP}'"))


