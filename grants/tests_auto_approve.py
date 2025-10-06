from django.test import TestCase, override_settings
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from grants.models import GrantApplication
from django.core import mail
from django.core.management import call_command


class AutoApproveCommandTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('auto', 'auto@example.com', 'pw')
        self.grant = GrantApplication.objects.create(
            user=self.user,
            full_name='Auto User',
            email='auto@example.com',
            address='Some Address',
            amount_requested=1000,
            status='Pending',
        )
        # override auto_now_add timestamp for test
        self.grant.created_at = timezone.now() - timedelta(minutes=31)
        self.grant.save(update_fields=['created_at'])

    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend', DEFAULT_FROM_EMAIL='noreply@example.com')
    def test_auto_approve_command_approves_and_emails(self):
        call_command('auto_approve')
        g = GrantApplication.objects.get(pk=self.grant.pk)
        self.assertEqual(g.status.lower(), 'approved')
        # one email to applicant should be sent
        self.assertTrue(len(mail.outbox) >= 1)


class HoneypotTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('hpuser', 'hp@example.com', 'pw')

    def test_honeypot_blocks_submission(self):
        self.client.login(username='hpuser', password='pw')
        data = {
            'full_name': 'Spam Bot',
            'email': 'bot@example.com',
            'address': 'Spam Street',
            'amount_requested': 1000,
            'hp': 'I am a bot',
        }
        resp = self.client.post('/grants/apply/', data, follow=True)
        # Should redirect to wait page and no GrantApplication created
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(GrantApplication.objects.filter(user=self.user).exists())
