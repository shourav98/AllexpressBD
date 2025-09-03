from django.contrib import admin
from .models import Product, Variation, ReviewRating, ProductGallery
import admin_thumbnails
from unfold.admin import ModelAdmin
# Register your models here.
#  PRODUCTS
# ---------------------------
@admin_thumbnails.thumbnail("image")
class ProductGalleryInline(admin.TabularInline):
    model = ProductGallery
    extra = 1


@admin.register(Product)
class ProductAdmin(ModelAdmin):
    list_display = ("name", "price", "stock", "category", "modified_date", "is_available")
    list_filter = ("category",)
    prepopulated_fields = {"slug": ("name",)}
    inlines = [ProductGalleryInline]


@admin.register(Variation)
class VariationAdmin(ModelAdmin):
    list_display = ("product", "variation_category", "variation_value", "is_active")
    list_editable = ("is_active",)
    list_filter = ("product", "variation_category", "variation_value")


@admin.register(ProductGallery)
class ProductGalleryAdmin(ModelAdmin):
    list_display = ("product", "image")


@admin.register(ReviewRating)
class ReviewRatingAdmin(ModelAdmin):
    list_display = ("product", "rating", "user", "review")

    

# @admin_thumbnails.thumbnail('image')
# class ProductGalleryInline(admin.TabularInline):
#     model = ProductGallery
#     extra = 1

# @admin.register(Product)
# class ProductAdmin(ModelAdmin):
#     list_display = ('name', 'price', 'stock', 'category', 'modified_date','is_available')
#     prepopulated_fields = {'slug':('name',)}
#     inlines = [ProductGalleryInline]
#     list_filter = ('category',)


# @admin.register(Variation)
# class VariationAdmin(ModelAdmin):
#     list_display = ('product', 'variation_category', 'variation_value', 'is_active')
#     list_editable = ('is_active',)
#     list_filter = ('product', 'variation_category', 'variation_value')

# @admin.register(ProductGallery)  
# class ProductGalleryAdmin(ModelAdmin):
#     list_display = ('product', 'image',)


# @admin.register(ReviewRating)  
# class ReviewRatingAdmin(ModelAdmin):
#     list_display = ('product', 'rating', 'user','review')


