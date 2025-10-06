from django.test import TestCase, Client
from django.contrib.auth.models import User
from .models import GrantApplication

class ApplyFlowTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user('applytester', 'apply@example.com', 'TestPass!123')

    def test_apply_creates_application_and_redirects(self):
        self.client.login(username='applytester', password='TestPass!123')
        # ensure no application exists
        GrantApplication.objects.filter(user=self.user).delete()
        resp = self.client.post('/grants/apply/', {
            'full_name': 'Apply Tester',
            'email': 'apply@example.com',
            'address': '123 Test Ave',
            'amount_requested': '1000',
        })
        # should redirect to wait
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp.url, '/grants/wait/')
        app = GrantApplication.objects.filter(user=self.user).first()
        self.assertIsNotNone(app)
        self.assertEqual(app.full_name, 'Apply Tester')
        