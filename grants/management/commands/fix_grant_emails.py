from django.core.management.base import BaseCommand
from grants.models import GrantApplication
import re

EMAIL_RE = re.compile(r"[^@\s]+@[^@\s]+\.[^@\s]+")

class Command(BaseCommand):
    help = 'Fix migrated placeholder emails for GrantApplication records'

    def handle(self, *args, **options):
        corrected = 0
        for g in GrantApplication.objects.all():
            if not g.email or not EMAIL_RE.match(str(g.email)):
                user_email = getattr(g.user, 'email', '')
                new_email = user_email if user_email and EMAIL_RE.match(user_email) else ''
                if g.email != new_email:
                    g.email = new_email
                    g.save()
                    corrected += 1
                    self.stdout.write(f'Updated GrantApplication id={g.id} email -> "{new_email}"')
        self.stdout.write(self.style.SUCCESS(f'Done. Corrected {corrected} records.'))
