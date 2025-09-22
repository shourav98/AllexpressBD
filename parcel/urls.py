from django.urls import path
from . import views
from orders import views as order_views

urlpatterns = [
    # Admin parcel management
    path('dashboard/', views.parcel_dashboard, name='parcel_dashboard'),
    path('list/', views.parcel_list, name='parcel_list'),
    path('<str:consignment_id>/', views.parcel_detail, name='parcel_detail'),
    path('<str:consignment_id>/refresh/', views.refresh_parcel_status, name='refresh_parcel_status'),
    path('<str:consignment_id>/cancel/', views.cancel_parcel, name='cancel_parcel'),
    path('bulk-actions/', views.bulk_parcel_actions, name='bulk_parcel_actions'),

    # AJAX endpoints
    path('ajax/zones/', views.get_zones_ajax, name='get_zones_ajax'),
    path('ajax/areas/', views.get_areas_ajax, name='get_areas_ajax'),

    # Legacy endpoints (from orders app - keeping for compatibility)
    path('track-parcel/<str:order_number>/', order_views.track_parcel, name='track_parcel'),
    path('pathao-webhook/', order_views.pathao_webhook, name='pathao_webhook'),
    path('batch-create-orders/', order_views.batch_create_orders, name='batch_create_orders'),
]