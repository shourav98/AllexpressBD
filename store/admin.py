from django.contrib import admin
from .models import Product, Variation, VariationCombination, ReviewRating, ProductGallery, InventoryLog
import admin_thumbnails
from unfold.admin import ModelAdmin
from django.utils.html import format_html
from django.urls import reverse
# Register your models here.
#  PRODUCTS
# ---------------------------
@admin_thumbnails.thumbnail("image")
class ProductGalleryInline(admin.TabularInline):
    model = ProductGallery
    extra = 1

# VariationInline removed since variations are now global

class VariationCombinationInline(admin.TabularInline):
    model = VariationCombination
    extra = 1
    fields = ('size_variation', 'color_variation', 'stock', 'is_active')

@admin.register(Product)
class ProductAdmin(ModelAdmin):
    list_display = (
        "name",
        "show_images",
        "price",
        "stock",
        "low_stock_status",
        "category_or_brand",
        "modified_date",
        "is_available",
    )
    list_editable = ("stock", "is_available")
    list_filter = ("is_available", "category")
    prepopulated_fields = {"slug": ("name",)}
    inlines = [ProductGalleryInline, VariationCombinationInline]

    def get_row_css_class(self, obj):
        """Apply custom CSS class based on stock value."""
        if obj.stock == 0:
            return "row-out-of-stock"
        elif obj.stock < 5:
            return "row-low-stock"
        return ""

    def low_stock_status(self, obj):
        if obj.stock == 0:
            return format_html('<span style="color:red; font-weight:bold;">❌ Out of Stock</span>')
        elif obj.stock < 5:
            return format_html('<span style="color:orange; font-weight:bold;">⚠️ Low ({})</span>', obj.stock)
        else:
            return format_html('<span style="color:green; font-weight:bold;">✅ OK ({})</span>', obj.stock)
    low_stock_status.short_description = "Stock Status"
    low_stock_status.admin_order_field = "stock"

    def show_images(self, obj):
        if obj.images:
            return format_html(
                '<img src="{}" width="50" height="50" style="object-fit:cover;" />',
                obj.images.url,
            )
        return "No Image"
    show_images.short_description = "Image"

    # ✅ Add combined column
    def category_or_brand(self, obj):
        links = []
        if obj.category:
            cat_url = reverse("admin:category_category_change", args=[obj.category.id])
            links.append(f'<a href="{cat_url}">{obj.category}</a>')
        if obj.brand:
            brand_url = reverse("admin:category_brand_change", args=[obj.brand.id])
            links.append(f'<a href="{brand_url}">{obj.brand}</a>')
        return format_html(" / ".join(links)) if links else "—"
    category_or_brand.short_description = "Category / Brand"


    class Media:
        css = {
            "all": ("css/admin_custom.css",)
        }





@admin.register(Variation)
class VariationAdmin(ModelAdmin):
    list_display = ("variation_category", "variation_value", "is_active")
    list_editable = ("is_active",)
    list_filter = ("variation_category", "variation_value")


@admin.register(VariationCombination)
class VariationCombinationAdmin(ModelAdmin):
    list_display = ("product", "size_variation", "color_variation", "stock", "is_active")
    list_editable = ("stock", "is_active")
    list_filter = ("product", "size_variation", "color_variation")



@admin.register(ProductGallery)
class ProductGalleryAdmin(ModelAdmin):
    list_display = ("product", "image")


@admin.register(ReviewRating)
class ReviewRatingAdmin(ModelAdmin):
    list_display = ("product", "rating", "user", "review")



@admin.register(InventoryLog)
class InventoryLogAdmin(ModelAdmin):
    list_display = ('product', 'variation_combination', 'change', 'reason', 'created_at')
    list_filter = ('reason', 'created_at')
    search_fields = ('product__name', 'variation_combination__size_variation__variation_value', 'variation_combination__color_variation__variation_value')

    

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


