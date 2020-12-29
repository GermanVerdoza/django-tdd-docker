from rest_framework import viewsets, mixins
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated

from recipe import serializers
from core.models import Tag, Ingredient


class BaseRecipeAttrsViewset(viewsets.GenericViewSet,
                             mixins.ListModelMixin,
                             mixins.CreateModelMixin):
    """Base class for use in the viewsets for user"""
    authentication_classes = (TokenAuthentication, )
    permission_classes = (IsAuthenticated, )

    def get_queryset(self):
        """Return objects only for current authenticated user"""
        return self.queryset.filter(user=self.request.user)

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
