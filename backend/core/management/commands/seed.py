import os

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

ADMIN_GROUP = "admin"


class Command(BaseCommand):
    help = "Seed the initial administrator and admin group."

    @transaction.atomic
    def handle(self, *args, **options):
        username = os.environ.get("SEED_ADMIN_USERNAME", "").strip()

        password = os.environ.get("SEED_ADMIN_PASSWORD", "")

        if not username:
            raise CommandError("SEED_ADMIN_USERNAME must be configured.")

        if not password:
            raise CommandError("SEED_ADMIN_PASSWORD must be configured.")

        User = get_user_model()

        group, group_created = Group.objects.get_or_create(name=ADMIN_GROUP)

        if group_created:
            self.stdout.write(self.style.SUCCESS(f"Created group '{ADMIN_GROUP}'."))

        user, created = User.objects.get_or_create(username=username)

        if created:
            user.set_password(password)
            user.save(update_fields=["password"])

            self.stdout.write(
                self.style.SUCCESS(f"Created administrator '{username}'.")
            )
        else:
            self.stdout.write(
                f"User '{username}' already exists. Existing password was preserved."
            )

        if not user.groups.filter(pk=group.pk).exists():
            user.groups.add(group)

            self.stdout.write(
                self.style.SUCCESS(f"Assigned '{username}' to group '{ADMIN_GROUP}'.")
            )
        else:
            self.stdout.write(
                f"User '{username}' already belongs to group '{ADMIN_GROUP}'."
            )

        self.stdout.write(self.style.SUCCESS("Administrator initialization completed."))
