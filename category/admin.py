from django.contrib import admin
from . models import Category, Brand

# Register your models here.
class CategoryAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('category_name',)}
    list_display = ('category_name', 'slug', 'parent', 'is_active')
    search_fields = ('category_name',)
    list_editable = ('is_active',)
admin.site.register(Category, CategoryAdmin)


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ['brand_name', 'slug', 'is_active']
    prepopulated_fields = {'slug': ('brand_name',)}
    list_filter = ['is_active']
    search_fields = ['brand_name', 'description']