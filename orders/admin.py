from django.contrib import admin
from .models import Payment, Order, OrderProduct
from unfold.admin import ModelAdmin
from django.utils.html import format_html

# Register your models here.
#  ORDERS & PAYMENTS
# ---------------------------
@admin.register(Order)
class OrderAdmin(ModelAdmin):
    list_display = ("order_number", "order_total", "full_name", "phone", "payment_method", "status")
    list_filter = ("created_at", "status", "phone", "order_number")
    list_editable = ("status",)  # ✅ makes status editable from list view






@admin.register(OrderProduct)
class OrderProductAdmin(ModelAdmin):
    list_display = ("order_number", "product", "product_images", "color", "size", "quantity", "total_amount")
    list_filter = ("created_at", "product", "order")

    def order_number(self, obj):
        return obj.order.order_number if obj.order else "-"
    order_number.short_description = "Order Number"

    def product_images(self, obj):
        if obj.product and obj.product.images:
            return format_html('<img src="{}" width="50" height="50" style="object-fit:cover;" />', obj.product.images.url)
        return "No Image"
    product_images.short_description = "Image"




@admin.register(Payment)
class PaymentAdmin(ModelAdmin):
    list_display = ("payment_id", "amount_paid", "payment_method", "status")
    list_filter = ("created_at", "status", "payment_method", "payment_id")
    


    
