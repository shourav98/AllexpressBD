# dashboard.py (main project directory)
from datetime import timedelta
from django.db.models import Sum, Count, Q, Avg
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.core.cache import cache
from django.contrib.humanize.templatetags.humanize import intcomma
from orders.models import Order, Payment, OrderProduct
from store.models import Product, Variation, VariationCombination, ReviewRating
from accounts.models import Account
import logging

logger = logging.getLogger(__name__)

def dashboard_callback(request, context):
    selected_period = request.GET.get('period', '7')
    
    try:
        period_days = int(selected_period)
    except ValueError:
        period_days = 7

    now = timezone.now()
    last_period_days = now - timedelta(days=period_days)
    last_365_days = now - timedelta(days=365)
    
    # KPI Calculations - Only cache simple data, not complex objects
    cache_key = f"dashboard_data_{request.user.id}_{selected_period}"
    cached_simple_data = cache.get(cache_key)
    
    if cached_simple_data:
        # Use cached simple data and rebuild context
        kpi_data, chart_data, table_data = cached_simple_data
    else:
        # Calculate fresh data
        kpi_data = calculate_kpi_data(period_days, last_period_days, last_365_days, now)
        chart_data = calculate_chart_data(period_days, last_365_days, now)
        table_data = calculate_table_data(last_365_days)
        
        # Cache only simple data (lists, dicts, primitives)
        simple_data = (kpi_data, chart_data, table_data)
        cache.set(cache_key, simple_data, 300)  # 5 minutes

    # Build context with fresh objects (don't cache these)
    context.update(build_context(kpi_data, chart_data, table_data, selected_period))
    
    return context

def calculate_kpi_data(period_days, last_period_days, last_365_days, now):
    """Calculate and return simple KPI data (primitives only)"""
    
    # Total Revenue
    total_revenue = Order.objects.filter(
        created_at__gte=last_365_days,
        status='Completed'
    ).aggregate(total=Sum('order_total'))['total'] or 0

    current_revenue = Order.objects.filter(
        created_at__gte=last_period_days,
        status='Completed'
    ).aggregate(total=Sum('order_total'))['total'] or 0

    previous_period_days = now - timedelta(days=period_days * 2)
    previous_revenue = Order.objects.filter(
        created_at__range=(previous_period_days, last_period_days),
        status='Completed'
    ).aggregate(total=Sum('order_total'))['total'] or 0

    revenue_change = ((current_revenue - previous_revenue) / previous_revenue * 100) if previous_revenue > 0 else (100.0 if current_revenue > 0 else 0.0)

    # Total Orders
    total_orders = Order.objects.filter(created_at__gte=last_365_days).count()
    current_orders = Order.objects.filter(created_at__gte=last_period_days).count()
    previous_orders = Order.objects.filter(
        created_at__range=(previous_period_days, last_period_days)
    ).count()

    orders_change = ((current_orders - previous_orders) / previous_orders * 100) if previous_orders > 0 else (100.0 if current_orders > 0 else 0.0)

    # New Customers
    new_customers = Account.objects.filter(
        date_joined__gte=last_365_days,
        is_active=True
    ).count()

    current_customers = Account.objects.filter(
        date_joined__gte=last_period_days,
        is_active=True
    ).count()

    previous_customers = Account.objects.filter(
        date_joined__range=(previous_period_days, last_period_days),
        is_active=True
    ).count()

    customers_change = ((current_customers - previous_customers) / previous_customers * 100) if previous_customers > 0 else (100.0 if current_customers > 0 else 0.0)

    # Average Order Value
    completed_orders = Order.objects.filter(
        created_at__gte=last_365_days,
        status='Completed'
    )
    avg_order_value = completed_orders.aggregate(avg=Avg('order_total'))['avg'] or 0

    current_avg = Order.objects.filter(
        created_at__gte=last_period_days,
        status='Completed'
    ).aggregate(avg=Avg('order_total'))['avg'] or 0

    previous_avg = Order.objects.filter(
        created_at__range=(previous_period_days, last_period_days),
        status='Completed'
    ).aggregate(avg=Avg('order_total'))['avg'] or 0

    avg_change = ((current_avg - previous_avg) / previous_avg * 100) if previous_avg > 0 else (100.0 if current_avg > 0 else 0.0)

    return {
        'total_revenue': float(total_revenue),
        'current_revenue': float(current_revenue),
        'revenue_change': revenue_change,
        'total_orders': total_orders,
        'current_orders': current_orders,
        'orders_change': orders_change,
        'new_customers': new_customers,
        'current_customers': current_customers,
        'customers_change': customers_change,
        'avg_order_value': float(avg_order_value),
        'current_avg': float(current_avg),
        'avg_change': avg_change,
        'period_days': period_days,
    }

def calculate_chart_data(period_days, last_365_days, now):
    """Calculate chart data (primitives only)"""
    
    # Sales Chart Data
    sales_data = []
    labels = []

    for i in range(period_days, -1, -1):
        date = now - timedelta(days=i)
        day_start = date.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = date.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        daily_sales = Order.objects.filter(
            created_at__range=(day_start, day_end),
            status='Completed'
        ).aggregate(total=Sum('order_total'))['total'] or 0
        
        sales_data.append(float(daily_sales))
        labels.append(date.strftime('%b %d'))

    # Product Performance
    product_performance = Product.objects.annotate(
        sales=Sum('orderproduct__total_amount', 
        filter=Q(orderproduct__order__created_at__gte=last_365_days, 
                 orderproduct__order__status='Completed'))
    ).order_by('-sales')[:10]

    product_labels = [p.name[:20] + '...' if len(p.name) > 20 else p.name for p in product_performance]
    product_data = [float(p.sales or 0) for p in product_performance]

    # Payment Methods
    payment_methods = Order.objects.filter(
        created_at__gte=last_365_days,
        status='Completed'
    ).values('payment_method').annotate(
        total=Sum('order_total')
    ).order_by('-total')

    payment_labels = [pm['payment_method'] for pm in payment_methods]
    payment_data = [float(pm['total'] or 0) for pm in payment_methods]

    # Inventory Data
    inventory_items = Product.objects.filter(is_available=True).order_by('-stock')[:15]
    inventory_labels = [item.name[:20] + '...' if len(item.name) > 20 else item.name for item in inventory_items]
    inventory_data = [float(item.stock) for item in inventory_items]

    return {
        'sales_labels': labels,
        'sales_data': sales_data,
        'product_labels': product_labels,
        'product_data': product_data,
        'payment_labels': payment_labels,
        'payment_data': payment_data,
        'inventory_labels': inventory_labels,
        'inventory_data': inventory_data,
    }

def calculate_table_data(last_365_days):
    """Calculate table data (primitives only)"""
    
    recent_orders = Order.objects.filter(
        created_at__gte=last_365_days
    ).select_related('user').order_by('-created_at')[:10]

    table_data = []
    for order in recent_orders:
        table_data.append({
            "id": order.id,
            "cells": [
                f"#{order.order_number}",
                order.full_name() or order.email,
                f"${order.order_total:,.2f}",
                order.status,
                order.created_at.strftime("%b %d, %Y")
            ]
        })
    
    return table_data

def build_context(kpi_data, chart_data, table_data, selected_period):
    """Build the final context with proper template objects"""
    
    period_footer = _("Last {} days").format(kpi_data['period_days'])
    
    kpi = [
        {
            "title": _("Total Revenue"),
            "metric": f"${kpi_data['current_revenue']:,.2f}",
            "footer": period_footer,
            "icon": "heroicons-outline:currency-dollar",
            "trend": "up" if kpi_data['revenue_change'] >= 0 else "down",
            "trend_value": f"{abs(kpi_data['revenue_change']):.1f}%",
        },
        {
            "title": _("Total Orders"),
            "metric": f"{intcomma(kpi_data['current_orders'])}",
            "footer": period_footer,
            "icon": "heroicons-outline:shopping-cart",
            "trend": "up" if kpi_data['orders_change'] >= 0 else "down",
            "trend_value": f"{abs(kpi_data['orders_change']):.1f}%",
        },
        {
            "title": _("New Customers"),
            "metric": f"{intcomma(kpi_data['current_customers'])}",
            "footer": period_footer,
            "icon": "heroicons-outline:users",
            "trend": "up" if kpi_data['customers_change'] >= 0 else "down",
            "trend_value": f"{abs(kpi_data['customers_change']):.1f}%",
        },
        {
            "title": _("Avg Order Value"),
            "metric": f"${kpi_data['current_avg']:,.2f}",
            "footer": period_footer,
            "icon": "heroicons-outline:chart-bar",
            "trend": "up" if kpi_data['avg_change'] >= 0 else "down",
            "trend_value": f"{abs(kpi_data['avg_change']):.1f}%",
        },
    ]

    charts = {
        "sales": {
            "labels": chart_data['sales_labels'],
            "datasets": [{
                "label": _("Daily Sales ($)"), 
                "data": chart_data['sales_data'],
            }],
        },
        "products": {
            "labels": chart_data['product_labels'],
            "datasets": [{
                "label": _("Sales ($)"), 
                "data": chart_data['product_data'],
            }],
        },
        "payments": {
            "labels": chart_data['payment_labels'],
            "datasets": [{
                "label": _("Revenue by Payment Method"),
                "data": chart_data['payment_data'],
            }]
        }
    }

    # Recent Customers (don't cache model instances)
    recent_customers = Account.objects.filter(
        date_joined__gte=timezone.now() - timedelta(days=365)
    ).order_by('-date_joined')[:5]

    customer_data = [
        {
            "name": customer.get_full_name() if hasattr(customer, 'get_full_name') else customer.username,
            "email": customer.email,
            "joined": customer.date_joined.strftime("%b %d, %Y"),
        }
        for customer in recent_customers
    ]

    # Low Stock Alerts (don't cache model instances)
    low_stock_products = Product.objects.filter(stock__lt=5, is_available=True)[:5]
    low_stock_variations = VariationCombination.objects.filter(stock__lt=5, is_active=True)[:5]

    # Progress Metrics
    total_orders_count = Order.objects.count()
    completed_orders_count = Order.objects.filter(status='Completed').count()
    completion_rate = (completed_orders_count / total_orders_count * 100) if total_orders_count > 0 else 0
    
    avg_rating = ReviewRating.objects.filter(status=True).aggregate(avg=Avg('rating'))['avg'] or 0
    satisfaction_rate = (avg_rating / 5 * 100) if avg_rating else 0

    progress = [
        {
            "title": _("Order Completion Rate"), 
            "description": _("Completed vs Total Orders"), 
            "value": round(completion_rate, 1)
        },
        {
            "title": _("Customer Satisfaction"), 
            "description": _("Based on product reviews"), 
            "value": round(satisfaction_rate, 1)
        },
    ]

    return {
        "kpi": kpi,
        "charts": charts,
        "table_data": table_data,
        "customer_data": customer_data,
        "low_stock_products": low_stock_products,
        "low_stock_variations": low_stock_variations,
        "progress": progress,
        "inventory_labels": chart_data['inventory_labels'],
        "inventory_data": chart_data['inventory_data'],
        "selected_period": selected_period,
    }