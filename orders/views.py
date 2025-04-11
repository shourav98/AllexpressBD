from decimal import Decimal
import datetime
import requests
from django.conf import settings
from django.contrib import messages
from django.core.mail import send_mail
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt

from .forms import OrderForm, PaymentMethodForm
from .models import Order, Payment, OrderProduct
from carts.models import CartItem


def payments(request):
    if request.method == 'POST':
        order_number = request.POST.get('order_number')
        payment_method = request.POST.get('payment_method')

        try:
            order = Order.objects.get(user=request.user, is_ordered=False, order_number=order_number)
        except Order.DoesNotExist:
            messages.error(request, "Order not found.")
            return redirect('checkout')

        payment = Payment(
            user=request.user,
            payment_id=order_number,
            payment_method=payment_method,
            amount_paid=str(order.order_total),
            status='Pending' if payment_method == 'Cash on Delivery' else 'Completed',
        )
        payment.save()

        order.payment = payment
        if payment_method == 'Cash on Delivery':
            order.is_ordered = True
        else:
            order.is_ordered = False
        order.status = 'New'
        order.save()

        cart_items = CartItem.objects.filter(user=request.user)
        for item in cart_items:
            order_product = OrderProduct()
            order_product.order = order
            order_product.payment = payment
            order_product.user = request.user
            order_product.product = item.product
            order_product.quantity = item.quantity
            order_product.product_price = item.product.price
            order_product.total_amount = item.sub_total()
            order_product.ordered = True
            order_product.save()
            order_product.variations.set(item.variations.all())

        CartItem.objects.filter(user=request.user).delete()
        return redirect('order_complete', order_number=order.order_number)

    return render(request, 'orders/payments.html')


@csrf_exempt
def place_order(request):
    current_user = request.user
    
    # If the cart count is less than or equal to 0, then redirect back to shop
    cart_items = CartItem.objects.filter(user=current_user)
    cart_count = cart_items.count()
    if cart_count <= 0:
        print("Cart is empty, redirecting to store.")
        return redirect('store')
    
    grand_total = Decimal(0)
    discount = Decimal(0)
    total = Decimal(0)
    for cart_item in cart_items:
        total += Decimal(cart_item.product.price) * cart_item.quantity
    discount = Decimal('0.5') * total
    grand_total = total - discount
    
    if request.method == 'POST':
        form = OrderForm(request.POST)
        payment_method = PaymentMethodForm(request.POST)
        payment_method_name = request.POST.get('payment_method')
        print(f"Payment method: {payment_method_name}")
        
        if form.is_valid() and payment_method.is_valid():
            try:
                with transaction.atomic():
                    # Store all the billing information inside the order table
                    data = Order()
                    data.user = current_user
                    data.first_name = form.cleaned_data['first_name']
                    data.last_name = form.cleaned_data['last_name']
                    data.phone = form.cleaned_data['phone']
                    data.email = form.cleaned_data['email']
                    data.address_line_1 = form.cleaned_data['address_line_1']
                    data.address_line_2 = form.cleaned_data['address_line_2']
                    data.country = form.cleaned_data['country']
                    data.state = form.cleaned_data['state']
                    data.city = form.cleaned_data['city']
                    data.order_note = form.cleaned_data['order_note']
                    data.order_total = grand_total
                    data.discount = discount
                    data.ip = request.META.get('REMOTE_ADDR')
                    data.payment_method = payment_method.cleaned_data['payment_method']
                    data.save()

                    # Generate order number
                    yr = int(datetime.date.today().strftime('%Y'))
                    dt = int(datetime.date.today().strftime('%d'))
                    mt = int(datetime.date.today().strftime('%m'))
                    d = datetime.date(yr, mt, dt)
                    current_date = d.strftime('%Y%m%d')
                    order_number = current_date + str(data.id)
                    data.order_number = order_number
                    data.save()
                    print(f"Order saved: {data.order_number}")

                    # Send confirmation email after saving the order
                    send_order_confirmation_email(data)

                    # Handle COD option
                    if payment_method_name == 'Cash on Delivery':
                        data.is_ordered = True
                    else:
                        data.is_ordered = False
                    data.status = 'Pending'
                    data.save()
                    print(f"Order created: {data.order_number}, is_ordered={data.is_ordered}, status={data.status}")

                    payment = Payment(
                        user=request.user,
                        payment_id=order_number,
                        payment_method=payment_method_name,
                        amount_paid=str(data.order_total),
                        status='Pending' if payment_method_name == 'Cash on Delivery' else 'Completed',
                    )
                    payment.save()
                    print(f"Payment created: {payment.payment_id}, status={payment.status}")

                    # Create OrderProduct entries
                    for item in cart_items:
                        order_product = OrderProduct()
                        order_product.order = data
                        order_product.payment = payment
                        order_product.user = request.user
                        order_product.product = item.product
                        order_product.quantity = item.quantity
                        order_product.product_price = item.product.price
                        order_product.total_amount = item.sub_total()

                        # Handle variations
                        color_variation = item.variations.filter(variation_category__iexact='color').first()
                        size_variation = item.variations.filter(variation_category__iexact='size').first()
                        order_product.color = color_variation.variation_value if color_variation else ''
                        order_product.size = size_variation.variation_value if size_variation else ''

                        order_product.ordered = True
                        try:
                            order_product.save()
                            print(f"OrderProduct saved: ID={order_product.id}, Product={order_product.product.product_name}")
                        except Exception as e:
                            print(f"Error saving OrderProduct: {e}")
                            raise

                        # Add variations to the ManyToManyField
                        variations_to_add = []
                        if color_variation:
                            variations_to_add.append(color_variation)
                        if size_variation:
                            variations_to_add.append(size_variation)
                        if variations_to_add:
                            try:
                                order_product.variations.set(variations_to_add)
                                print(f"Variations set: {variations_to_add}")
                            except Exception as e:
                                print(f"Error setting variations: {e}")
                                raise

                        print(f"OrderProduct created: Product={order_product.product.product_name}, ordered={order_product.ordered}, variations={order_product.variations.all()}")

                    CartItem.objects.filter(user=current_user).delete()
                    print("Cart items deleted.")

                # Handle payment method (outside the transaction block to ensure the order is committed)
                if data.payment_method == 'SSLcommerz':
                    sslcommerz_url = "https://sandbox.sslcommerz.com/gwprocess/v4/api.php"
                    payload = {
                        'store_id': settings.SSLCOMMERZ_STORE_ID,
                        'store_passwd': settings.SSLCOMMERZ_STORE_PASS,
                        'total_amount': grand_total,
                        'currency': 'BDT',
                        'tran_id': data.order_number,
                        'success_url': f'{settings.BASE_URL}/orders/payment-success/',
                        'fail_url': f'{settings.BASE_URL}/orders/payment-failed/',
                        'cancel_url': f'{settings.BASE_URL}/orders/payment-cancel/',
                        'cus_name': data.full_name(),
                        'cus_email': data.email,
                        'cus_phone': data.phone,
                        'cus_add1': data.address_line_1,
                        'cus_city': data.city,
                        'cus_country': data.country,
                        'shipping_method': 'NO',
                        'product_name': 'Products',
                        'product_category': 'General',
                        'product_profile': 'general',
                    }
                    response = requests.post(sslcommerz_url, data=payload)
                    ssl_response = response.json()
                    print(f"SSLcommerz redirect: {ssl_response['GatewayPageURL']}")
                    return redirect(ssl_response['GatewayPageURL'])

                return redirect('order_complete', order_number=data.order_number)
            except Exception as e:
                print(f"Error in place_order: {e}")
                messages.error(request, "An error occurred while placing your order. Please try again.")
                return redirect('checkout')
    print("Invalid form data.")
    return redirect('checkout')




# from decimal import Decimal
# import datetime
# import requests
# from django.conf import settings
# from django.contrib import messages
# from django.core.mail import send_mail
# from django.http import HttpResponse
# from django.shortcuts import render, redirect
# from django.views.decorators.csrf import csrf_exempt

# from .forms import OrderForm, PaymentMethodForm
# from .models import Order, Payment, OrderProduct
# from carts.models import CartItem


# def payments(request):
#     if request.method == 'POST':
#         order_number = request.POST.get('order_number')
#         payment_method = request.POST.get('payment_method')

#         try:
#             order = Order.objects.get(user=request.user, is_ordered=False, order_number=order_number)
#         except Order.DoesNotExist:
#             messages.error(request, "Order not found.")
#             return redirect('checkout')

#         payment = Payment(
#             user=request.user,
#             payment_id=order_number,
#             payment_method=payment_method,
#             amount_paid=str(order.order_total),
#             status='Pending' if payment_method == 'Cash on Delivery' else 'Completed',
#         )
#         payment.save()

#         order.payment = payment
#         if payment_method == 'Cash on Delivery':
#             order.is_ordered = True
#         else:
#             order.is_ordered = False
#         order.status = 'New'
#         order.save()

#         cart_items = CartItem.objects.filter(user=request.user)
#         for item in cart_items:
#             order_product = OrderProduct()
#             order_product.order = order
#             order_product.payment = payment
#             order_product.user = request.user
#             order_product.product = item.product
#             order_product.quantity = item.quantity
#             order_product.product_price = item.product.price
#             order_product.total_amount = item.sub_total()
#             order_product.ordered = True
#             order_product.save()
#             order_product.variations.set(item.variations.all())

#         CartItem.objects.filter(user=request.user).delete()
#         return redirect('order_complete', order_number=order.order_number)

#     return render(request, 'orders/payments.html')


# @csrf_exempt

# def place_order(request):
#     current_user = request.user
    
#     # If the cart count is less than or equal to 0, then redirect back to shop
#     cart_items = CartItem.objects.filter(user=current_user)
#     cart_count = cart_items.count()
#     if cart_count <= 0:
#         return redirect('store')
    
#     grand_total = Decimal(0)
#     discount = Decimal(0)
#     total = Decimal(0)
#     for cart_item in cart_items:
#         total += Decimal(cart_item.product.price) * cart_item.quantity
#     discount = Decimal('0.5') * total
#     grand_total = total - discount
    
#     if request.method == 'POST':
#         form = OrderForm(request.POST)
#         payment_method = PaymentMethodForm(request.POST)
#         payment_method_name = request.POST.get('payment_method')
#         print(request.POST['payment_method'],"@@@@@@@@@@@@@")
#         if form.is_valid() and payment_method.is_valid():
#             # Store all the billing information inside the order table
#             data = Order()
#             data.user = current_user
#             data.first_name = form.cleaned_data['first_name']
#             data.last_name = form.cleaned_data['last_name']
#             data.phone = form.cleaned_data['phone']
#             data.email = form.cleaned_data['email']
#             data.address_line_1 = form.cleaned_data['address_line_1']
#             data.address_line_2 = form.cleaned_data['address_line_2']
#             data.country = form.cleaned_data['country']
#             data.state = form.cleaned_data['state']
#             data.city = form.cleaned_data['city']
#             data.order_note = form.cleaned_data['order_note']
#             data.order_total = grand_total
#             data.discount = discount
#             data.ip = request.META.get('REMOTE_ADDR')
#             data.payment_method = payment_method.cleaned_data['payment_method']
#             data.save()

#             # Generate order number
#             yr = int(datetime.date.today().strftime('%Y'))
#             dt = int(datetime.date.today().strftime('%d'))
#             mt = int(datetime.date.today().strftime('%m'))
#             d = datetime.date(yr, mt, dt)
#             current_date = d.strftime('%Y%m%d')
#             order_number = current_date + str(data.id)
#             data.order_number = order_number
#             data.save()

#             # Send confirmation email after saving the order
#             send_order_confirmation_email(data)

                        
#             # Handle COD option
#             # data.is_ordered = True 
#             if payment_method_name == 'Cash on Delivery':
#                 data.is_ordered = True
#             else:
#                 data.is_ordered = False
#             data.status = 'Pending'
#             data.save()
#             payment = Payment(
#                 user=request.user,
#                 payment_id=order_number,
#                 payment_method=payment_method,
#                 amount_paid=str(data.order_total),
#                 status='Pending' if payment_method == 'Cash on Delivery' else 'Completed',
#             )
#             payment.save()
            
#             for item in cart_items:
#                 order_product = OrderProduct()
#                 order_product.order = data
#                 order_product.payment = payment
#                 order_product.user = request.user
#                 order_product.product = item.product
#                 order_product.quantity = item.quantity
#                 order_product.product_price = item.product.price
#                 variation = item.variations.first() 
                
#                 color_variation = item.variations.filter(variation_category__iexact='color').first()
#                 if color_variation:
#                     order_product.color = color_variation.variation_value
#                 else:
#                     order_product.color = ''  
                    
                    
#                 size_variation = item.variations.filter(variation_category__iexact='size').first()
#                 if size_variation:
#                     order_product.size = size_variation.variation_value
#                 else:
#                     order_product.size = ''  


#                 color_variation = item.variations.filter(variation_category__iexact='color').first()
#                 size_variation = item.variations.filter(variation_category__iexact='size').first()

#                 order_product.color = color_variation.variation_value if color_variation else ''
#                 order_product.size = size_variation.variation_value if size_variation else ''

#                 # if variation:
#                 #     print(variation)
#                 #     order_product.variations = variation
#                 #     order_product.color = item.color
#                 #     order_product.size = item.size
#                 order_product.total_amount = item.sub_total()
#                 order_product.ordered = True
#                 order_product.save()

#                 # Check if variations exist before setting them
#                 # if item.variations:
#                 #     order_product.variations.set(item.variations.all())
#                 order_product.save()   
#             CartItem.objects.filter(user=current_user).delete()


#             # Handle payment method
#             if data.payment_method == 'SSLcommerz':
#                 sslcommerz_url = "https://sandbox.sslcommerz.com/gwprocess/v4/api.php"
#                 payload = {
#                     'store_id': settings.SSLCOMMERZ_STORE_ID,
#                     'store_passwd': settings.SSLCOMMERZ_STORE_PASS,
#                     'total_amount': grand_total,
#                     'currency': 'BDT',
#                     'tran_id': data.order_number,
#                     'success_url': 'http://127.0.0.1:8000/orders/payment-success/',
#                     'fail_url': 'http://127.0.0.1:8000/orders/payment-failed/',
#                     'cancel_url': 'http://127.0.0.1:8000/orders/payment-cancel/',
#                     'cus_name': data.full_name(),
#                     'cus_email': data.email,
#                     'cus_phone': data.phone,
#                     'cus_add1': data.address_line_1,
#                     'cus_city': data.city,
#                     'cus_country': data.country,
#                     'shipping_method': 'NO',
#                     'product_name': 'Products',
#                     'product_category': 'General',
#                     'product_profile': 'general',
#                 }

#                 response = requests.post(sslcommerz_url, data=payload)
#                 ssl_response = response.json()  
#                 # redirect ssl pgw
#                 return redirect(ssl_response['GatewayPageURL'])

#             return redirect('order_complete', order_number=data.order_number)
#     return redirect('checkout')
@csrf_exempt
def order_complete(request, order_number):
    try:
        # Fetch the order and associated ordered products
        order = Order.objects.get(order_number=order_number, is_ordered=True)
        ordered_products = OrderProduct.objects.filter(order=order).select_related('product')

        # Calculate subtotal and grand total
        subtotal = sum(item.product_price * item.quantity for item in ordered_products)
        discount = subtotal * 0.5  # Assuming a 50% discount as per your project requirement
        grand_total = subtotal - discount

        # Transaction ID from request
        transID = request.POST.get('tran_id') or request.GET.get('tran_id')

        context = {
            'order': order,
            'ordered_products': ordered_products,
            'subtotal': subtotal,
            'discount': discount,
            'grand_total': grand_total,
            'transaction_id': transID,
        }

        return render(request, 'orders/order_complete.html', context)
    except Order.DoesNotExist:
        messages.error(request, "Order not found.")
        return redirect('store')



import time
from django.db import transaction

@csrf_exempt
def payment_success(request):
    tran_id = request.POST.get('tran_id') or request.GET.get('tran_id')
    val_id = request.POST.get('val_id') or request.GET.get('val_id')
    print(f"Payment Success - tran_id: {tran_id}, val_id: {val_id}")

    # Retry finding the order up to 3 times with a 1-second delay
    max_retries = 3
    retry_delay = 1  # seconds
    for attempt in range(max_retries):
        try:
            with transaction.atomic():
                order = Order.objects.get(order_number=tran_id)
                print(f"Order found: {order.order_number}, is_ordered={order.is_ordered}")
                if order.is_ordered:
                    print("Order already processed.")
                    ordered_products = OrderProduct.objects.filter(order=order).select_related('product')
                    subtotal = sum(item.product_price * item.quantity for item in ordered_products)
                    return render(request, 'orders/payment_success.html', {'order': order, 'ordered_products': ordered_products, 'subtotal': subtotal})
                break  # Order found, exit the retry loop
        except Order.DoesNotExist:
            if attempt < max_retries - 1:
                print(f"Order not found on attempt {attempt + 1}, retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                print("Order not found after all retries.")
                messages.error(request, "Order not found. Please contact support.")
                return redirect('home')

    ordered_products = OrderProduct.objects.filter(order=order).select_related('product')
    print(f"OrderProduct entries: {ordered_products.count()}")
    for op in ordered_products:
        print(f"OrderProduct: Product={op.product.product_name}, ordered={op.ordered}")
    subtotal = sum(item.product_price * item.quantity for item in ordered_products)

    payment = Payment.objects.create(
        user=order.user,
        payment_id=val_id,
        payment_method='SSLcommerz',
        amount_paid=order.order_total,
        status='Completed',
    )
    order.payment = payment
    order.is_ordered = True
    order.status = 'Completed'
    order.save()
    print(f"Order updated: is_ordered={order.is_ordered}, status={order.status}")

    CartItem.objects.filter(user=order.user).delete()
    send_order_confirmation_email(order)
    print(f"Rendering payment_success.html for order: {order.order_number}")
    return render(request, 'orders/payment_success.html', {'order': order, 'ordered_products': ordered_products, 'subtotal': subtotal})



@csrf_exempt



def payment_failed(request):
    return render(request, 'orders/payment_failed.html')


def send_order_confirmation_email(order):
    subject = 'Order Confirmation'
    message = (
        f"Dear {order.full_name()},\n\n"
        f"Your order has been successfully placed!\n"
        f"Order Number: {order.order_number}\n"
        f"Total Amount: {order.order_total}\n\n"
        f"Thank you for shopping with us!"
    )
    send_mail(
        subject,
        message,
        settings.EMAIL_HOST_USER,
        [order.email],
        fail_silently=False,
    )