from django import forms
from recipes.models import Recipe
from .constants import ERROR_NO_TAGS


class RecipeAdminForm(forms.ModelForm):
    class Meta:
        model = Recipe
        fields = '__all__'

    def clean(self):
        cleaned_data = super().clean()
        tags = cleaned_data.get('tags')
        if not tags:
            raise forms.ValidationError(ERROR_NO_TAGS)
        return cleaned_data
