from django import forms
from .models import ReviewRating, Product, Variation, VariationCombination


class ReviewForm(forms.ModelForm):
    class Meta:
        model = ReviewRating
        fields = ['subject','review', 'rating']





class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ["name", "description", "price", "stock", "is_available"]


class VariationForm(forms.ModelForm):
    class Meta:
        model = Variation
        fields = ["variation_category", "variation_value", "is_active"]


class VariationCombinationForm(forms.ModelForm):
    class Meta:
        model = VariationCombination
        fields = ["size_variation", "color_variation", "stock", "is_active"]