from django.shortcuts import render, get_object_or_404
from store.models import Product
from django.db.models import Count, Q, F, ExpressionWrapper, DecimalField, Value, Case, When
from decimal import Decimal
from orders.models import OrderProduct
from django.core.paginator import Paginator
from category.models import Category, Brand


def home(request):
    """Home page with search results, categories, and popular/best seller products."""
    keyword = request.GET.get("keyword")
    search_products = []
    
    # Base queryset for active products with annotated discounted price
    base_products = Product.objects.annotate(
        discounted_price_annotated=Case(
            When(
                discount_percentage__gt=0,
                then=ExpressionWrapper(
                    F('price') - (F('price') * F('discount_percentage') / Value(100)),
                    output_field=DecimalField(max_digits=10, decimal_places=2)
                )
            ),
            default=F('price')
        )
    ).filter(is_available=True)
    
    # Search functionality
    if keyword:
        search_products = base_products.filter(
            Q(description__icontains=keyword) | Q(name__icontains=keyword)
        ).order_by("created_date")

    # Price range filter
    min_price = request.GET.get("min_price")
    max_price = request.GET.get("max_price")
    
    products = base_products
    if min_price and max_price:
        try:
            min_price = Decimal(min_price)
            max_price = Decimal(max_price)
            products = products.filter(discounted_price_annotated__gte=min_price,
                                       discounted_price_annotated__lte=max_price)
        except (ValueError, TypeError):
            pass
    
    products = products.order_by('-created_date')
    
    # Paginate products
    paginator = Paginator(products, 12)
    page = request.GET.get('page')
    paged_products = paginator.get_page(page)

    # Best sellers
    best_sellers = (
        base_products.filter(
            orderproduct__ordered=True,
            orderproduct__order__is_ordered=True,
        )
        .annotate(sales_count=Count("orderproduct"))
        .order_by("-sales_count", "-created_date")[:8]
    )

    # Apply price filter to best sellers
    if min_price and max_price:
        best_sellers = best_sellers.filter(discounted_price_annotated__gte=min_price,
                                           discounted_price_annotated__lte=max_price)

    parent_categories = Category.objects.filter(parent__isnull=True, is_active=True)
    brands = Brand.objects.filter(is_active=True)

    context = {
        "products": paged_products,
        "search_products": search_products,
        "best_sellers": best_sellers,
        "parent_categories": parent_categories,
        "brands": brands,
        "min_price": min_price,
        "max_price": max_price,
    }
    return render(request, "home.html", context)


def products_by_brand(request, brand_slug):
    """Display products filtered by brand."""
    brand = get_object_or_404(Brand, slug=brand_slug)

    base_products = Product.objects.annotate(
        discounted_price_annotated=Case(
            When(
                discount_percentage__gt=0,
                then=ExpressionWrapper(
                    F('price') - (F('price') * F('discount_percentage') / Value(100)),
                    output_field=DecimalField(max_digits=10, decimal_places=2)
                )
            ),
            default=F('price')
        )
    ).filter(is_available=True, brand=brand)

    # Apply filters
    size = request.GET.get('size')
    price_min = request.GET.get('price_min', 0)
    price_max = request.GET.get('price_max', 5000)

    if size:
        base_products = base_products.filter(variation__variation_category='size', variation__variation_value=size)
    
    try:
        price_min = Decimal(price_min)
        price_max = Decimal(price_max)
        base_products = base_products.filter(discounted_price_annotated__gte=price_min,
                                             discounted_price_annotated__lte=price_max)
    except (ValueError, TypeError):
        pass

    # Pagination
    paginator = Paginator(base_products, 12)
    page = request.GET.get('page')
    paged_products = paginator.get_page(page)

    # Search functionality
    keyword = request.GET.get("keyword")
    search_products = []
    if keyword:
        search_products = base_products.filter(
            Q(description__icontains=keyword) | Q(name__icontains=keyword)
        ).order_by("created_date")
        paged_products = search_products

    # Recently viewed
    if 'recently_viewed' not in request.session:
        request.session['recently_viewed'] = []
    recent_product_ids = request.session['recently_viewed']
    recent_products = Product.objects.filter(id__in=recent_product_ids, is_available=True)[:8]

    parent_categories = Category.objects.filter(parent__isnull=True, is_active=True)
    brands = Brand.objects.filter(is_active=True)

    context = {
        "products": paged_products,
        "product_count": base_products.count(),
        "brand": brand,
        "parent_categories": parent_categories,
        "brands": brands,
        "search_products": search_products,
        "recent_products": recent_products,
    }
    return render(request, "store/store.html", context)






def returns(request):
    return render(request, 'footer/returns.html')

def shipping(request):
    return render(request, 'footer/shipping.html')

def offers(request):
    return render(request, 'footer/offers.html')

def size_charts(request):
    return render(request, 'footer/size_charts.html')

def gift_vouchers(request):
    return render(request, 'footer/gift_vouchers.html')

# def home(request):
#     return render(request, 'home.html')

def about(request):
    return render(request, 'footer/about.html')

def privacy(request):
    return render(request, 'footer/privacy.html')

def terms(request):
    return render(request, 'footer/terms.html')

def warranty(request):
    return render(request, 'footer/warranty.html')