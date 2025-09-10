from datetime import timedelta
from django.db.models import Sum, Count, Q, Avg
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from orders.models import Order, Payment, OrderProduct
from store.models import Product, Variation, ReviewRating
from accounts.models import Account
from django.contrib.humanize.templatetags.humanize import intcomma

def dashboard_callback(request, context):
    now = timezone.now()
    last_7_days = now - timedelta(days=7)
    last_30_days = now - timedelta(days=30)
    last_90_days = now - timedelta(days=90)
    last_365_days = now - timedelta(days=365)
    
    # Current month range
    current_month_start = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    previous_month_start = (current_month_start - timedelta(days=1)).replace(day=1)
    
    # Total Revenue Calculations
    total_revenue = Order.objects.filter(
        created_at__gte=last_365_days, 
        status='Completed'
    ).aggregate(total=Sum('order_total'))['total'] or 0
    
    previous_revenue = Order.objects.filter(
        created_at__gte=last_365_days - timedelta(days=7),
        created_at__lt=last_365_days,
        status='Completed'
    ).aggregate(total=Sum('order_total'))['total'] or 0
    
    revenue_change = ((total_revenue - previous_revenue) / previous_revenue * 100) if previous_revenue > 0 else 0

    # Total Orders
    total_orders = Order.objects.filter(
        created_at__gte=last_365_days
    ).count()
    
    previous_orders = Order.objects.filter(
        created_at__gte=last_365_days - timedelta(days=7),
        created_at__lt=last_365_days
    ).count()
    
    orders_change = ((total_orders - previous_orders) / previous_orders * 100) if previous_orders > 0 else 0

    # New Customers
    new_customers = Account.objects.filter(
        date_joined__gte=last_365_days,
        is_active=True
    ).count()
    
    previous_customers = Account.objects.filter(
        date_joined__gte=last_365_days - timedelta(days=7),
        date_joined__lt=last_365_days,
        is_active=True
    ).count()
    
    customers_change = ((new_customers - previous_customers) / previous_customers * 100) if previous_customers > 0 else 0

    # Average Order Value
    completed_orders = Order.objects.filter(
        created_at__gte=last_365_days,
        status='Completed'
    )
    if completed_orders.exists():
        avg_order_value = completed_orders.aggregate(
            avg=Avg('order_total')
        )['avg'] or 0
    else:
        avg_order_value = 0
    
    previous_avg = Order.objects.filter(
        created_at__gte=last_365_days - timedelta(days=7),
        created_at__lt=last_365_days,
        status='Completed'
    ).aggregate(avg=Avg('order_total'))['avg'] or 0
    
    avg_change = ((avg_order_value - previous_avg) / previous_avg * 100) if previous_avg > 0 else 0

    # KPI Cards with trend indicators
    kpi = [
        {
            "title": _("Total Revenue"),
            "metric": f"${total_revenue:,.2f}",
            "footer": _("Last 7 days"),
            "icon": "heroicons-outline:currency-dollar",
            "trend": "up" if revenue_change >= 0 else "down",
            "trend_value": f"{abs(revenue_change):.1f}%",
            "color": "green" if revenue_change >= 0 else "red",
        },
        {
            "title": _("Total Orders"),
            "metric": f"{intcomma(total_orders)}",
            "footer": _("Last 7 days"),
            "icon": "heroicons-outline:shopping-cart",
            "trend": "up" if orders_change >= 0 else "down",
            "trend_value": f"{abs(orders_change):.1f}%",
            "color": "green" if orders_change >= 0 else "red",
        },
        {
            "title": _("New Customers"),
            "metric": f"{intcomma(new_customers)}",
            "footer": _("Last 7 days"),
            "icon": "heroicons-outline:users",
            "trend": "up" if customers_change >= 0 else "down",
            "trend_value": f"{abs(customers_change):.1f}%",
            "color": "green" if customers_change >= 0 else "red",
        },
        {
            "title": _("Avg Order Value"),
            "metric": f"${avg_order_value:,.2f}",
            "footer": _("Last 7 days"),
            "icon": "heroicons-outline:chart-bar",
            "trend": "up" if avg_change >= 0 else "down",
            "trend_value": f"{abs(avg_change):.1f}%",
            "color": "green" if avg_change >= 0 else "red",
        },
    ]

    # Sales Chart Data (Last 30 days daily sales)
    sales_data = []
    labels = []
    
    for i in range(30, -1, -1):
        date = now - timedelta(days=i)
        day_start = date.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = date.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        daily_sales = Order.objects.filter(
            created_at__range=(day_start, day_end),
            status='Completed'
        ).aggregate(total=Sum('order_total'))['total'] or 0
        
        sales_data.append(float(daily_sales))
        labels.append(date.strftime('%b %d'))

    chart_data = {
        "sales": {
            "labels": labels,
            "datasets": [{
                "label": _("Daily Sales ($)"), 
                "data": sales_data,
                "borderColor": "#3b82f6",
                "backgroundColor": "rgba(59, 130, 246, 0.1)",
                "fill": True,
                "tension": 0.4,
            }],
        }
    }

    # Product Performance Chart
    product_performance = Product.objects.annotate(
        sales=Sum('orderproduct__total_amount', 
        filter=Q(orderproduct__order__created_at__gte=last_365_days, orderproduct__order__status='Completed'))
    ).order_by('-sales')[:10]

    chart_data["products"] = {
        "labels": [p.name[:20] + '...' if len(p.name) > 20 else p.name for p in product_performance],
        "datasets": [{
            "label": _("Sales ($)"), 
            "data": [p.sales or 0 for p in product_performance],
            "backgroundColor": [
                "#3b82f6", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6",
                "#06b6d4", "#84cc16", "#f97316", "#ec4899", "#64748b"
            ],
        }],
    }

    # Top Orders Table
    top_orders = Order.objects.filter(
        created_at__gte=last_365_days,
        status='Completed'
    ).select_related('user').order_by('-order_total')[:10]

    table_data = [
        {
            "id": order.id,
            "cells": [
                f"#{order.order_number}",
                order.full_name() or order.email,
                f"${order.order_total:,.2f}",
                order.status,
                order.created_at.strftime("%b %d, %Y")
            ]
        } for order in top_orders
    ]

    # Recent Customers
    recent_customers = Account.objects.filter(
        date_joined__gte=last_365_days
    ).order_by('-date_joined')[:5]

    customer_data = [
        {
            "name": customer.full_name(),
            "email": customer.email,
            "joined": customer.date_joined.strftime("%b %d, %Y"),
            "orders": Order.objects.filter(user=customer).count()
        }
        for customer in recent_customers
    ]

    # Low Stock Alerts
    low_stock_products = Product.objects.filter(stock__lt=5, is_available=True)[:5]
    low_stock_variations = Variation.objects.filter(stock__lt=5, is_active=True)[:5]

    # Progress items (you can replace with actual calculations)
    total_completed_orders = Order.objects.filter(status='Completed').count()
    total_orders_count = Order.objects.count()
    completion_rate = (total_completed_orders / total_orders_count * 100) if total_orders_count > 0 else 0
    
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

     # Payment methods distribution for a pie chart
    payment_methods = Order.objects.filter(
        created_at__gte=last_365_days
    ).values('payment_method').annotate(
        count=Count('id'),
        total=Sum('order_total')
    ).order_by('-total')
    
    # Prepare payment data for chart
    payment_labels = []
    payment_data = []
    payment_colors = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6']
    
    for i, method in enumerate(payment_methods):
        payment_labels.append(method['payment_method'])
        payment_data.append(float(method['total'] or 0))
    
    # Add payment chart to chart_data
    chart_data["payments"] = {
        "labels": payment_labels,
        "datasets": [{
            "label": _("Revenue by Payment Method"),
            "data": payment_data,
            "backgroundColor": payment_colors[:len(payment_labels)],
        }]
    }
    ordered_products = (
        OrderProduct.objects
        .values("product__name")
        .annotate(total_quantity=Sum("quantity"))
        .order_by("-total_quantity")
    )

    inventory = (
        Product.objects
        .values("name", "stock")
        .order_by("-stock")
    )
    context.update({
        "kpi": kpi,
        "charts": chart_data,
        "table_data": table_data,
        "customer_data": customer_data,
        "low_stock_products": low_stock_products,
        "low_stock_variations": low_stock_variations,
        "progress": progress,
        "payment_data": payment_data,
        "total_products": Product.objects.count(),
        "total_customers": Account.objects.filter(is_active=True).count(),
        "pending_orders": Order.objects.filter(status='New').count(),
        "completed_orders": Order.objects.filter(status='Completed').count(),
        "ordered_products": ordered_products,
        "inventory": inventory,
    })
    
    return context