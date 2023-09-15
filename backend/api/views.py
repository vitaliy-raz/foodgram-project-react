from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from rest_framework.decorators import action
from rest_framework import viewsets, permissions, filters, mixins
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import AllowAny, IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend

from foodgram.settings import FILE_NAME
from recipes.models import Recipe, Tag, Ingredient, RecipeIngredient
from users.models import User, Subscribe
from .serializers import (
    UserSerializer,
    SubscribeSerializer,
    TagSerializer,
    IngredientSerializer,
    RecipeReadSerializer,
    RecipeCreateSerializer,
    FavoriteSerializer,
)
from .permissions import IsAdminOrReadOnly, IsAuthorOrReadOnly
from .filters import IngredientFilter, RecipeFilter
from .paginations import CustomPaginator


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (IsAuthorOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = (IngredientFilter,)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (IsAuthorOrReadOnly,)


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    filter_backends = (DjangoFilterBackend,)
    paginations_class = CustomPaginator
    permission_classes = (
        IsAuthorOrReadOnly,
        IsAdminOrReadOnly,
    )
    filterset_class = RecipeFilter
    http_method_names = ["get", "post", "patch", "create", "delete"]

    def get_serializer_class(self):
        if self.action in ("list", "retrieve"):
            return RecipeReadSerializer
        return RecipeCreateSerializer

    @action(detail=False, methods=["get"], permission_classes=(IsAuthenticated,))
    def download_shopping_cart(self, request, **kwargs):
        ingredients = (
            RecipeIngredient.objects.filter(recipe__shopping_recipe__user=request.user)
            .values("ingredient")
            .annotate(total_amount=Sum("amount"))
            .values_list("ingredient__name", "total_amount", "ingredient__measure")
        )
        file_list = []
        [
            file_list.append("{} - {} {}.".format(*ingredient))
            for ingredient in ingredients
        ]
        file = HttpResponse(
            "Cписок покупок:\n" + "\n".join(file_list), content_type="text/plain"
        )
        file["Content-Disposition"] = f"attachment; filename={FILE_NAME}"
        return file


class FavoriteViewSet(viewsets.ModelViewSet):
    serializer_class = FavoriteSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        recipe_id = self.kwargs.get("recipe_id")
        recipe = get_object_or_404(Recipe, id=recipe_id)
        return recipe.favorites.all()
