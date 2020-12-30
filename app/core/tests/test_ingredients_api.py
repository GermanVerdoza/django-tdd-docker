from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Ingredient
from recipe.serializers import IngredientSerializer

INGREDIENTS_URL = reverse('recipe:ingredient-list')


class PublicIngredientApiTests(TestCase):
    """Test that Ingredients Api is Public available."""
    def setUp(self):
        self.client = APIClient()

    def test_login_is_required(self):
        """Test login is required for retrieving tags"""
        res = self.client.get(INGREDIENTS_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateIngredientsApiTest(TestCase):
    """Test Ingredients Api for authorized user."""

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email='test@excel.network', password='pass123',
            name='Test FullName'
        )
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_retrieve_ingredients(self):
        """Test for retrieving list of ingredients"""
        Ingredient.objects.create(user=self.user, name='Salami')
        Ingredient.objects.create(user=self.user, name='Pancake')

        res = self.client.get(INGREDIENTS_URL)
        tags = Ingredient.objects.all().order_by('-name')
        serializer = IngredientSerializer(tags, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_limited_ingredients(self):
        """Test Ingredient returned are specific for logged user"""
        user2 = get_user_model().objects.create_user(
            email='test2@excel.network', password='pass123',
            name='Test FullName 2'
        )
        Ingredient.objects.create(user=user2, name='Orange')
        tag = Ingredient.objects.create(user=self.user, name='Curry')
        res = self.client.get(INGREDIENTS_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['name'], tag.name)

    def test_create_ingredient_success(self):
        """Test creating a new Ingredient"""
        payload = {'name': 'Test Ingredient'}
        self.client.post(INGREDIENTS_URL, payload)

        exists = Ingredient.objects.filter(user=self.user,
                                           name=payload['name']
                                           ).exists()
        self.assertTrue(exists)

    def test_create_ingredient_fail(self):
        """Test creating a new Ingredient with invalid payload"""
        payload = {'name': ''}
        res = self.client.post(INGREDIENTS_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
