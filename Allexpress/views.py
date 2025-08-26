from django.shortcuts import render
from store.models import Product
from django.db.models import Count, Q
from decimal import Decimal
from orders.models import OrderProduct
from django.core.paginator import Paginator
from category.models import Category



def home(request):
    """Home page with search results, categories, and popular/best seller products."""
    # Search functionality
    keyword = request.GET.get("keyword")
    search_products = []
    if keyword:
        search_products = Product.objects.filter(
            Q(description__icontains=keyword) | Q(product_name__icontains=keyword),
            is_available=True
        ).order_by("created_date")

    # Get all active products
    products = Product.objects.filter(is_available=True).order_by('-created_date')

    # Paginate products
    paginator = Paginator(products, 12)  # Show 12 products per page
    page = request.GET.get('page')
    paged_products = paginator.get_page(page)

    # Get best seller products (updated to 8)
    best_sellers = (
        Product.objects.filter(
            is_available=True,
            orderproduct__ordered=True,
            orderproduct__order__is_ordered=True,
        )
        .annotate(sales_count=Count("orderproduct"))
        .order_by("-sales_count", "-created_date")[:8]  # Changed from 6 to 8
    )

    # Get all parent categories
    parent_categories = Category.objects.filter(parent__isnull=True, is_active=True)

    context = {
        "products": paged_products,
        "search_products": search_products,
        "best_sellers": best_sellers,
        "parent_categories": parent_categories,
    }
    return render(request, "home.html", context)