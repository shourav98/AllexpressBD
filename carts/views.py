from django.shortcuts import render, redirect, get_object_or_404
from store.models import Product, Variation, VariationCombination
from .models import Cart, CartItem
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse, JsonResponse

from django.contrib.auth.decorators import login_required
# Create your views here.

def _cart_id(request):
    cart = request.session.session_key
    if not cart:
        cart = request.session.create()
    return cart

def get_cart_count(request):
    """Helper function to get total cart items count"""
    try:
        if request.user.is_authenticated:
            cart_items = CartItem.objects.filter(user=request.user, is_active=True)
        else:
            cart = Cart.objects.get(cart_id=_cart_id(request))
            cart_items = CartItem.objects.filter(cart=cart, is_active=True)
        return sum(item.quantity for item in cart_items)
    except:
        return 0

def cart_count_ajax(request):
    """AJAX endpoint to get cart count"""
    count = get_cart_count(request)
    return JsonResponse({'count': count})

def add_cart(request, product_id):
    current_user = request.user
    product = Product.objects.get(id=product_id)

    variation_combination = None
    quantity = 1

    if request.method == 'POST':
        size_value = request.POST.get('radio_size')
        color_value = request.POST.get('radio_color')
        quantity = int(request.POST.get('quantity', 1))

        # Debug logging
        print(f"DEBUG: Adding to cart - Product: {product.name}, Size: {size_value}, Color: {color_value}, Quantity: {quantity}")

        # Find variation combination by matching variation values
        variation_combination = None
        if size_value or color_value:
            filters = {'product': product}
            if size_value:
                filters['size_variation__variation_value__iexact'] = size_value
            if color_value:
                filters['color_variation__variation_value__iexact'] = color_value
            variation_combination = VariationCombination.objects.filter(**filters).first()
            print(f"DEBUG: Variation combination found: {variation_combination}")
            if variation_combination:
                print(f"DEBUG: VC details - Size: {variation_combination.size_variation.variation_value if variation_combination.size_variation else None}, Color: {variation_combination.color_variation.variation_value if variation_combination.color_variation else None}")
        else:
            print("DEBUG: No size or color values provided")

    if current_user.is_authenticated:
        # Authenticated user logic
        is_cart_item_exists = CartItem.objects.filter(product=product, user=current_user, variation_combination=variation_combination).exists()

        if is_cart_item_exists:
            cart_item = CartItem.objects.get(product=product, user=current_user, variation_combination=variation_combination)
            cart_item.quantity += quantity
            cart_item.save()
        else:
            cart_item = CartItem.objects.create(product=product, quantity=quantity, user=current_user, variation_combination=variation_combination)
            cart_item.save()

        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            cart_count = get_cart_count(request)
            return JsonResponse({'success': True, 'cart_count': cart_count})
        return redirect('cart')

    else:  # For non-authenticated users (session-based cart handling)
        try:
            cart = Cart.objects.get(cart_id=_cart_id(request))
        except Cart.DoesNotExist:
            cart = Cart.objects.create(cart_id=_cart_id(request))
        cart.save()

        is_cart_item_exists = CartItem.objects.filter(product=product, cart=cart, variation_combination=variation_combination).exists()

        if is_cart_item_exists:
            cart_item = CartItem.objects.get(product=product, cart=cart, variation_combination=variation_combination)
            cart_item.quantity += quantity
            cart_item.save()
        else:
            cart_item = CartItem.objects.create(product=product, quantity=quantity, cart=cart, variation_combination=variation_combination)
            cart_item.save()

        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            cart_count = get_cart_count(request)
            return JsonResponse({'success': True, 'cart_count': cart_count})
        return redirect('cart')




def remove_cart(request, product_id, cart_item_id):
    product = get_object_or_404(Product, id=product_id)
    
    try:
        if request.user.is_authenticated:
            # If the user is authenticated, find the cart item by user
            cart_item = CartItem.objects.get(product=product, user=request.user, id=cart_item_id)
        else:
            # Otherwise, use session-based cart_id to find the cart and cart item
            cart = Cart.objects.get(cart_id=_cart_id(request))
            cart_item = CartItem.objects.get(product=product, cart=cart, id=cart_item_id)
        if cart_item.quantity > 1:
            cart_item.quantity -= 1
            cart_item.save()
        else:
            cart_item.delete()
    
    except CartItem.DoesNotExist:
        # Handle the case where the cart item does not exist
        pass
    return redirect('cart')





def remove_cart_item(request, product_id, cart_item_id):
    product = get_object_or_404(Product, id=product_id)
    
    try:
        if request.user.is_authenticated:
            # If the user is authenticated, find the cart item by user
            cart_item = CartItem.objects.get(product=product, user=request.user, id=cart_item_id)
        else:
            # Otherwise, use session-based cart_id to find the cart and cart item
            cart = Cart.objects.get(cart_id=_cart_id(request))
            cart_item = CartItem.objects.get(product=product, cart=cart, id=cart_item_id)
        
        cart_item.delete()
        return redirect('cart')
    
    except CartItem.DoesNotExist:
        # Handle the case where the cart item does not exist
        pass






def cart(request, total =0, quantity =0, cart_item = None):
    cart_items = [] 
    try:
        discount = 0
        grand_total = 0
        if request.user.is_authenticated:
            cart_items = CartItem.objects.filter(user = request.user, is_active=True)
        else:

            cart = Cart.objects.get(cart_id=_cart_id(request))
            cart_items = CartItem.objects.filter(cart=cart, is_active=True)
        for cart_item in cart_items:
            # Calculate original price total
            original_total = cart_item.product.price * cart_item.quantity
            # Calculate discounted price total
            discounted_total = cart_item.product.discounted_price * cart_item.quantity
            total += discounted_total
            quantity += cart_item.quantity

        # Calculate total discount amount (original - discounted)
        discount = sum((cart_item.product.price - cart_item.product.discounted_price) * cart_item.quantity for cart_item in cart_items)
        grand_total = total
    except ObjectDoesNotExist:
        pass

    context = {
        'total': total, 
        'quantity': quantity,
        'cart_items': cart_items,
        'discount'  : discount,
        'grand_total': grand_total
    }
    return render(request,'store/cart.html', context)


@login_required(login_url="login")
def checkout(request, total=0, quantity=0, cart_item=None):
    cart_items = []
    discount = 0  # Initialize discount with a default value
    grand_total = 0  # Initialize grand_total with a default value
    try:
        # Get the cart
        if request.user.is_authenticated:
            cart_items = CartItem.objects.filter(user = request.user, is_active=True)
        else:

            cart = Cart.objects.get(cart_id=_cart_id(request))
            cart_items = CartItem.objects.filter(cart=cart, is_active=True)

        # Calculate total and quantity
        for cart_item in cart_items:
            # Calculate original price total
            original_total = cart_item.product.price * cart_item.quantity
            # Calculate discounted price total
            discounted_total = cart_item.product.discounted_price * cart_item.quantity
            total += discounted_total
            quantity += cart_item.quantity

        # Calculate total discount amount (original - discounted)
        discount = sum((cart_item.product.price - cart_item.product.discounted_price) * cart_item.quantity for cart_item in cart_items)
        grand_total = total

    except ObjectDoesNotExist:
        # If cart or cart items do not exist, return default values
        pass

    context = {
        'total': total,
        'quantity': quantity,
        'cart_items': cart_items,
        'discount': discount,
        'grand_total': grand_total,
    }
    return render(request, 'store/checkout.html', context)


