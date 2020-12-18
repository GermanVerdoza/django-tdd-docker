from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse


class AdminSiteTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.admin_user = get_user_model().objects.create_superuser(
            email='admin@excel.network', password='pass123'
        )
        self.client.force_login(self.admin_user)
        self.user = get_user_model().objects.create_user(
            email='test@excel.network', password='pass123',
            name='Test FullName'
        )

    def test_users_listed(self):
        """Test user list in admin site"""
        url = reverse('admin:core_customuser_changelist')
        res = self.client.get(url)

        self.assertContains(res, self.user.name)
        self.assertContains(res, self.user.email)

    def test_user_change_page(self):
        url = reverse('admin:core_customuser_change', args=[self.user.id])
        res = self.client.get(url)

        self.assertEqual(res.status_code, 200)

    def test_create_user_page(self):
        url = reverse('admin:core_customuser_add')
        res = self.client.get(url)

        self.assertEqual(res.status_code, 200)
