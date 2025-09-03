from django.contrib import admin
from . models import Cart,CartItem
from unfold.admin import ModelAdmin

# Register your models here.
#  CART
# ---------------------------
@admin.register(Cart)
class CartAdmin(ModelAdmin):
    list_display = ("cart_id", "date_added")


@admin.register(CartItem)
class CartItemAdmin(ModelAdmin):
    list_display = ("product", "cart", "quantity", "is_active")


# @admin.register(Cart)
# class CartAdmin(ModelAdmin):
#     list_display = ('cart_id', 'date_added')


# @admin.register(CartItem)
# class CartItemAdmin(ModelAdmin):
#     list_display = ('product', 'cart', 'quantity', 'is_active')

