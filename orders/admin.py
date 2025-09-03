from django.contrib import admin
from .models import Payment, Order, OrderProduct
from unfold.admin import ModelAdmin

# Register your models here.
#  ORDERS & PAYMENTS
# ---------------------------
@admin.register(Order)
class OrderAdmin(ModelAdmin):
    list_display = ("order_number", "order_total", "full_name", "phone", "payment_method", "status")
    list_filter = ("created_at", "status", "phone", "order_number")


@admin.register(OrderProduct)
class OrderProductAdmin(ModelAdmin):
    list_display = ("order", "product", "color", "size", "quantity", "total_amount")
    list_filter = ("created_at", "product", "order")


@admin.register(Payment)
class PaymentAdmin(ModelAdmin):
    list_display = ("payment_id", "amount_paid", "payment_method", "status")
    list_filter = ("created_at", "status", "payment_method", "payment_id")

    
# @admin.register(Order)
# class OrderAdmin(ModelAdmin):
#     list_display = ('order_number', 'order_total', 'full_name', 'phone', 'payment_method', 'status')
    
#     list_filter = ('created_at','status', 'phone','order_number' )
    

# @admin.register(OrderProduct) 
# class OrderProductAdmin(ModelAdmin):
#     list_display = ('order', 'product', 'color', 'size', 'quantity', 'total_amount')
    
#     list_filter = ('created_at','product','order')

# @admin.register(Payment)    
# class PaymentAdmin(ModelAdmin):
#     list_display = ('payment_id', 'amount_paid', 'payment_method', 'status')
    
#     list_filter = ('created_at','status', 'payment_method','payment_id' )
    
