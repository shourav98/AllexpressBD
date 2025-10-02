from django.shortcuts import render, redirect, get_object_or_404
from .models import Product, ReviewRating, ProductGallery
from category.models import Category, Brand
from carts.models import CartItem
from carts.views import _cart_id
from django.core.paginator import Paginator
from django.db.models import Q, Count, F, ExpressionWrapper, DecimalField, Case, When, IntegerField, Value, Sum
from django.db.models.functions import Coalesce
from .forms import ReviewForm
from django.contrib import messages
from orders.models import OrderProduct
from decimal import Decimal



from django.http import JsonResponse
from .models import Variation, VariationCombination
from .forms import ProductForm, VariationForm
from carts.models import Cart

def store(request, category_slug=None, brand_slug=None):
    """Store page with products, categories, subcategories, brands, filters, and search."""
    category = None
    brand = None
    # Include products that have stock either at product level or in combinations
    products = Product.objects.filter(is_available=True).annotate(
        total_stock=Case(
            When(variation_combinations__isnull=False, then=Sum('variation_combinations__stock')),
            default=F('stock'),
            output_field=IntegerField()
        )
    ).filter(
        Q(stock__gt=0) | Q(total_stock__gt=0)
    ).distinct()
    categories = None

    # Filter by category
    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)
        if category.parent is None:  # Parent category
            # Include all child categories
            child_categories = Category.objects.filter(parent=category)
            products = products.filter(category__in=[category, *child_categories])
        else:
            # Child category
            products = products.filter(category=category)

    # Filter by brand
    if brand_slug:
        brand = get_object_or_404(Brand, slug=brand_slug)
        products = products.filter(brand=brand)

    # Apply size filter
    size = request.GET.get('size')
    if size:
        products = products.filter(
            variation_combinations__size_variation__variation_value=size
        )

    # Apply price filter
    price_min = request.GET.get('price_min', 0)
    price_max = request.GET.get('price_max', 5000)

    # Annotate discounted price
    products = products.annotate(
        discounted_price_annotated=Coalesce(
            ExpressionWrapper(
                F('price') - (F('price') * F('discount_percentage') / 100),
                output_field=DecimalField(max_digits=10, decimal_places=2)
            ),
            F('price'),
            output_field=DecimalField(max_digits=10, decimal_places=2)
        )
    )

    try:
        price_min = Decimal(price_min)
        price_max = Decimal(price_max)
        products = products.filter(
            discounted_price_annotated__gte=price_min, discounted_price_annotated__lte=price_max
        )
    except (ValueError, TypeError):
        pass

    # Fetch best seller products
    best_sellers = (
        Product.objects.filter(
            is_available=True,
            orderproduct__ordered=True,
            orderproduct__order__is_ordered=True,
        )
        .annotate(sales_count=Count("orderproduct"))
        .annotate(
            discounted_price_annotated=Coalesce(
                ExpressionWrapper(
                    F('price') - (F('price') * F('discount_percentage') / 100),
                    output_field=DecimalField(max_digits=10, decimal_places=2)
                ),
                F('price'),
                output_field=DecimalField(max_digits=10, decimal_places=2)
            )
        )
        .order_by("-sales_count", "-created_date")[:6]
    )

    # Search functionality
    keyword = request.GET.get("keyword")
    if keyword:
        products = products.filter(
            Q(description__icontains=keyword) | Q(name__icontains=keyword)
        ).order_by("created_date")

    # Pagination
    paginator = Paginator(products, 12)
    page = request.GET.get('page')
    paged_products = paginator.get_page(page)

    # Recently viewed products
    recent_product_ids = request.session.get('recently_viewed', [])
    recent_products = Product.objects.filter(id__in=recent_product_ids, is_available=True).annotate(
        discounted_price_annotated=Coalesce(
            ExpressionWrapper(
                F('price') - (F('price') * F('discount_percentage') / 100),
                output_field=DecimalField(max_digits=10, decimal_places=2)
            ),
            F('price'),
            output_field=DecimalField(max_digits=10, decimal_places=2)
        )
    )[:8]

    # Parent categories & brands
    parent_categories = Category.objects.filter(parent__isnull=True, is_active=True)
    brands = Brand.objects.filter(is_active=True)

    context = {
        "products": paged_products,
        "product_count": products.count(),
        "category": category,
        "categories": categories,
        "parent_categories": parent_categories,
        "brands": brands,
        "brand": brand,
        "best_sellers": best_sellers,
        "recent_products": recent_products,
    }
    return render(request, "store/store.html", context)






# def product_detail(request, category_slug, product_slug):
#     """Product details with reviews, gallery, discount, and cart status."""
#     discount_percentage = Decimal("50")

#     if 'recently_viewed' not in request.session:
#         request.session['recently_viewed'] = []

#     try:
#         single_product = Product.objects.get(category__slug=category_slug, slug=product_slug)
#         in_cart = CartItem.objects.filter(
#             cart__cart_id=_cart_id(request), product=single_product
#         ).exists()

#         recently_viewed = request.session.get('recently_viewed', [])
#         if single_product.id not in recently_viewed:
#             recently_viewed.insert(0, single_product.id)
#             recently_viewed = recently_viewed[:8]
#             request.session['recently_viewed'] = recently_viewed
#             request.session.modified = True

#         related_products = Product.objects.filter(
#             category=single_product.category, is_available=True
#         ).exclude(id=single_product.id)[:6]
#     except Product.DoesNotExist:
#         single_product = None
#         in_cart = False
#         related_products = []

#     orderproduct = (
#         OrderProduct.objects.filter(user=request.user, product_id=single_product.id).exists()
#         if request.user.is_authenticated and single_product
#         else None
#     )

#     reviews = ReviewRating.objects.filter(product_id=single_product.id, status=True) if single_product else []
#     product_gallery = ProductGallery.objects.filter(product_id=single_product.id) if single_product else []
#     parent_categories = Category.objects.filter(parent__isnull=True, is_active=True)
#     brands = Brand.objects.filter(is_active=True)

#     context = {
#         "single_product": single_product,
#         "in_cart": in_cart,
#         "related_products": related_products,
#         "orderproduct": orderproduct,
#         "reviews": reviews,
#         "product_gallery": product_gallery,
#         "discount_percentage": discount_percentage,
#         "parent_categories": parent_categories,
#         "brands": brands,
#     }
#     return render(request, "store/product_detail.html", context)

def search(request):
    """Search products by keyword."""
    products = []
    product_count = 0
    keyword = request.GET.get("keyword")
    if keyword:
        products = Product.objects.filter(
            Q(description__icontains=keyword) | Q(name__icontains=keyword),
            is_available=True
        ).annotate(
            discounted_price_annotated=Coalesce(
                ExpressionWrapper(
                    F('price') - (F('price') * F('discount_percentage') / 100),
                    output_field=DecimalField(max_digits=10, decimal_places=2)
                ),
                F('price'),
                output_field=DecimalField(max_digits=10, decimal_places=2)
            )
        ).order_by("created_date")
        product_count = products.count()

    parent_categories = Category.objects.filter(parent__isnull=True, is_active=True)
    brands = Brand.objects.filter(is_active=True)

    context = {
        "products": products,
        "product_count": product_count,
        "parent_categories": parent_categories,
        "brands": brands,
    }
    return render(request, "store/store.html", context)

def submit_review(request, product_id):
    """Submit or update a review for a product."""
    url = request.META.get("HTTP_REFERER")
    if request.method == "POST":
        try:
            reviews = ReviewRating.objects.get(
                user_id=request.user.id, product_id=product_id
            )
            form = ReviewForm(request.POST, instance=reviews)
            if form.is_valid():
                form.save()
                messages.success(request, "Thank you! Your review has been updated.")
        except ReviewRating.DoesNotExist:
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
    



def products_by_brand(request, brand_slug):
    """Display products filtered by brand."""
    brand = get_object_or_404(Brand, slug=brand_slug)
    products = Product.objects.filter(brand=brand, is_available=True).annotate(
        total_stock=Case(
            When(variation_combinations__isnull=False, then=Sum('variation_combinations__stock')),
            default=F('stock'),
            output_field=IntegerField()
        )
    ).filter(
        Q(stock__gt=0) | Q(total_stock__gt=0)
    ).distinct()

    # Apply filters
    size = request.GET.get('size')
    price_min = request.GET.get('price_min', 0)
    price_max = request.GET.get('price_max', 5000)

    if size:
        products = products.filter(variation_combinations__size_variation__variation_value=size)
    
    try:
        price_min = Decimal(price_min)
        price_max = Decimal(price_max)
        products = products.filter(price__gte=price_min, price__lte=price_max)
    except (ValueError, TypeError):
        pass

    # Annotate discounted price
    products = products.annotate(
        discounted_price_annotated=Coalesce(
            ExpressionWrapper(
                F('price') - (F('price') * F('discount_percentage') / 100),
                output_field=DecimalField(max_digits=10, decimal_places=2)
            ),
            F('price'),
            output_field=DecimalField(max_digits=10, decimal_places=2)
        )
    )

    # Pagination
    paginator = Paginator(products, 12)
    page = request.GET.get('page')
    paged_products = paginator.get_page(page)

    # Search functionality
    keyword = request.GET.get("keyword")
    search_products = []
    if keyword:
        search_products = Product.objects.filter(
            Q(description__icontains=keyword) | Q(name__icontains=keyword),
            is_available=True, brand=brand
        ).annotate(
            discounted_price_annotated=Coalesce(
                ExpressionWrapper(
                    F('price') - (F('price') * F('discount_percentage') / 100),
                    output_field=DecimalField(max_digits=10, decimal_places=2)
                ),
                F('price'),
                output_field=DecimalField(max_digits=10, decimal_places=2)
            )
        ).order_by("created_date")
        paged_products = search_products

    # Get recently viewed products
    if 'recently_viewed' not in request.session:
        request.session['recently_viewed'] = []
    recent_product_ids = request.session['recently_viewed']
    recent_products = Product.objects.filter(id__in=recent_product_ids, is_available=True).annotate(
        discounted_price_annotated=Coalesce(
            ExpressionWrapper(
                F('price') - (F('price') * F('discount_percentage') / 100),
                output_field=DecimalField(max_digits=10, decimal_places=2)
            ),
            F('price'),
            output_field=DecimalField(max_digits=10, decimal_places=2)
        )
    )[:8]

    parent_categories = Category.objects.filter(parent__isnull=True, is_active=True)
    brands = Brand.objects.filter(is_active=True)  # For navigation

    context = {
        "products": paged_products,
        "product_count": products.count(),
        "brand": brand,
        "parent_categories": parent_categories,
        "brands": brands,
        "search_products": search_products,
        "recent_products": recent_products,
    }
    return render(request, "store/store.html", context)



def product_detail(request, category_slug=None, product_slug=None, brand_slug=None):
    """Product details with reviews, gallery, discount, and cart status."""

    if "recently_viewed" not in request.session:
        request.session["recently_viewed"] = []

    try:
        if category_slug:
            single_product = get_object_or_404(
                Product.objects.annotate(
                    discounted_price_annotated=Coalesce(
                        ExpressionWrapper(
                            F('price') - (F('price') * F('discount_percentage') / 100),
                            output_field=DecimalField(max_digits=10, decimal_places=2)
                        ),
                        F('price'),
                        output_field=DecimalField(max_digits=10, decimal_places=2)
                    )
                ),
                category__slug=category_slug, slug=product_slug
            )
        elif brand_slug:
            single_product = get_object_or_404(
                Product.objects.annotate(
                    discounted_price_annotated=Coalesce(
                        ExpressionWrapper(
                            F('price') - (F('price') * F('discount_percentage') / 100),
                            output_field=DecimalField(max_digits=10, decimal_places=2)
                        ),
                        F('price'),
                        output_field=DecimalField(max_digits=10, decimal_places=2)
                    )
                ),
                brand__slug=brand_slug, slug=product_slug
            )
        else:
            raise Product.DoesNotExist

        # Always set cart_quantity to 1 for the quantity selector
        cart_quantity = 1

        # Check if product is in cart for display purposes
        if not single_product.variation_combinations.exists():
            try:
                if request.user.is_authenticated:
                    in_cart = CartItem.objects.filter(user=request.user, product=single_product, variation_combination__isnull=True, is_active=True).exists()
                else:
                    cart = Cart.objects.get(cart_id=_cart_id(request))
                    in_cart = CartItem.objects.filter(cart=cart, product=single_product, variation_combination__isnull=True, is_active=True).exists()
            except Cart.DoesNotExist:
                in_cart = False
        else:
            # For products with variations, check if any cart item exists
            try:
                if request.user.is_authenticated:
                    in_cart = CartItem.objects.filter(user=request.user, product=single_product, is_active=True).exists()
                else:
                    cart = Cart.objects.get(cart_id=_cart_id(request))
                    in_cart = CartItem.objects.filter(cart=cart, product=single_product, is_active=True).exists()
            except Cart.DoesNotExist:
                in_cart = False

        # Track recently viewed
        recently_viewed = request.session.get("recently_viewed", [])
        if single_product.id not in recently_viewed:
            recently_viewed.insert(0, single_product.id)
            request.session["recently_viewed"] = recently_viewed[:8]
            request.session.modified = True

        # Related products (excluding current one)
        related_products = Product.objects.filter(is_available=True).exclude(id=single_product.id).annotate(
            discounted_price_annotated=Coalesce(
                ExpressionWrapper(
                    F('price') - (F('price') * F('discount_percentage') / 100),
                    output_field=DecimalField(max_digits=10, decimal_places=2)
                ),
                F('price'),
                output_field=DecimalField(max_digits=10, decimal_places=2)
            )
        )[:6]

    except Product.DoesNotExist:
        single_product, in_cart, related_products = None, False, []

    # Check if user already ordered the product
    orderproduct = (
        OrderProduct.objects.filter(user=request.user, product_id=single_product.id).exists()
        if request.user.is_authenticated and single_product
        else None
    )

    # Reviews and gallery
    reviews = ReviewRating.objects.filter(product_id=single_product.id, status=True) if single_product else []
    product_gallery = ProductGallery.objects.filter(product_id=single_product.id) if single_product else []

    parent_categories = Category.objects.filter(parent__isnull=True, is_active=True)
    brands = Brand.objects.filter(is_active=True)

    context = {
        "single_product": single_product,
        "in_cart": in_cart,
        "cart_quantity": cart_quantity,
        "related_products": related_products,
        "orderproduct": orderproduct,
        "reviews": reviews,
        "product_gallery": product_gallery,
        "parent_categories": parent_categories,
        "brands": brands,
    }
    return render(request, "store/product_detail.html", context)





def product_create(request):
    if request.method == "POST":
        form = ProductForm(request.POST)
        if form.is_valid():
            product = form.save()
            return redirect("product_edit", pk=product.pk)
    else:
        form = ProductForm()
    return render(request, "store/product_form.html", {"form": form})


def add_variation_ajax(request, product_id):
    """AJAX endpoint to add variation"""
    if request.method == "POST":
        product = get_object_or_404(Product, pk=product_id)
        form = VariationForm(request.POST)
        if form.is_valid():
            variation = form.save(commit=False)
            variation.product = product
            variation.save()
            return JsonResponse({
                "success": True,
                "id": variation.id,
                "category": variation.variation_category,
                "value": variation.variation_value,
            })
        return JsonResponse({"success": False, "errors": form.errors})
    return JsonResponse({"success": False})


def get_cart_quantity_ajax(request, product_id):
    """AJAX endpoint to get cart quantity for selected variations - always returns 1"""
    if request.method == "GET":
        # Always return 1 for the quantity selector
        return JsonResponse({"quantity": 1})
    return JsonResponse({"error": "Invalid request"}, status=400)
