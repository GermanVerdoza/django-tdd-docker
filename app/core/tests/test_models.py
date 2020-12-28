from django.test import TestCase
from django.contrib.auth import get_user_model
from core import models


def sample_user(email='german"mimail.com', password='testpass'):
    """Create a sample user for testing"""
    return get_user_model().objects.create_user(email, password)


class ModelTests(TestCase):

    def test_create_user_with_email(self):
        """Test creating user only with an email"""
        email = 'test@grupoexcel.com'
        password = 'pass123'
        user = get_user_model().objects.create_user(
            email=email, password=password
        )
        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password))

    def test_normalize_email(self):
        """Test email for new_user is normalized"""
        email = 'test@GRUPOEXCEL.com'
        password = 'pass123'
        user = get_user_model().objects.create_user(
            email=email, password=password
        )
        self.assertEqual(user.email, email.lower())

    def test_create_user_invalid_email(self):
        """Test creating user only with an invalid email address"""
        password = 'pass123'
        with self.assertRaises(ValueError):
            get_user_model().objects.create_user(None, password)

    def test_create_new_superuser(self):
        """test create a new superuser"""
        user = get_user_model().objects.create_superuser(
            'test@grupoexcel.com', 'pass123'
        )
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)

    def test_tag_str(self):
        """Test the tag string representation"""
        tag = models.Tag.objects.create(
            user=sample_user(),
            name='Carnivore'
        )
        self.assertEqual(str(tag), tag.name)
