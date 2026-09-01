from datetime import date

from django.test import TestCase
from django.urls import reverse

from .models import Grant


class GrantListTests(TestCase):
    def test_only_open_grants_are_returned(self):
        open_grant = Grant.objects.create(name="Open Grant", deadline=date(2026, 12, 1), is_open=True)
        Grant.objects.create(name="Closed Grant", is_open=False)

        response = self.client.get(reverse("grant-list"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["grants"][0]["id"], open_grant.id)
        self.assertEqual(len(response.json()["grants"]), 1)
