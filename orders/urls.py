from django.urls import path
from . import views

# urlpatterns = [
#     path("place_order", views.place_order, name= "place_order"),
#     path("payments/", views.payments, name= "payments"),
#     path('payment-success/', views.payment_success, name='payment_success'),
#     path('payment-failed/', views.payment_failed, name='payment_failed'),
    
    
#     path('order-complete/<str:order_number>/', views.order_complete, name='order_complete'),
#     path('order-complete/', views.order_complete, name='order_complete'),
    
# ]



urlpatterns = [
    path('place_order/', views.place_order, name='place_order'),
    path("payments/", views.payments, name= "payments"),
    path('order-complete/<str:order_number>/', views.order_complete, name='order_complete'),
    path('payment-success/', views.payment_success, name='payment_success'),
    path('payment-failed/', views.payment_failed, name='payment_failed'),
    path('track-parcel/<str:order_number>/', views.track_parcel, name='track_parcel'),
    path('get_zones/', views.get_zones, name='get_zones'),
    path('get_areas/', views.get_areas, name='get_areas'),
    path('pathao-webhook/', views.pathao_webhook, name='pathao_webhook'),
    path('batch-create-orders/', views.batch_create_orders, name='batch_create_orders'),
    
]