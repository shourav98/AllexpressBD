from carts.views import _cart_id
from django.shortcuts import render, redirect, get_object_or_404
from .models import Product, ReviewRating, ProductGallery
from category.models import Category
from carts.models import CartItem
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db.models import Q
from .forms import ReviewForm
from django.contrib import messages
from orders.models import OrderProduct


from django.db.models import Count


# Create your views here.
from decimal import Decimal

from django.shortcuts import render
from .models import Product
from decimal import Decimal
from django.core.paginator import Paginator

def store(request, category_slug=None):
    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)
        products = Product.objects.filter(category=category, is_available=True)
    else:
        products = Product.objects.filter(is_available=True).order_by('id')

    # Calculate discounted price for each product
    for product in products:
        product.discounted_price = product.price * Decimal('0.5')

    # Debug: Check OrderProduct entries
    order_products = OrderProduct.objects.filter(ordered=True)
    print(f"OrderProduct entries with ordered=True: {order_products.count()}")
    for op in order_products:
        print(f"OrderProduct: Product={op.product.product_name}, Order is_ordered={op.order.is_ordered}, Product is_available={op.product.is_available}, OrderProduct ID={op.id}")

    # Fetch best seller products
    best_sellers = Product.objects.filter(
        is_available=True,
        orderproduct__ordered=True,
        orderproduct__order__is_ordered=True
    ).annotate(
        sales_count=Count('orderproduct')
    ).order_by('-sales_count', '-created_date')[:6]

    # Debug: Check best sellers
    print(f"Best sellers count: {best_sellers.count()}")
    for product in best_sellers:
        print(f"Best seller: {product.product_name}, Sales count: {product.sales_count}")

    # Add discounted price to best sellers
    for product in best_sellers:
        product.discounted_price = product.price * Decimal('0.5')

    # Pagination
    paginator = Paginator(products, 3 if category_slug else 6)
    page = request.GET.get('page')
    paged_products = paginator.get_page(page)

    # Handle search query
    search_products = []
    if 'keyword' in request.GET:
        keyword = request.GET['keyword']
        if keyword:
            search_products = Product.objects.order_by('created_date').filter(
                Q(description__icontains=keyword) | Q(product_name__icontains=keyword)
            )
            for product in search_products:
                product.discounted_price = product.price * Decimal('0.5')

    context = {
        'products': paged_products,
        'product_count': products.count(),
        'category_slug': category_slug,
        'best_sellers': best_sellers,
        'search_products': search_products,
    }
    return render(request, 'store/store.html', context)




# def store(request, category_slug=None):  # Accept category_slug as a parameter
#     if category_slug:
#         # Filter products by category if category_slug is provided
#         category = get_object_or_404(Category, slug=category_slug)  # Get category by slug
#         products = Product.objects.filter(category=category, is_available=True)
#     else:
#         # If no category is provided, show all available products
#         products = Product.objects.filter(is_available=True).order_by('id')

#     # Calculate discounted price for each product
#     for product in products:
#         # Ensure product.price is a Decimal type before doing the calculation
#         product.discounted_price = product.price * Decimal('0.5')  # Use Decimal for multiplication

#     # Pagination
#     paginator = Paginator(products, 3 if category_slug else 6)
#     page = request.GET.get('page')
#     paged_products = paginator.get_page(page)

#     context = {
#         'products': paged_products,
#         'product_count': products.count(),
#         'category_slug': category_slug,  # Pass the category_slug to the template for active category highlighting
#     }
#     return render(request, 'store/store.html', context)





def product_detail(request, category_slug, product_slug):
    discount_percentage = Decimal('50')  # Set discount percentage as Decimal

    try:
        single_product = Product.objects.get(category__slug=category_slug, slug=product_slug)
        in_cart = CartItem.objects.filter(cart__cart_id=_cart_id(request), product=single_product).exists()

        # Calculate the discounted price for the product
        single_product.discounted_price = single_product.price * (1 - discount_percentage / Decimal('100'))

        if category_slug:
            categories = Product.objects.all().filter(category__slug=category_slug)
            product_count = categories.count()

    except Product.DoesNotExist:
        single_product = None
        in_cart = False
        product_count = 0
        categories = None

    # Check if the user has ordered this product
    if request.user.is_authenticated:
        orderproduct = OrderProduct.objects.filter(user=request.user, product_id=single_product.id).exists()
    else:
        orderproduct = None

    # Get the reviews
    reviews = ReviewRating.objects.filter(product_id=single_product.id, status=True)

    # Get the product gallery
    product_gallery = ProductGallery.objects.filter(product_id=single_product.id)

    context = {
        'single_product': single_product,
        'in_cart': in_cart,
        'categories': categories,
        'orderproduct': orderproduct,
        'reviews': reviews,
        'product_gallery': product_gallery,
        'discount_percentage': discount_percentage,  # Pass the discount percentage for display
    }

    return render(request, 'store/product_detail.html', context)





def search(request):
    if 'keyword' in request.GET:
        keyword = request.GET['keyword']
        if keyword:
            products = Product.objects.order_by('created_date').filter(Q(discription__icontains=keyword) | Q(product_name__icontains=keyword))
            product_count = products.count()

    context = {
        'products': products,
        'product_count': product_count,
    }
        
    return render(request,'store/store.html',context)



def submit_review(request, product_id):
    url = request.META.get('HTTP_REFERER')
    if request.method == 'POST':
        try:
            reviews = ReviewRating.objects.get(user__id=request.user.id, product__id=product_id)
            form = ReviewForm(request.POST, instance=reviews)
            form.save()
            messages.success(request, 'Thank You! Your review has been updated')
            return redirect(url)
        except ReviewRating.DoesNotExist:
            form = ReviewForm(request.POST)
            if form.is_valid():
                data = ReviewRating()
                data.subject = form.cleaned_data['subject']
                data.rating = form.cleaned_data['rating']
                data.review = form.cleaned_data['review']
                data.ip = request.META.get("REMOTE_ADDR")
                data.product_id = product_id
                data.user_id = request.user.id
                data.save()
                messages.success(request, 'Thank You! Your review has been submitted')
                return redirect(url)
