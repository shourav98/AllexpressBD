from django.contrib import admin
from . models import Category

# Register your models here.
class CategoryAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('category_name',)}
    list_display = ('category_name', 'slug', 'parent', 'is_active')
    search_fields = ('category_name',)
    list_editable = ('is_active',)
admin.site.register(Category, CategoryAdmin)