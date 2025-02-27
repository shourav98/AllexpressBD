from django.shortcuts import render, redirect, get_object_or_404
from store.models import Product, Variation
from .models import Cart, CartItem
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse

from django.contrib.auth.decorators import login_required
# Create your views here.

def _cart_id(request):
    cart = request.session.session_key
    if not cart:
        cart = request.session.create()
    return cart

def add_cart(request, product_id):
    current_user = request.user
    product = Product.objects.get(id=product_id)
    
    product_variation = []

    if request.method == 'POST':
        for item in request.POST:
            key = item
            value = request.POST[key]

            # Mapping radio buttons to variation categories
            if key == 'radio_color':  
                key = 'color'
            elif key == 'radio_size':  
                key = 'size'

            try:
                variation = Variation.objects.get(product=product, variation_category__iexact=key, variation_value__iexact=value)
                product_variation.append(variation)
            except:
                pass

    # Sort the product_variation list to ensure consistent order
    product_variation = sorted(product_variation, key=lambda v: v.variation_category)

    if current_user.is_authenticated:
        # Authenticated user logic
        is_cart_item_exists = CartItem.objects.filter(product=product, user=current_user).exists()

        if is_cart_item_exists:
            cart_items = CartItem.objects.filter(product=product, user=current_user)
            existing_variations_list = []
            item_ids = []

            for item in cart_items:
                existing_variations = item.variations.all()
                # Sort existing variations to ensure consistent order
                sorted_existing_variations = sorted(existing_variations, key=lambda v: v.variation_category)
                existing_variations_list.append(list(sorted_existing_variations))
                item_ids.append(item.id)

            if product_variation in existing_variations_list:
                index = existing_variations_list.index(product_variation)
                item_id = item_ids[index]
                cart_item = CartItem.objects.get(id=item_id)
                cart_item.quantity += 1
                cart_item.save()
            else:
                new_cart_item = CartItem.objects.create(product=product, quantity=1, user=current_user)
                if product_variation:
                    new_cart_item.variations.clear()
                    new_cart_item.variations.add(*product_variation)
                new_cart_item.save()
        else:
            cart_item = CartItem.objects.create(product=product, quantity=1, user=current_user)
            if product_variation:
                cart_item.variations.clear()
                cart_item.variations.add(*product_variation)
            cart_item.save()

        return redirect('cart')

    else:  # For non-authenticated users (session-based cart handling)
        try:
            cart = Cart.objects.get(cart_id=_cart_id(request))
        except Cart.DoesNotExist:
            cart = Cart.objects.create(cart_id=_cart_id(request))
        cart.save()

        is_cart_item_exists = CartItem.objects.filter(product=product, cart=cart).exists()

        if is_cart_item_exists:
            cart_items = CartItem.objects.filter(product=product, cart=cart)
            existing_variations_list = []
            item_ids = []

            for item in cart_items:
                existing_variations = item.variations.all()
                # Sort existing variations to ensure consistent order
                sorted_existing_variations = sorted(existing_variations, key=lambda v: v.variation_category)
                existing_variations_list.append(list(sorted_existing_variations))
                item_ids.append(item.id)

            if product_variation in existing_variations_list:
                index = existing_variations_list.index(product_variation)
                item_id = item_ids[index]
                cart_item = CartItem.objects.get(id=item_id)
                cart_item.quantity += 1
                cart_item.save()
            else:
                new_cart_item = CartItem.objects.create(product=product, quantity=1, cart=cart)
                if product_variation:
                    new_cart_item.variations.clear()
                    new_cart_item.variations.add(*product_variation)
                new_cart_item.save()
        else:
            cart_item = CartItem.objects.create(product=product, quantity=1, cart=cart)
            if product_variation:
                cart_item.variations.clear()
                cart_item.variations.add(*product_variation)
            cart_item.save()

        return redirect('cart')






# def remove_cart(request, product_id, cart_item_id):
#     cart = Cart.objects.get(cart_id = _cart_id(request))
#     product = get_object_or_404(Product, id=product_id)
#     try:
#         cart_item = CartItem.objects.get(product=product, cart=cart, id=cart_item_id)

#         if cart_item.quantity > 1:
#             cart_item.quantity -= 1
#             cart_item.save()
#         else:
#             cart_item.delete()
#     except:
#         pass
#     return redirect('cart')

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



# from django.shortcuts import get_object_or_404

# def remove_cart_item(request, product_id, cart_item_id):
#     product = get_object_or_404(Product, id=product_id)
    
#     try:
#         if request.user.is_authenticated:
#             # If the user is authenticated, find the cart item by user
#             cart_item = CartItem.objects.get(product=product, user=request.user, id=cart_item_id)
#         else:
#             # Otherwise, use session-based cart_id to find the cart and cart item
#             cart = Cart.objects.get(cart_id=_cart_id(request))
#             cart_item = CartItem.objects.get(product=product, cart=cart, id=cart_item_id)
        
#         cart_item.delete()
    
#     except CartItem.DoesNotExist:
#         # Handle the case where the cart item does not exist
#         pass

#     return redirect('cart')



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
            total += (cart_item.product.price * cart_item.quantity)
            quantity += cart_item.quantity

        discount = (50*total)/100
        grand_total = total - discount
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
            total += (cart_item.product.price * cart_item.quantity)
            quantity += cart_item.quantity

        # Calculate discount and grand total
        discount = (50 * total) / 100
        grand_total = total - discount

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


