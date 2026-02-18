from django.http import Http404
from django.shortcuts import get_object_or_404, redirect

from .models import Recipe
from api.utils import decode_recipe_hash


def recipe_by_short_link(request, short_hash):
    """ Функция редиректа на рецепт по закодированной короткой ссылке. """

    recipe_id = decode_recipe_hash(short_hash)
    if recipe_id is None:
        raise Http404
    recipe = get_object_or_404(Recipe, id=recipe_id)
    return redirect(f'/recipes/{recipe.id}/')
