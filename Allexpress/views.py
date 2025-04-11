# from django.shortcuts import render
# from store.models import Product, ReviewRating
# def home(request):
#     products = Product.objects.all().filter(is_available=True).order_by('created_date')    
#     for product in products:
#         reviews = ReviewRating.objects.filter(product_id=product.id, status=True)
#     context = {
#         'products': products,
#         'reviews': reviews,
#     }
#     return render(request, 'home.html', context)





# Allexpress/views.py (assumed)
from django.shortcuts import render
from store.models import Product
from django.db.models import Count, Q
from decimal import Decimal
from orders.models import OrderProduct



def home(request):
    products = Product.objects.filter(is_available=True).order_by('id')

    # Calculate discounted price for each product
    for product in products:
        product.discounted_price = product.price * Decimal('0.5')

    # Debug: Check OrderProduct entries
    order_products = OrderProduct.objects.filter(ordered=True)
    print(f"Home - OrderProduct entries with ordered=True: {order_products.count()}")
    for op in order_products:
        print(f"Home - OrderProduct: Product={op.product.product_name}, Order is_ordered={op.order.is_ordered}, Product is_available={op.product.is_available}, OrderProduct ID={op.id}")

    # Fetch best seller products
    best_sellers = Product.objects.filter(
        is_available=True,
        orderproduct__ordered=True,
        orderproduct__order__is_ordered=True
    ).annotate(
        sales_count=Count('orderproduct')
    ).order_by('-sales_count', '-created_date')[:6]

    # Debug: Check best sellers
    print(f"Home - Best sellers count: {best_sellers.count()}")
    for product in best_sellers:
        print(f"Home - Best seller: {product.product_name}, Sales count: {product.sales_count}")

    # Add discounted price to best sellers
    for product in best_sellers:
        product.discounted_price = product.price * Decimal('0.5')

    context = {
        'products': products,
        'best_sellers': best_sellers,
    }
    return render(request, 'home.html', context)

# from django.shortcuts import render
# from store.models import Product, ReviewRating

# def home(request):
#     products = Product.objects.filter(is_available=True).order_by('created_date')    
#     reviews = []  # Initialize reviews as an empty list
#     for product in products:
#         product_reviews = ReviewRating.objects.filter(product_id=product.id, status=True)
#         reviews.append(product_reviews)  # Collect reviews for each product
        
        
#     for product in products:
#         if product.discount_percentage:  # Check if discount is available
#             # Apply discount if the field exists
#             product.discounted_price = product.price * (1 - product.discount_percentage / 100)
#         else:
#             product.discounted_price = None
#     context = {
#         'products': products,
#         'reviews': reviews,  # Pass the collected reviews
#     }
#     return render(request, 'home.html', context)
