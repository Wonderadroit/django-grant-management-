from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from grants.models import GrantApplication
from django.template.loader import render_to_string
from django.core.mail import send_mail, mail_admins
from django.conf import settings


class Command(BaseCommand):
    help = 'Auto-approve pending grant applications older than 30 minutes'

    def handle(self, *args, **options):
        cutoff = timedelta(minutes=30)
        pending = GrantApplication.objects.all()
        approved_count = 0
        now = timezone.now()
        for grant in pending:
            created_at = grant.created_at
            # normalize naive datetimes to aware using current timezone
            if created_at.tzinfo is None or created_at.tzinfo.utcoffset(created_at) is None:
                try:
                    created_at = timezone.make_aware(created_at, timezone.get_current_timezone())
                except Exception:
                    # fallback: treat as UTC
                    created_at = timezone.make_aware(created_at)

            age = now - created_at
            if age >= cutoff:
                grant.status = 'approved'
                grant.save()
                approved_count += 1

                # send approval email
                # attempt to render templates; if rendering fails, send a simple fallback email
                subject = 'Your grant application was approved'
                try:
                    context = {'grant': grant}
                    text = render_to_string('emails/approval.txt', context)
                    html = render_to_string('emails/approval.html', context)
                except Exception:
                    text = (f'Congratulations {grant.full_name}, your grant application for {grant.amount_requested} has been approved. '
                            'Please contact us on WhatsApp +1 (872) 228-1570 or email grantdavejohnsonfoundation@gmail.com to proceed.')
                    html = None

                try:
                    send_mail(subject, text, settings.DEFAULT_FROM_EMAIL, [grant.email], html_message=html, fail_silently=True)
                except Exception:
                    pass

                # notify admins
                try:
                    mail_admins('Grant auto-approved', f'Auto-approved application for {grant.full_name} ({grant.email}) requesting {grant.amount_requested}')
                except Exception:
                    pass

        self.stdout.write(self.style.SUCCESS(f'Approved {approved_count} applications'))
