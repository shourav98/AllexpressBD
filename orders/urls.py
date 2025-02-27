from django.urls import path
from . import views

urlpatterns = [
    path("place_order", views.place_order, name= "place_order"),
    path("payments/", views.payments, name= "payments"),
    path('payment-success/', views.payment_success, name='payment_success'),
    path('payment-failed/', views.payment_failed, name='payment_failed'),
    
    
    path('order-complete/<str:order_number>/', views.order_complete, name='order_complete'),
    path('order-complete/', views.order_complete, name='order_complete'),
    
]