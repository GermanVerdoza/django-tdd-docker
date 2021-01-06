from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import viewsets, mixins, status
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated

from recipe import serializers
from core.models import Tag, Ingredient, Recipe


class BaseRecipeAttrsViewset(viewsets.GenericViewSet,
                             mixins.ListModelMixin,
                             mixins.CreateModelMixin):
    """Base class for use in the viewsets for user"""
    authentication_classes = (TokenAuthentication, )
    permission_classes = (IsAuthenticated, )

    def get_queryset(self):
        """Return objects only for current authenticated user"""
        assigned_only = bool(
            int(self.request.query_params.get('assigned_only', '0'))
        )
        queryset = self.queryset
        if assigned_only:
            queryset = queryset.filter(recipe__isnull=False)
        return queryset.filter(user=self.request.user).distinct()

    def perform_create(self, serializer):
        """Create a new object and assign to authenticated user"""
        serializer.save(user=self.request.user)


class TagViewSet(BaseRecipeAttrsViewset):
    """Manage Tags in database"""
    queryset = Tag.objects.all().order_by('-name')
    serializer_class = serializers.TagSerializer


class IngredientViewSet(BaseRecipeAttrsViewset):
    """Manage ingredients in database"""
    queryset = Ingredient.objects.all().order_by('-name')
    serializer_class = serializers.IngredientSerializer


class RecipeViewSet(viewsets.ModelViewSet):
    """Manafe Recipes in the database."""
    queryset = Recipe.objects.all().order_by('-title')
    serializer_class = serializers.RecipeSerializer
    authentication_classes = (TokenAuthentication, )
    permission_classes = (IsAuthenticated, )

    def _params_to_int(self, qs):
        """Convert string of ID's to an integer list"""
        return [int(str_id) for str_id in qs.split(',')]

    def get_queryset(self):
        """Return objects only for current authenticated user"""
        tags = self.request.query_params.get('tags', '')
        ingredients = self.request.query_params.get('ingredients', '')
        queryset = self.queryset
        if tags:
            tag_ids = self._params_to_int(tags)
            queryset = queryset.filter(tags__id__in=tag_ids)
        if ingredients:
            ingredient_ids = self._params_to_int(ingredients)
            queryset = queryset.filter(ingredients__id__in=ingredient_ids)
        return queryset.filter(user=self.request.user)

    def get_serializer_class(self):
        """Return the appropiate serializer class"""
        if self.action == 'retrieve':
            return serializers.RecipeDetailSerializer
        elif self.action == 'upload_image':
            return serializers.RecipeImageSerializer
        return self.serializer_class

    def perform_create(self, serializer):
        """Create new Recipe for logged user"""
        serializer.save(user=self.request.user)

    @action(methods=['POST'], detail=True, url_path='upload-image')
    def upload_image(self, request, pk=None):
        """Action to upload recipe's image"""
        recipe = self.get_object()
        serializer = self.get_serializer(
            recipe,
            data=request.data
        )
        if serializer.is_valid():
            serializer.save()
            return Response(
                serializer.data, status=status.HTTP_200_OK
            )
        return Response(
            serializer.errors, status=status.HTTP_400_BAD_REQUEST
        )
