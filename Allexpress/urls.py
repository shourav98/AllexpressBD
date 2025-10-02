from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect
from django.http import JsonResponse, HttpResponse
import csv
from reportlab.pdfgen import canvas
from io import BytesIO
from django.conf import settings
from django.conf.urls.static import static
from . import views

def export_dashboard(request):
    format_type = request.GET.get('format', 'csv')
    period = request.GET.get('period', '7')
    
    if format_type == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="dashboard_export_{period}.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['Metric', 'Value', 'Period'])
        # Add your data here
        
        return response
        
    elif format_type == 'pdf':
        buffer = BytesIO()
        p = canvas.Canvas(buffer)
        p.drawString(100, 750, f"Dashboard Export - Last {period} days")
        p.showPage()
        p.save()
        
        response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="dashboard_export_{period}.pdf"'
        return response

urlpatterns = [
    # Admin URLs - THIS IS MISSING IN YOUR CURRENT CONFIG
    path('admin/', admin.site.urls),
    path('admin/export-dashboard/', export_dashboard, name='export_dashboard'),
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
