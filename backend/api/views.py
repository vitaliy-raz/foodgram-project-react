from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from rest_framework.decorators import action
from rest_framework import viewsets,  mixins
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from foodgram.settings import FILE_NAME
from recipes.models import (Recipe, Tag, Ingredient, Favorite,
                            RecipeIngredient, ShoppingCart)
from users.models import User, Subscribe
from .serializers import (
    UserSubscribeRepresentSerializer,
    SubscribeSerializer,
    TagSerializer,
    IngredientSerializer,
    RecipeReadSerializer,
    RecipeCreateSerializer,
    ShoppingCartSerializer,
    FavoriteSerializer,)
from api.utils import create_model_instance, delete_model_instance
from .permissions import IsAdminAuthorOrReadOnly
from .filters import IngredientFilter, RecipeFilter
from .paginations import CustomPaginator


class UserSubscribeView(APIView):

    def post(self, request, user_id):
        author = get_object_or_404(User, id=user_id)
        serializer = SubscribeSerializer(
            data={'user': request.user.id, 'author': author.id},
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete(self, request, user_id):
        author = get_object_or_404(User, id=user_id)
        if not Subscribe.objects.filter(user=request.user,
                                        author=author).exists():
            return Response(
                {'errors': 'Вы не подписаны на этого пользователя'},
                status=status.HTTP_400_BAD_REQUEST
            )
        Subscribe.objects.get(user=request.user.id,
                              author=user_id).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class UserSubscriptionsViewSet(mixins.ListModelMixin,
                               viewsets.GenericViewSet):
    serializer_class = UserSubscribeRepresentSerializer

    def get_queryset(self):
        return User.objects.filter(following__user=self.request.user)


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (AllowAny,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = (IngredientFilter,)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (AllowAny,)


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    filter_backends = (DjangoFilterBackend,)
    paginations_class = CustomPaginator
    permission_classes = (IsAdminAuthorOrReadOnly,)
    filterset_class = RecipeFilter
    http_method_names = ["get", "post", "patch", "create", "delete"]

    def get_serializer_class(self):
        if self.action in ("list", "retrieve"):
            return RecipeReadSerializer
        return RecipeCreateSerializer

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=(IsAuthenticated,)
    )
    def favorite(self, request, pk):
        recipe = get_object_or_404(Recipe, id=pk)
        if request.method == 'POST':
            return create_model_instance(request, recipe, FavoriteSerializer)

        if request.method == 'DELETE':
            error_message = 'У вас нет этого рецепта в избранном'
            return delete_model_instance(request, Favorite,
                                         recipe, error_message)

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated, ]
    )
    def shopping_cart(self, request, pk):
        recipe = get_object_or_404(Recipe, id=pk)
        if request.method == 'POST':
            return create_model_instance(request, recipe,
                                         ShoppingCartSerializer)

        if request.method == 'DELETE':
            error_message = 'У вас нет этого рецепта в списке покупок'
            return delete_model_instance(request, ShoppingCart,
                                         recipe, error_message)

    @action(detail=False, methods=["get"],
            permission_classes=(IsAuthenticated,))
    def download_shopping_cart(self, request, **kwargs):
        ingredients = (
            RecipeIngredient.objects.filter(
                recipe__shopping_recipe__user=request.user)
            .values("ingredient")
            .annotate(total_amount=Sum("amount"))
            .values_list("ingredient__name",
                         "total_amount",
                         "ingredient__measure")
        )
        file_list = []
        [
            file_list.append("{} - {} {}.".format(*ingredient))
            for ingredient in ingredients
        ]
        file = HttpResponse(
            "Cписок покупок:\n" + "\n".join(file_list),
            content_type="text/plain"
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
