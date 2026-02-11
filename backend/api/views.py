import datetime

from django.http import HttpResponse
from django.db.models import (Count, Exists, OuterRef, Value,
                              BooleanField, Prefetch, Subquery, Sum)
from djoser.views import UserViewSet as DjoserViewSet
from rest_framework import status, viewsets, filters
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from .serializers import (IngredientSerializer, User,
                          UserBaseSerializer, UserSerializerSetAndDelAvatar,
                          UserSerializerWithRecipeCount,
                          FollowSerializer, RecipeFullSerializer,
                          RecipeFavoriteSerializer,
                          RecipeCreateSerializer,
                          RecipeReducedOutputSerializer,
                          RecipeShoppingCartSerializer,
                          RecipeUpdateSerializer, TagSerializer)

from recipes.models import (Ingredient, Recipe, RecipeFavorite,
                            RecipeIngredient, ShoppingCart, Tag)
from recipes.constants import (ERROR_AVATAR_IS_NOT_FOUND,
                               ERROR_EMPTY_SHOPPING_CART,
                               ERROR_NO_DATA, ERROR_NO_FOLLOW,
                               ERROR_NO_RECIPE_IN_FAVORITE,
                               ERROR_NO_RECIPE_IN_SHOPPING_CART)
from .filters import NameSearchFilter, RecipeFilter
from .permissions import IsOwner
from .utils import generate_pdf_shopping_cart, encode_recipe_id


class UserViewSet(DjoserViewSet):
    pagination_class = LimitOffsetPagination
    http_method_names = ['get', 'post', 'put', 'delete']

    def get_permissions(self):
        if self.action in ('me', 'me_avatar', 'subscribe', 'subscriptions'):
            return (IsAuthenticated(),)
        elif self.action in ('list', 'create', 'retrieve'):
            return (AllowAny(),)
        return super().get_permissions()

    def get_serializer_class(self, *args, **kwargs):
        if self.action == 'me':
            return UserBaseSerializer
        if self.action == 'me_avatar':
            return UserSerializerSetAndDelAvatar
        if self.action == 'subscribe':
            return FollowSerializer
        if self.action == 'subscriptions':
            return UserSerializerWithRecipeCount
        return super().get_serializer_class(*args, **kwargs)

    def get_queryset(self, recipes_limit=None):
        base_queryset = User.objects.all()
        queryset = base_queryset.annotate(
            recipes_count=Count('recipes', distinct=True)
        )
        if recipes_limit is not None and recipes_limit > 0:
            subquery = Recipe.objects.filter(
                author_id=OuterRef('pk')
            ).order_by('-pub_date')[:recipes_limit]
            recipes_prefetch = Prefetch(
                'recipes',
                queryset=Recipe.objects.filter(
                    id__in=Subquery(subquery.values('id'))
                ),
                to_attr='limited_recipes'
            )
            queryset = queryset.prefetch_related(recipes_prefetch)
        else:
            queryset = queryset.prefetch_related('recipes')
        return queryset

    @action(detail=False, methods=('put', 'delete', ),
            url_path='me/avatar', url_name='me_avatar')
    def me_avatar(self, request):
        if request.method == 'PUT':
            if 'avatar' not in request.data:
                return Response(
                    {'avatar': [ERROR_NO_DATA]},
                    status=status.HTTP_400_BAD_REQUEST
                )
            serializer = self.get_serializer_class()(request.user,
                                                     data=request.data,
                                                     partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        elif request.method == 'DELETE':
            if request.user.avatar:
                request.user.avatar.delete(save=True)
                return Response(status=status.HTTP_204_NO_CONTENT)
            return Response(
                {'detail': [ERROR_AVATAR_IS_NOT_FOUND]},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=True, methods=('post', 'delete',),
            url_path='subscribe', url_name='subscribe')
    def subscribe(self, request, *args, **kwargs):
        user_being_followed = self.get_object()
        if request.method == 'POST':
            recipes_limit = request.query_params.get('recipes_limit')
            if recipes_limit is not None:
                recipes_limit = int(recipes_limit)
            serializer = self.get_serializer(data={
                'user_being_followed': user_being_followed.id,
            }, context={'request': request})

            serializer.is_valid(raise_exception=True)
            serializer.save()
            user_serializer = UserSerializerWithRecipeCount(
                user_being_followed, context={'request': request}
            )
            return Response(user_serializer.data,
                            status=status.HTTP_201_CREATED)
        elif request.method == 'DELETE':
            user_being_followed = self.get_object()
            user_is_following = request.user
            is_subscribed = user_is_following.following.filter(
                user_being_followed=user_being_followed).exists()
            if is_subscribed:
                user_is_following.following.filter(
                    user_being_followed=user_being_followed).delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            else:
                return Response(
                    {'user_being_followed': [ERROR_NO_FOLLOW]},
                    status=status.HTTP_400_BAD_REQUEST
                )

    @action(detail=False, methods=('get',),
            url_path='subscriptions', url_name='subscriptions')
    def subscriptions(self, request, *args, **kwargs):
        recipes_limit = request.query_params.get('recipes_limit')
        if recipes_limit is not None:
            recipes_limit = int(recipes_limit)
        followed_users_ids = request.user.following.values_list(
            'user_being_followed', flat=True)
        followed_users = self.get_queryset(recipes_limit=recipes_limit).filter(
            id__in=followed_users_ids)

        page = self.paginate_queryset(followed_users)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(followed_users, many=True)
        return Response(serializer.data, context={'request': request},
                        status=status.HTTP_200_OK)


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (AllowAny,)
    filter_backends = (NameSearchFilter,)
    search_fields = ('^name',)
    pagination_class = None


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (AllowAny,)
    pagination_class = None


class RecipeViewSet(viewsets.ModelViewSet):
    http_method_names = ['get', 'post', 'patch', 'delete']
    pagination_class = LimitOffsetPagination
    filter_backends = (filters.SearchFilter, DjangoFilterBackend,
                       filters.OrderingFilter)
    filterset_class = RecipeFilter

    def get_permissions(self):
        if self.action in ('list', 'retrieve'):
            return (AllowAny(),)
        elif self.action in ('create',):
            return (IsAuthenticated(),)
        elif self.action in ('partial_update', 'destroy'):
            return (IsAuthenticated(), IsOwner(),)
        return super().get_permissions()

    def get_queryset(self):
        user = self.request.user
        base_queryset = Recipe.objects.select_related(
            'author'
        ).prefetch_related(
            'tags', 'recipeingredients__ingredient')
        if user.is_authenticated:
            favorite_subquery = RecipeFavorite.objects.filter(
                recipe=OuterRef('pk'),
                user=user
            )
            shopping_cart_subquery = ShoppingCart.objects.filter(
                recipe=OuterRef('pk'),
                user=user
            )
            return base_queryset.annotate(
                is_favorited=Exists(favorite_subquery),
                is_in_shopping_cart=Exists(shopping_cart_subquery)
            )
        else:
            return base_queryset.annotate(
                is_favorited=Value(False, output_field=BooleanField()),
                is_in_shopping_cart=Value(False, output_field=BooleanField())
            )

    def get_shopping_cart_queryset(self):
        user = self.request.user
        shopping_cart_queryset = RecipeIngredient.objects.filter(
            recipe__shopping_cart_recipes__user=user
        ).values(
            'ingredient__name', 'ingredient__measurement_unit'
        ).annotate(
            total_amount=Sum('amount')
        ).order_by('ingredient__name')
        return shopping_cart_queryset

    def get_serializer_class(self):
        if self.action in ('retrieve', 'list'):
            return RecipeFullSerializer
        elif self.action == 'create':
            return RecipeCreateSerializer
        elif self.action in ('partial_update'):
            return RecipeUpdateSerializer
        return RecipeFullSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        recipe = self.get_queryset().get(pk=serializer.instance.pk)
        recipe_serializer = RecipeFullSerializer(
            recipe, context={'request': request}
        )
        return Response(recipe_serializer.data, status=status.HTTP_201_CREATED)

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance,
                                         data=request.data,
                                         partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        recipe = self.get_queryset().get(pk=serializer.instance.pk)
        recipe_serializer = RecipeFullSerializer(
            recipe, context={'request': request}
        )
        return Response(recipe_serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['get'],
            url_path='get-link',
            url_name='get-link',
            permission_classes=[AllowAny])
    def get_short_link(self, request, *args, **kwargs):
        recipe = self.get_object()
        short_hash = encode_recipe_id(recipe.id)
        short_link = request.build_absolute_uri(f's/{short_hash}')
        return Response({'short-link': short_link}, status=status.HTTP_200_OK)

    @action(detail=True, methods=('post', 'delete',),
            url_path='favorite',
            url_name='favorite',
            permission_classes=(IsAuthenticated,))
    def favorite(self, request, *args, **kwargs):
        recipe = self.get_object()
        if request.method == 'POST':
            serializer = RecipeFavoriteSerializer(data={
                'recipe': recipe.id,
            }, context={'request': request})
            serializer.is_valid(raise_exception=True)
            serializer.save()
            recipe_serializer = RecipeReducedOutputSerializer(
                recipe, context={'request': request}
            )
            return Response(recipe_serializer.data,
                            status=status.HTTP_201_CREATED)
        elif request.method == 'DELETE':
            recipe = self.get_object()
            user = request.user
            is_favorited = user.favorite_recipes.filter(recipe=recipe).exists()
            if is_favorited:
                user.favorite_recipes.filter(recipe=recipe).delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            else:
                return Response(
                    {'recipe': [ERROR_NO_RECIPE_IN_FAVORITE]},
                    status=status.HTTP_400_BAD_REQUEST
                )

    @action(detail=True, methods=('post', 'delete',),
            url_path='shopping_cart',
            url_name='shopping_cart',
            permission_classes=(IsAuthenticated,))
    def shopping_cart(self, request, *args, **kwargs):
        recipe = self.get_object()
        if request.method == 'POST':
            print('shoping_cart post')
            serializer = RecipeShoppingCartSerializer(data={
                'recipe': recipe.id,
            }, context={'request': request})
            serializer.is_valid(raise_exception=True)
            serializer.save()
            print('after serializer save')
            recipe_serializer = RecipeReducedOutputSerializer(
                recipe, context={'request': request}
            )
            return Response(recipe_serializer.data,
                            status=status.HTTP_201_CREATED)
        elif request.method == 'DELETE':
            recipe = self.get_object()
            user = request.user
            if recipe.is_in_shopping_cart:
                user.shopping_cart_recipes.filter(recipe=recipe).delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            else:
                return Response(
                    {'recipe': [ERROR_NO_RECIPE_IN_SHOPPING_CART]},
                    status=status.HTTP_400_BAD_REQUEST
                )

    @action(detail=False, methods=('get',),
            url_path='download_shopping_cart',
            url_name='download_shopping_cart',
            permission_classes=(IsAuthenticated,))
    def download_shopping_cart(self, request, *args, **kwargs):
        shopping_cart_to_download = self.get_shopping_cart_queryset()
        if not shopping_cart_to_download:
            return Response({'detail': [ERROR_EMPTY_SHOPPING_CART]},
                            status=400)
        pdf = generate_pdf_shopping_cart(
            shopping_cart=shopping_cart_to_download)
        response = HttpResponse(pdf, content_type='application/pdf')
        current_date = datetime.datetime.now().strftime("%Y%m%d")
        filename = f'shopping_list_{current_date}.pdf'
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
