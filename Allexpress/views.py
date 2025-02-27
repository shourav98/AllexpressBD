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


from django.shortcuts import render
from store.models import Product, ReviewRating

def home(request):
    products = Product.objects.filter(is_available=True).order_by('created_date')    
    reviews = []  # Initialize reviews as an empty list
    for product in products:
        product_reviews = ReviewRating.objects.filter(product_id=product.id, status=True)
        reviews.append(product_reviews)  # Collect reviews for each product
        
        
    for product in products:
        if product.discount_percentage:  # Check if discount is available
            # Apply discount if the field exists
            product.discounted_price = product.price * (1 - product.discount_percentage / 100)
        else:
            product.discounted_price = None
    context = {
        'products': products,
        'reviews': reviews,  # Pass the collected reviews
    }
    return render(request, 'home.html', context)
