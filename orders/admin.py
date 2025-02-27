from django.contrib import admin
from .models import Payment, Order, OrderProduct

# Register your models here.
# class OrderAdmin
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'order_total', 'full_name', 'phone', 'payment_method', 'status')
    
    list_filter = ('created_at','status', 'phone','order_number' )
    
    
class OrderProductAdmin(admin.ModelAdmin):
    list_display = ('order', 'product', 'color', 'size', 'quantity', 'total_amount')
    
    list_filter = ('created_at','product','order')
    
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('payment_id', 'amount_paid', 'payment_method', 'status')
    
    list_filter = ('created_at','status', 'payment_method','payment_id' )
    
admin.site.register(Payment, PaymentAdmin)
admin.site.register(Order,OrderAdmin)
admin.site.register(OrderProduct, OrderProductAdmin)