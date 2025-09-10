from django.contrib import admin
from .models import Product, Variation, ReviewRating, ProductGallery, InventoryLog
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
    list_display = ("name", "price", "stock", 'low_stock', "category", "modified_date", "is_available")
    list_editable = ('stock', 'is_available')
    list_filter = ('is_available',"category",)
    prepopulated_fields = {"slug": ("name",)}
    inlines = [ProductGalleryInline]

    def low_stock(self, obj):
        return obj.stock < 5  # Highlight if stock < 5
    low_stock.boolean = True
    low_stock.short_description = "Low Stock (<5)"




@admin.register(Variation)
class VariationAdmin(ModelAdmin):
    list_display = ("product", "variation_category", "variation_value", 'stock', "is_active")
    list_editable = ('stock', "is_active",)
    list_filter = ("product", "variation_category", "variation_value")



@admin.register(ProductGallery)
class ProductGalleryAdmin(ModelAdmin):
    list_display = ("product", "image")


@admin.register(ReviewRating)
class ReviewRatingAdmin(ModelAdmin):
    list_display = ("product", "rating", "user", "review")



@admin.register(InventoryLog)
class InventoryLogAdmin(ModelAdmin):
    list_display = ('product', 'variation', 'change', 'reason', 'created_at')
    list_filter = ('reason', 'created_at')
    search_fields = ('product__name', 'variation__variation_value')

    

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


