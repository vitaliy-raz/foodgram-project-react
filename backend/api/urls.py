from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (TagViewSet, IngredientViewSet,
                    RecipeViewSet, UserSubscribeView,
                    UserSubscriptionsViewSet)


router = DefaultRouter()

router.register(r"tags", TagViewSet, basename="tags")
router.register(r"ingredients", IngredientViewSet, basename="ingredients")
router.register(r"recipes", RecipeViewSet, basename="recipes")

urlpatterns = [
    path('users/subscriptions/',
         UserSubscriptionsViewSet.as_view({'get': 'list'})),
    path('users/<int:user_id>/subscribe/', UserSubscribeView.as_view()),
    path("", include(router.urls)),
    path('', include('djoser.urls')),
    path(r"auth/", include("djoser.urls.authtoken")),
]
