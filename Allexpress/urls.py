from django.contrib import admin
from django.urls import path, include
from . import views
from django.conf.urls.static import static
from django.conf import settings

urlpatterns = [
    path('admin/', admin.site.urls),
    path("",views.home, name= "home"),
    path("store/",include('store.urls')),
    path("cart/",include('carts.urls')),
    path("accounts/",include('accounts.urls')),
    
    path('orders/', include('orders.urls')),

    path('parcel/', include('parcel.urls')),

    path('returns/', views.returns, name='returns'),
    path('shipping/', views.shipping, name='shipping'),
    path('offers/', views.offers, name='offers'),
    path('size-charts/', views.size_charts, name='size_charts'),
    path('gift-vouchers/', views.gift_vouchers, name='gift_vouchers'),
    path('about/', views.about, name='about'),
    path('privacy/', views.privacy, name='privacy'),
    path('terms/', views.terms, name='terms'),
    path('warranty/', views.warranty, name='warranty'),


    path('brand/<slug:brand_slug>/', views.products_by_brand, name='products_by_brand'),  # New URL


] + static(settings.MEDIA_URL, document_root = settings.MEDIA_ROOT)
