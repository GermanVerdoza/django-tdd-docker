from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status

CREATE_USER_URL = reverse('users:create')
TOKEN_URL = reverse('users:token')


def create_user(**params):
    return get_user_model().objects.create_user(**params)


class PublicUserApiTest(TestCase):
    """Test the users API (public)"""

    def setUp(self):
        self.client = APIClient()

    def test_create_user_success(self):
        """Test create a new user successfully"""
        payload = {
            'email': 'test2@gmail.com',
            'password': 'pass987',
            'name': 'Name Testing'
        }
        res = self.client.post(CREATE_USER_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        user = get_user_model().objects.get(**res.data)
        self.assertTrue(user.check_password(payload['password']))
        self.assertNotIn('password', res.data)

    def test_user_exists(self):
        """Test create a user that exist fails"""
        payload = {
            'email': 'test2@gmail.com',
            'password': 'pass987',
            'name': 'Name Testing'
        }
        create_user(**payload)

        res = self.client.post(CREATE_USER_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_invalid_password(self):
        """Test password is strong enough"""
        payload = {
            'email': 'test2@gmail.com',
            'password': 'pw',
            'name': 'Name Testing'
        }

        res = self.client.post(CREATE_USER_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        user_exists = get_user_model().objects.filter(
            email=payload['email']
        ).exists()
        self.assertFalse(user_exists)

    def test_user_token_create(self):
        """Test that user creates a valid token"""
        payload = {
            'email': 'test2@gmail.com',
            'password': 'pass987',
        }
        create_user(**payload)

        res = self.client.post(TOKEN_URL, payload)
        self.assertIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_token_invalid_token(self):
        """Test that token is not created with invalid credentials"""
        create_user(email='test2@gmail.com', password='pass123')
        payload = {
            'email': 'test2@gmail.com',
            'password': 'pass987',
        }

        res = self.client.post(TOKEN_URL, payload)
        self.assertNotIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_user_token_invalid_user(self):
        """Test that token is not created if user does not exists"""
        payload = {
            'email': 'test2@gmail.com',
            'password': 'pass987',
        }

        res = self.client.post(TOKEN_URL, payload)
        self.assertNotIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_token_invalid_data(self):
        """Test that token is not created with missing email or pass"""

        res = self.client.post(TOKEN_URL, {
            'email': 'one',
            'password': '',
        })
        self.assertNotIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
