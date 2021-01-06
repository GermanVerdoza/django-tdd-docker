from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Tag, Recipe
from recipe.serializers import TagSerializer

TAGS_URL = reverse('recipe:tag-list')


class PublicTagApiTests(TestCase):
    """Test that Tags Api is Public available."""
    def setUp(self):
        self.client = APIClient()

    def test_login_required(self):
        """Test login is required for retrieving tags"""
        res = self.client.get(TAGS_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateTagsApiTest(TestCase):
    """Test Tags Api for authorized user."""

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email='test@excel.network', password='pass123',
            name='Test FullName'
        )
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_retrieve_tags(self):
        """Test for retrieving tags"""
        Tag.objects.create(user=self.user, name='Carnivore')
        Tag.objects.create(user=self.user, name='Dessert')

        res = self.client.get(TAGS_URL)
        tags = Tag.objects.all().order_by('-name')
        serializer = TagSerializer(tags, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_limited_tags(self):
        """Test tags returned are specific for logged user"""
        user2 = get_user_model().objects.create_user(
            email='test2@excel.network', password='pass123',
            name='Test FullName 2'
        )
        Tag.objects.create(user=user2, name='Fruits')
        tag = Tag.objects.create(user=self.user, name='Soups')
        res = self.client.get(TAGS_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['name'], tag.name)

    def test_create_tag_success(self):
        """Test creating a new Tag"""
        payload = {'name': 'Test Tag'}
        self.client.post(TAGS_URL, payload)

        exists = Tag.objects.filter(user=self.user,
                                    name=payload['name']
                                    ).exists()
        self.assertTrue(exists)

    def test_create_tag_fail(self):
        """Test creating a new Tag with invalid payload"""
        payload = {'name': ''}
        res = self.client.post(TAGS_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_filter_assigned_tags(self):
        """Test to filter only tags assigend to recipes"""
        tag1 = Tag.objects.create(user=self.user, name='Breackfast')
        tag2 = Tag.objects.create(user=self.user, name='Lunch')
        recipe = Recipe.objects.create(
            title='PB&J Sandwich', cook_time_minutes='5', price=2.5,
            user=self.user
        )
        recipe.tags.add(tag1)

        res = self.client.get(TAGS_URL, {'assigned_only': 1})

        serializer1 = TagSerializer(tag1)
        serializer2 = TagSerializer(tag2)
        self.assertIn(serializer1.data, res.data)
        self.assertNotIn(serializer2.data, res.data)

    def test_unique_assigned_tags_filter(self):
        """Test filter assigend tags are unique"""
        tag = Tag.objects.create(user=self.user, name='Breackfast')
        Tag.objects.create(user=self.user, name='Lunch')
        recipe = Recipe.objects.create(
            title='PB&J Sandwich', cook_time_minutes='5', price=2.5,
            user=self.user
        )
        recipe.tags.add(tag)
        recipe2 = Recipe.objects.create(
            title='Pancakes', cook_time_minutes='15', price=4.5,
            user=self.user
        )
        recipe2.tags.add(tag)

        res = self.client.get(TAGS_URL, {'assigned_only': 1})

        self.assertEqual(len(res.data), 1)
