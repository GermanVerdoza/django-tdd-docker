import tempfile
import os
from PIL import Image
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Recipe, Tag, Ingredient
from recipe.serializers import RecipeSerializer, RecipeDetailSerializer

RECIPES_URL = reverse('recipe:recipe-list')


def image_upload_url(recipe_id):
    """Return URL for new recipe image"""
    return reverse('recipe:recipe-upload-image', args=[recipe_id])


def sample_tag(user, name='Main Tag'):
    """Create and return a sample tag"""
    return Tag.objects.create(user=user, name=name)


def sample_ingredient(user, name='Sugar'):
    """Create and return a sample ingredient"""
    return Ingredient.objects.create(user=user, name=name)


def detail_url(recipe_id):
    """Create recipe deatial url"""
    return reverse('recipe:recipe-detail', args=[recipe_id])


def sample_recipe(user, **params):
    """Create and return a recipe"""
    defaults = {
        'title': 'Sample Recipe',
        'cook_time_minutes': 10,
        'price': 3.00
    }
    defaults.update(params)

    return Recipe.objects.create(user=user, **defaults)


class PublicRecipeApiTests(TestCase):
    """Test that Recipes Api is Public available."""
    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """Test login is required for retrieving recipes"""
        res = self.client.get(RECIPES_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateRecipesApiTest(TestCase):
    """Test Recipes Api for authorized user."""

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email='test@excel.network', password='pass123',
            name='Test FullName'
        )
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_retrieve_recipes(self):
        """Test for retrieving a list recipes"""
        sample_recipe(user=self.user, title='Pizza')
        sample_recipe(user=self.user, title='Pancake')

        res = self.client.get(RECIPES_URL)
        recipes = Recipe.objects.all().order_by('-title')
        serializer = RecipeSerializer(recipes, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_limited_recipes(self):
        """Test recipes returned are specific for logged user"""
        user2 = get_user_model().objects.create_user(
            email='test2@excel.network', password='pass123',
            name='Test FullName 2'
        )
        sample_recipe(user=user2, title='Cocktail')
        sample_recipe(user=self.user, title='Ice Cream')
        res = self.client.get(RECIPES_URL)

        recipes = Recipe.objects.filter(user=self.user).order_by('-id')
        serializer = RecipeSerializer(recipes, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data, serializer.data)

    def test_view_recipe_detail(self):
        """Test for viewing a simple recipe detail"""
        recipe = sample_recipe(user=self.user)
        recipe.tags.add(sample_tag(user=self.user))
        recipe.ingredients.add(sample_ingredient(user=self.user))

        res = self.client.get(detail_url(recipe.id))

        serializer = RecipeDetailSerializer(recipe)

        self.assertEqual(res.data, serializer.data)

    def test_create_recipe_basic(self):
        """Test creating a new Recipe"""
        payload = {'title': 'Test Recipe', 'cook_time_minutes': 30,
                   'price': 6.00}
        res = self.client.post(RECIPES_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipe = Recipe.objects.get(id=res.data['id'])
        for key in payload.keys():
            self.assertEqual(payload[key], getattr(recipe, key))

    def test_create_recipe_tags(self):
        """Test creating a new Recipe with tags"""
        tag1 = sample_tag(user=self.user, name='Fruits')
        tag2 = sample_tag(user=self.user, name='Dessert')
        payload = {'title': 'Strawberry Cream', 'cook_time_minutes': 15,
                   'price': 12.00, 'tags': [tag1.id, tag2.id]}
        res = self.client.post(RECIPES_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipe = Recipe.objects.get(id=res.data['id'])
        tags = recipe.tags.all()

        self.assertEqual(tags.count(), 2)
        self.assertIn(tag1, tags)
        self.assertIn(tag2, tags)

    def test_create_recipe_ingredients(self):
        """Test creating a new Recipe with ingredients"""
        ingredient1 = sample_ingredient(user=self.user, name='Bread')
        ingredient2 = sample_ingredient(user=self.user, name='Jelly')

        payload = {'title': 'Jelly sandwich', 'cook_time_minutes': 5,
                   'price': 1.00,
                   'ingredients': [ingredient1.id, ingredient2.id]}
        res = self.client.post(RECIPES_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipe = Recipe.objects.get(id=res.data['id'])
        ingredients = recipe.ingredients.all()

        self.assertEqual(ingredients.count(), 2)
        self.assertIn(ingredient1, ingredients)
        self.assertIn(ingredient2, ingredients)

    def test_partial_update_recipe(self):
        """Test Upadte with patch"""
        recipe = sample_recipe(user=self.user)
        recipe.tags.add(sample_tag(user=self.user))
        new_tag = sample_tag(user=self.user, name="Ramen")

        payload = {'title': 'Spicy Miso', 'tags': [new_tag.id]}

        self.client.patch(detail_url(recipe.id), payload)

        recipe.refresh_from_db()

        self.assertEqual(recipe.title, payload['title'])
        tags = recipe.tags.all()
        self.assertEqual(len(tags), 1)
        self.assertIn(new_tag, tags)

    def test_full_update_recipe(self):
        """Test Upadte with put"""
        recipe = sample_recipe(user=self.user)
        recipe.tags.add(sample_tag(user=self.user))

        payload = {'title': 'Ravioli bolognese', 'cook_time_minutes': 25,
                   'price': 10.00}

        self.client.put(detail_url(recipe.id), payload)
        recipe.refresh_from_db()
        self.assertEqual(recipe.title, payload['title'])
        self.assertEqual(recipe.cook_time_minutes,
                         payload['cook_time_minutes'])
        self.assertEqual(recipe.price, payload['price'])
        tags = recipe.tags.all()
        self.assertEqual(len(tags), 0)


class RecipeImageUploadTest(TestCase):
    """Test for RecipeImageUpload."""

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            'user@mail.com',
            'testpass'
        )
        self.client.force_authenticate(self.user)
        self.recipe = sample_recipe(user=self.user)

    def tearDown(self):
        self.recipe.image.delete()

    def test_upload_image_to_recipe(self):
        """Test uploading new image to recipe"""
        url = image_upload_url(self.recipe.id)
        with tempfile.NamedTemporaryFile(suffix='.jpg') as ntf:
            img = Image.new('RGB', (10, 10))
            img.save(ntf, format='JPEG')
            ntf.seek(0)
            res = self.client.post(url, {'image': ntf}, format='multipart')

        self.recipe.refresh_from_db()

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('image', res.data)
        self.assertTrue(os.path.exists(self.recipe.image.path))

    def test_upload_image_bad(self):
        """Test uploading an invalid image to recipe"""
        url = image_upload_url(self.recipe.id)
        res = self.client.post(url, {'image': 'notimage'}, format='multipart')

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_filter_recipe_by_tag(self):
        """Test returnig specific tagged recipes"""
        recipe1 = sample_recipe(user=self.user, title='Caesar Salad')
        recipe2 = sample_recipe(user=self.user, title='Tofu Treats')
        tag1 = sample_tag(user=self.user, name='Vegan')
        tag2 = sample_tag(user=self.user, name='Vegeterian')
        recipe1.tags.add(tag1)
        recipe2.tags.add(tag2)
        recipe3 = sample_recipe(user=self.user, title='Lasagne')

        res = self.client.get(RECIPES_URL, {'tags': f'{tag1.id},{tag2.id}'})

        serializer1 = RecipeSerializer(recipe1)
        serializer2 = RecipeSerializer(recipe2)
        serializer3 = RecipeSerializer(recipe3)

        self.assertIn(serializer1.data, res.data)
        self.assertIn(serializer2.data, res.data)
        self.assertNotIn(serializer3.data, res.data)

    def test_filter_recipe_by_ingredient(self):
        """Test returnig recipes with specific ingredients"""
        recipe1 = sample_recipe(user=self.user, title='Italian Pizza')
        recipe2 = sample_recipe(user=self.user, title='Speciale Pizza')
        ingredient1 = sample_ingredient(user=self.user,
                                        name='Mozzarela Cheesse')
        ingredient2 = sample_ingredient(user=self.user, name='Peperoni')
        recipe1.ingredients.add(ingredient1)
        recipe2.ingredients.add(ingredient2)
        recipe3 = sample_recipe(user=self.user, title='Lasagne')

        res = self.client.get(RECIPES_URL,
                              {'ingredients':
                               f'{ingredient1.id},{ingredient2.id}'})

        serializer1 = RecipeSerializer(recipe1)
        serializer2 = RecipeSerializer(recipe2)
        serializer3 = RecipeSerializer(recipe3)

        self.assertIn(serializer1.data, res.data)
        self.assertIn(serializer2.data, res.data)
        self.assertNotIn(serializer3.data, res.data)
