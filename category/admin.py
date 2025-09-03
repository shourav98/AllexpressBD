from django.contrib import admin
from . models import Category, Brand
from unfold.admin import ModelAdmin

# Register your models here.
#  CATEGORY & BRAND
# ---------------------------
@admin.register(Category)
class CategoryAdmin(ModelAdmin):
    list_display = ("category_name", "slug", "parent", "is_active")
    list_editable = ("is_active",)
    search_fields = ("category_name",)
    prepopulated_fields = {"slug": ("category_name",)}


@admin.register(Brand)
class BrandAdmin(ModelAdmin):
    list_display = ("brand_name", "slug", "is_active")
    list_filter = ("is_active",)
    search_fields = ("brand_name", "description")
    prepopulated_fields = {"slug": ("brand_name",)}

# @admin.register(Category)
# class CategoryAdmin(ModelAdmin):
#     prepopulated_fields = {'slug': ('category_name',)}
#     list_display = ('category_name', 'slug', 'parent', 'is_active')
#     search_fields = ('category_name',)
#     list_editable = ('is_active',)
#     list_display = ('category_name', 'slug', 'parent', 'is_active')
#     search_fields = ('category_name',)
#     list_editable = ('is_active',)



# @admin.register(Brand)
# class BrandAdmin(ModelAdmin):
#     list_display = ['brand_name', 'slug', 'is_active']
#     prepopulated_fields = {'slug': ('brand_name',)}
#     list_filter = ['is_active']
#     search_fields = ['brand_name', 'description']