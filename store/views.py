# views.py
from django.shortcuts import render, redirect, get_object_or_404
from .models import Product, ReviewRating, ProductGallery
from category.models import Category
from carts.models import CartItem
from carts.views import _cart_id
from django.core.paginator import Paginator
from django.db.models import Q, Count
from .forms import ReviewForm
from django.contrib import messages
from orders.models import OrderProduct
from decimal import Decimal

def store(request, category_slug=None):
    """Store page with products, categories, subcategories, and filters."""
    category = None
    products = Product.objects.filter(is_available=True)
    categories = None

    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)
        if category.is_parent():
            # Parent category: show subcategories and their products
            categories = category.get_subcategories()
            products = Product.objects.filter(category__in=categories, is_available=True)
        else:
            # Subcategory: show products in this subcategory
            products = products.filter(category=category)

    # Apply filters
    size = request.GET.get('size')
    price_min = request.GET.get('price_min', 0)
    price_max = request.GET.get('price_max', 5000)

    if size:
        products = products.filter(variation__variation_category='size', variation__variation_value=size)
    
    try:
        price_min = Decimal(price_min)
        price_max = Decimal(price_max)
        products = products.filter(price__gte=price_min, price__lte=price_max)
    except (ValueError, TypeError):
        pass  # Ignore invalid price inputs

    # Fetch best seller products
    best_sellers = (
        Product.objects.filter(
            is_available=True,
            orderproduct__ordered=True,
            orderproduct__order__is_ordered=True,
        )
        .annotate(sales_count=Count("orderproduct"))
        .order_by("-sales_count", "-created_date")[:6]
    )

    # Pagination
    paginator = Paginator(products, 12)  # Show 12 products per page
    page = request.GET.get('page')
    paged_products = paginator.get_page(page)

    # Search functionality
    keyword = request.GET.get("keyword")
    search_products = []
    if keyword:
        search_products = Product.objects.filter(
            Q(description__icontains=keyword) | Q(product_name__icontains=keyword),
            is_available=True
        ).order_by("created_date")
        paged_products = search_products  # Update for search results

    # Get recently viewed products
    if 'recently_viewed' not in request.session:
        request.session['recently_viewed'] = []
    recent_product_ids = request.session['recently_viewed']
    recent_products = Product.objects.filter(id__in=recent_product_ids, is_available=True)[:8]

    # Get all parent categories for navigation
    parent_categories = Category.objects.filter(parent__isnull=True, is_active=True)

    context = {
        "products": paged_products,
        "product_count": products.count(),
        "category": category,
        "categories": categories,  # Subcategories if parent category
        "parent_categories": parent_categories,
        "best_sellers": best_sellers,
        "search_products": search_products,
        "recent_products": recent_products,
    }
    return render(request, "store/store.html", context)

def product_detail(request, category_slug, product_slug):
    """Product details with reviews, gallery, discount, and cart status."""
    discount_percentage = Decimal("50")

    if 'recently_viewed' not in request.session:
        request.session['recently_viewed'] = []

    try:
        single_product = Product.objects.get(category__slug=category_slug, slug=product_slug)
        in_cart = CartItem.objects.filter(
            cart__cart_id=_cart_id(request), product=single_product
        ).exists()

        # Add to recently viewed products
        recently_viewed = request.session.get('recently_viewed', [])
        if single_product.id not in recently_viewed:
            recently_viewed.insert(0, single_product.id)
            recently_viewed = recently_viewed[:8]
            request.session['recently_viewed'] = recently_viewed
            request.session.modified = True

        # Get related products in the same subcategory
        related_products = Product.objects.filter(
            category=single_product.category, is_available=True
        ).exclude(id=single_product.id)[:6]
    except Product.DoesNotExist:
        single_product = None
        in_cart = False
        related_products = []

    # Check if user purchased this product
    orderproduct = (
        OrderProduct.objects.filter(user=request.user, product_id=single_product.id).exists()
        if request.user.is_authenticated and single_product
        else None
    )

    # Reviews & gallery
    reviews = ReviewRating.objects.filter(product_id=single_product.id, status=True) if single_product else []
    product_gallery = ProductGallery.objects.filter(product_id=single_product.id) if single_product else []

    # Get all parent categories for navigation
    parent_categories = Category.objects.filter(parent__isnull=True, is_active=True)

    context = {
        "single_product": single_product,
        "in_cart": in_cart,
        "related_products": related_products,
        "orderproduct": orderproduct,
        "reviews": reviews,
        "product_gallery": product_gallery,
        "discount_percentage": discount_percentage,
        "parent_categories": parent_categories,
    }
    return render(request, "store/product_detail.html", context)

def search(request):
    """Search products by keyword."""
    products = []
    product_count = 0
    keyword = request.GET.get("keyword")
    if keyword:
        products = Product.objects.filter(
            Q(description__icontains=keyword) | Q(product_name__icontains=keyword),
            is_available=True
        ).order_by("created_date")
        product_count = products.count()

    # Get all parent categories for navigation
    parent_categories = Category.objects.filter(parent__isnull=True, is_active=True)

    context = {
        "products": products,
        "product_count": product_count,
        "parent_categories": parent_categories,
    }
    return render(request, "store/store.html", context)

def submit_review(request, product_id):
    """Submit or update a review for a product."""
    url = request.META.get("HTTP_REFERER")
    if request.method == "POST":
        try:
            # Update review if exists
            reviews = ReviewRating.objects.get(
                user_id=request.user.id, product_id=product_id
            )
            form = ReviewForm(request.POST, instance=reviews)
            if form.is_valid():
                form.save()
                messages.success(request, "Thank you! Your review has been updated.")
        except ReviewRating.DoesNotExist:
            # Create new review
            form = ReviewForm(request.POST)
            if form.is_valid():
                data = ReviewRating()
                data.subject = form.cleaned_data["subject"]
                data.rating = form.cleaned_data["rating"]
                data.review = form.cleaned_data["review"]
                data.ip = request.META.get("REMOTE_ADDR")
                data.product_id = product_id
                data.user_id = request.user.id
                data.save()
                messages.success(request, "Thank you! Your review has been submitted.")
        return redirect(url)


# from carts.views import _cart_id
# from django.shortcuts import render, redirect, get_object_or_404
# from .models import Product, ReviewRating, ProductGallery
# from category.models import Category
# from carts.models import CartItem
# from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
# from django.db.models import Q, Count
# from .forms import ReviewForm
# from django.contrib import messages
# from orders.models import OrderProduct
# from decimal import Decimal


# def store(request, category_slug=None):
#     """Store page with products, categories, best sellers, and optional search."""
#     category = None
#     products = Product.objects.filter(is_available=True)

#     if category_slug:
#         category = get_object_or_404(Category, slug=category_slug)
#         products = products.filter(category=category)

#     # Fetch best seller products
#     best_sellers = (
#         Product.objects.filter(
#             is_available=True,
#             orderproduct__ordered=True,
#             orderproduct__order__is_ordered=True,
#         )
#         .annotate(sales_count=Count("orderproduct"))
#         .order_by("-sales_count", "-created_date")[:6]
#     )

#     # Get all products for show more functionality
#     all_products = products
#     total_products = products.count()

#     # Search functionality
#     search_products = []
#     keyword = request.GET.get("keyword")
#     if keyword:
#         search_products = Product.objects.filter(
#             Q(description__icontains=keyword) | Q(product_name__icontains=keyword)
#         ).order_by("created_date")

#     # Get recently viewed products from session
#     if 'recently_viewed' not in request.session:
#         request.session['recently_viewed'] = []
    
#     recent_product_ids = request.session['recently_viewed']
#     recent_products = Product.objects.filter(id__in=recent_product_ids)[:8]

#     context = {
#         "products": all_products,
#         "product_count": total_products,
#         "category_slug": category_slug,
#         "best_sellers": best_sellers,
#         "search_products": search_products,
#         "recent_products": recent_products,
#     }
#     return render(request, "store/store.html", context)


# def product_detail(request, category_slug, product_slug):
#     """Product details with reviews, gallery, discount, and cart status."""
#     discount_percentage = Decimal("50")
    
#     # Initialize recently viewed in session if it doesn't exist
#     if 'recently_viewed' not in request.session:
#         request.session['recently_viewed'] = []

#     try:
#         single_product = Product.objects.get(
#             category__slug=category_slug, slug=product_slug
#         )
#         in_cart = CartItem.objects.filter(
#             cart__cart_id=_cart_id(request), product=single_product
#         ).exists()

#         # Add to recently viewed products
#         recently_viewed = request.session.get('recently_viewed', [])
#         if single_product.id not in recently_viewed:
#             recently_viewed.insert(0, single_product.id)
#             recently_viewed = recently_viewed[:8]  # Keep only last 8 items
#             request.session['recently_viewed'] = recently_viewed
#             request.session.modified = True

#         categories = Product.objects.filter(category__slug=category_slug)
#         product_count = categories.count()
#     except Product.DoesNotExist:
#         single_product = None
#         in_cart = False
#         product_count = 0
#         categories = None

#     # Check if user purchased this product
#     orderproduct = (
#         OrderProduct.objects.filter(user=request.user, product_id=single_product.id)
#         .exists()
#         if request.user.is_authenticated and single_product
#         else None
#     )

#     # Reviews & gallery
#     reviews = ReviewRating.objects.filter(product_id=single_product.id, status=True)
#     product_gallery = ProductGallery.objects.filter(product_id=single_product.id)

#     context = {
#         "single_product": single_product,
#         "in_cart": in_cart,
#         "categories": categories,
#         "product_count": product_count,
#         "orderproduct": orderproduct,
#         "reviews": reviews,
#         "product_gallery": product_gallery,
#         "discount_percentage": discount_percentage,
#     }
#     return render(request, "store/product_detail.html", context)


# def search(request):
#     """Search products by keyword."""
#     products = []
#     product_count = 0

#     keyword = request.GET.get("keyword")
#     if keyword:
#         products = Product.objects.filter(
#             Q(description__icontains=keyword) | Q(product_name__icontains=keyword)
#         ).order_by("created_date")
#         product_count = products.count()

#     context = {"products": products, "product_count": product_count}
#     return render(request, "store/store.html", context)


# def submit_review(request, product_id):
#     """Submit or update a review for a product."""
#     url = request.META.get("HTTP_REFERER")
#     if request.method == "POST":
#         try:
#             # Update review if exists
#             reviews = ReviewRating.objects.get(
#                 user_id=request.user.id, product_id=product_id
#             )
#             form = ReviewForm(request.POST, instance=reviews)
#             if form.is_valid():
#                 form.save()
#                 messages.success(request, "Thank you! Your review has been updated.")
#         except ReviewRating.DoesNotExist:
#             # Create new review
#             form = ReviewForm(request.POST)
#             if form.is_valid():
#                 data = ReviewRating()
#                 data.subject = form.cleaned_data["subject"]
#                 data.rating = form.cleaned_data["rating"]
#                 data.review = form.cleaned_data["review"]
#                 data.ip = request.META.get("REMOTE_ADDR")
#                 data.product_id = product_id
#                 data.user_id = request.user.id
#                 data.save()
#                 messages.success(request, "Thank you! Your review has been submitted.")
#         return redirect(url)







# from carts.views import _cart_id
# from django.shortcuts import render, redirect, get_object_or_404
# from .models import Product, ReviewRating, ProductGallery
# from category.models import Category
# from carts.models import CartItem
# from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
# from django.db.models import Q
# from .forms import ReviewForm
# from django.contrib import messages
# from orders.models import OrderProduct


# from django.db.models import Count


# # Create your views here.
# from decimal import Decimal

# from django.shortcuts import render
# from .models import Product
# from decimal import Decimal
# from django.core.paginator import Paginator

# def store(request, category_slug=None):
#     if category_slug:
#         category = get_object_or_404(Category, slug=category_slug)
#         products = Product.objects.filter(category=category, is_available=True)
#     else:
#         products = Product.objects.filter(is_available=True).order_by('id')

#     # Calculate discounted price for each product
#     for product in products:
#         product.discounted_price = product.price * Decimal('0.5')

#     # Debug: Check OrderProduct entries
#     order_products = OrderProduct.objects.filter(ordered=True)
#     print(f"OrderProduct entries with ordered=True: {order_products.count()}")
#     for op in order_products:
#         print(f"OrderProduct: Product={op.product.product_name}, Order is_ordered={op.order.is_ordered}, Product is_available={op.product.is_available}, OrderProduct ID={op.id}")

#     # Fetch best seller products
#     best_sellers = Product.objects.filter(
#         is_available=True,
#         orderproduct__ordered=True,
#         orderproduct__order__is_ordered=True
#     ).annotate(
#         sales_count=Count('orderproduct')
#     ).order_by('-sales_count', '-created_date')[:6]

#     # Debug: Check best sellers
#     print(f"Best sellers count: {best_sellers.count()}")
#     for product in best_sellers:
#         print(f"Best seller: {product.product_name}, Sales count: {product.sales_count}")

#     # Add discounted price to best sellers
#     for product in best_sellers:
#         product.discounted_price = product.price * Decimal('0.5')

#     # Pagination
#     paginator = Paginator(products, 3 if category_slug else 6)
#     page = request.GET.get('page')
#     paged_products = paginator.get_page(page)

#     # Handle search query
#     search_products = []
#     if 'keyword' in request.GET:
#         keyword = request.GET['keyword']
#         if keyword:
#             search_products = Product.objects.order_by('created_date').filter(
#                 Q(description__icontains=keyword) | Q(product_name__icontains=keyword)
#             )
#             for product in search_products:
#                 product.discounted_price = product.price * Decimal('0.5')

#     context = {
#         'products': paged_products,
#         'product_count': products.count(),
#         'category_slug': category_slug,
#         'best_sellers': best_sellers,
#         'search_products': search_products,
#     }
#     return render(request, 'store/store.html', context)






# def product_detail(request, category_slug, product_slug):
#     discount_percentage = Decimal('50')  # Set discount percentage as Decimal

#     try:
#         single_product = Product.objects.get(category__slug=category_slug, slug=product_slug)
#         in_cart = CartItem.objects.filter(cart__cart_id=_cart_id(request), product=single_product).exists()

#         # Calculate the discounted price for the product
#         single_product.discounted_price = single_product.price * (1 - discount_percentage / Decimal('100'))

#         if category_slug:
#             categories = Product.objects.all().filter(category__slug=category_slug)
#             product_count = categories.count()

#     except Product.DoesNotExist:
#         single_product = None
#         in_cart = False
#         product_count = 0
#         categories = None

#     # Check if the user has ordered this product
#     if request.user.is_authenticated:
#         orderproduct = OrderProduct.objects.filter(user=request.user, product_id=single_product.id).exists()
#     else:
#         orderproduct = None

#     # Get the reviews
#     reviews = ReviewRating.objects.filter(product_id=single_product.id, status=True)

#     # Get the product gallery
#     product_gallery = ProductGallery.objects.filter(product_id=single_product.id)

#     context = {
#         'single_product': single_product,
#         'in_cart': in_cart,
#         'categories': categories,
#         'orderproduct': orderproduct,
#         'reviews': reviews,
#         'product_gallery': product_gallery,
#         'discount_percentage': discount_percentage,  # Pass the discount percentage for display
#     }

#     return render(request, 'store/product_detail.html', context)





# def search(request):
#     if 'keyword' in request.GET:
#         keyword = request.GET['keyword']
#         if keyword:
#             products = Product.objects.order_by('created_date').filter(Q(discription__icontains=keyword) | Q(product_name__icontains=keyword))
#             product_count = products.count()

#     context = {
#         'products': products,
#         'product_count': product_count,
#     }
        
#     return render(request,'store/store.html',context)



# def submit_review(request, product_id):
#     url = request.META.get('HTTP_REFERER')
#     if request.method == 'POST':
#         try:
#             reviews = ReviewRating.objects.get(user__id=request.user.id, product__id=product_id)
#             form = ReviewForm(request.POST, instance=reviews)
#             form.save()
#             messages.success(request, 'Thank You! Your review has been updated')
#             return redirect(url)
#         except ReviewRating.DoesNotExist:
#             form = ReviewForm(request.POST)
#             if form.is_valid():
#                 data = ReviewRating()
#                 data.subject = form.cleaned_data['subject']
#                 data.rating = form.cleaned_data['rating']
#                 data.review = form.cleaned_data['review']
#                 data.ip = request.META.get("REMOTE_ADDR")
#                 data.product_id = product_id
#                 data.user_id = request.user.id
#                 data.save()
#                 messages.success(request, 'Thank You! Your review has been submitted')
#                 return redirect(url)
