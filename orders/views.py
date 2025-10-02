
from decimal import Decimal
import datetime
import requests
from django.conf import settings
from django.contrib import messages
from django.core.mail import send_mail
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from django.contrib import auth

from django.http import JsonResponse
import json
from django.contrib.admin.views.decorators import staff_member_required

import time
from django.db import transaction

from .forms import OrderForm, PaymentMethodForm
from .models import Order, Payment, OrderProduct
from carts.models import CartItem

from parcel.models import PathaoCourier, PathaoZone, PathaoArea, PathaoCity
from parcel.pathao_integration import PathaoAPIClient


from django.views.decorators.http import require_GET
import logging

logger = logging.getLogger(__name__)





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
            print(f"DEBUG: Payments - Creating OrderProduct for {item.product.name}, CartItem VC: {item.variation_combination}")
            order_product = OrderProduct()
            order_product.order = order
            order_product.payment = payment
            order_product.user = request.user
            order_product.product = item.product
            order_product.quantity = item.quantity
            order_product.product_price = item.product.price
            order_product.total_amount = item.sub_total()
            order_product.ordered = True
            order_product.variation_combination = item.variation_combination
            if item.variation_combination:
                order_product.color = item.variation_combination.color_variation.variation_value if item.variation_combination.color_variation else ''
                order_product.size = item.variation_combination.size_variation.variation_value if item.variation_combination.size_variation else ''
                print(f"DEBUG: Payments - Set OrderProduct color: '{order_product.color}', size: '{order_product.size}'")
            else:
                print("DEBUG: Payments - No variation combination for OrderProduct")
            order_product.save()

        CartItem.objects.filter(user=request.user).delete()
        return redirect('order_complete', order_number=order.order_number)

    return render(request, 'orders/payments.html')



@csrf_exempt  # If needed, but consider removing if CSRF is handled properly
def place_order(request):
    if not request.user.is_authenticated:
        return redirect('login')

    current_user = request.user

    # Load cities
    cities = PathaoCity.objects.filter(is_active=True)
    if not cities:
        try:
            pathao_client = PathaoAPIClient()
            cities_data = pathao_client.get_cities()
            for city in cities_data:
                PathaoCity.objects.get_or_create(
                    city_id=city.get("city_id"),
                    defaults={
                        "city_name": city.get("city_name"),
                        "is_active": True
                    }
                )
            cities = PathaoCity.objects.filter(is_active=True)
        except Exception as e:
            logger.exception(f"Failed to fetch and populate cities: {e}")
            messages.error(request, "Failed to load delivery locations. Please try again.")
            return redirect('checkout')

    cart_items = CartItem.objects.filter(user=current_user)
    cart_count = cart_items.count()
    if cart_count <= 0:
        messages.error(request, "Your cart is empty.")
        return redirect('store')

    # Calculate order totals
    total = Decimal(0)
    for cart_item in cart_items:
        total += Decimal(cart_item.product.price) * cart_item.quantity
    discount = Decimal('0.5') * total  # Note: This seems like 50% discount; adjust if needed
    grand_total = total - discount

    if request.method == 'POST':
        form = OrderForm(request.POST)
        payment_method = request.POST.get('payment_method')
        city_id = request.POST.get('pathao_city_id')
        zone_id = request.POST.get('pathao_zone_id')
        area_id = request.POST.get('pathao_area_id')

        # Store form data in session for persistence
        if form.is_valid():
            request.session['checkout_form_data'] = {
                'first_name': form.cleaned_data.get('first_name'),
                'last_name': form.cleaned_data.get('last_name'),
                'phone': form.cleaned_data.get('phone'),
                'email': form.cleaned_data.get('email'),
                'address_line_1': form.cleaned_data.get('address_line_1'),
                'address_line_2': form.cleaned_data.get('address_line_2'),
                'order_note': form.cleaned_data.get('order_note'),
                'pathao_city_id': city_id,
                'pathao_zone_id': zone_id,
                'pathao_area_id': area_id,
                'payment_method': payment_method,
            }

        if form.is_valid() and city_id and zone_id and area_id:
            try:
                with transaction.atomic():
                    # Create order instance from form but don't save yet
                    order = form.save(commit=False)
                    city_obj = PathaoCity.objects.get(city_id=city_id)
                    zone_obj = PathaoZone.objects.get(zone_id=zone_id)
                    area_obj = PathaoArea.objects.get(area_id=area_id)
                    order.user = current_user
                    order.order_total = grand_total
                    order.discount = discount
                    order.ip = request.META.get('REMOTE_ADDR')
                    order.payment_method = payment_method

                    # Save to get an ID
                    order.save()

                    # Generate order number with the actual ID
                    today = datetime.date.today()
                    order_number = f"{today.strftime('%Y%m%d')}{order.id}"
                    order.order_number = order_number
                    order.save()

                    # Try to create Pathao shipment (optional)
                    pathao_courier = None
                    delivery_fee = Decimal('0.00')
                    try:
                        pathao_client = PathaoAPIClient()
                        if pathao_client.authenticate():
                            # Calculate total weight
                            total_weight = sum(item.quantity for item in cart_items)

                            # Get delivery cost (with fallback)
                            delivery_cost = pathao_client.get_delivery_cost(
                                city_id=int(city_id),
                                zone_id=int(zone_id),
                                delivery_type=48,
                                item_type=2,
                                item_weight=total_weight
                            )

                            if delivery_cost and 'data' in delivery_cost:
                                delivery_fee = Decimal(str(delivery_cost['data']['total_price']))
                            else:
                                logger.warning("Could not calculate delivery cost. Using default fee.")
                                delivery_fee = Decimal('100.00')

                            # Update order total with delivery fee
                            order.order_total += delivery_fee
                            order.save()

                            # Create Pathao order
                            pathao_order_data = {
                                "store_id": settings.PATHAO_STORE_ID,
                                "merchant_order_id": order.order_number,
                                "sender_name": order.full_name(),
                                "sender_phone": order.phone,
                                "recipient_name": order.full_name(),
                                "recipient_phone": order.phone,
                                "recipient_address": order.full_address(),
                                "recipient_city": int(city_id),  # Updated field name
                                "recipient_zone": int(zone_id),  # Updated field name
                                "recipient_area": int(area_id),  # Updated field name
                                "special_instruction": order.order_note or "None",
                                "item_quantity": total_weight,
                                "item_weight": total_weight,
                                "amount_to_collect": float(order.order_total) if payment_method == 'Cash on Delivery' else 0,
                                "item_description": "E-commerce products",
                                "delivery_type": 48,
                                "item_type": 2
                            }

                            pathao_order = pathao_client.create_order(pathao_order_data)

                            if pathao_order and 'data' in pathao_order:
                                # Create Pathao courier record
                                consignment_id = pathao_order['data'].get('consignment_id')
                                delivery_status = pathao_order['data'].get('order_status', 'Pending')

                                # If consignment_id is None or empty, use mock ID
                                if not consignment_id:
                                    consignment_id = f"MOCK-{order.order_number}"
                                    delivery_status = 'Mock'

                                pathao_courier = PathaoCourier(
                                    order=order,
                                    consignment_id=consignment_id,
                                    merchant_order_id=order.order_number,
                                    delivery_status=delivery_status,
                                    delivery_fee=delivery_fee
                                )
                                pathao_courier.save()
                                logger.info(f"Pathao shipment created for order {order.order_number}")
                            else:
                                logger.error(f"Pathao order creation failed for order {order.order_number}: {pathao_order}")
                        else:
                            logger.warning("Pathao authentication failed, proceeding without courier service")
                    except Exception as e:
                        logger.exception(f"Pathao integration failed for order {order.order_number}: {e}")
                        # Continue without Pathao

                    # Ensure PathaoCourier record exists
                    if not pathao_courier:
                        # Create mock consignment ID for failed integrations
                        mock_consignment_id = f"MOCK-{order.order_number}"
                        try:
                            pathao_courier = PathaoCourier(
                                order=order,
                                consignment_id=mock_consignment_id,
                                merchant_order_id=order.order_number,
                                delivery_status='Mock',
                                delivery_fee=delivery_fee if 'delivery_fee' in locals() else Decimal('0.00')
                            )
                            pathao_courier.save()
                            logger.info(f"PathaoCourier created with mock consignment ID {mock_consignment_id} for order {order.order_number}")
                            print(f"DEBUG: PathaoCourier saved with ID {pathao_courier.id}, consignment_id {pathao_courier.consignment_id}")
                        except Exception as e:
                            logger.error(f"Failed to save PathaoCourier for order {order.order_number}: {e}")
                            print(f"DEBUG: Failed to save PathaoCourier: {e}")

                    # Create payment record
                    payment = Payment(
                        user=request.user,
                        payment_id=order_number,
                        payment_method=payment_method,
                        amount_paid=str(order.order_total),
                        status='Pending' if payment_method == 'Cash on Delivery' else 'Pending',
                    )
                    payment.save()

                    # Create order products
                    for item in cart_items:
                        print(f"DEBUG: Creating OrderProduct for {item.product.name}, CartItem VC: {item.variation_combination}")
                        order_product = OrderProduct(
                            order=order,
                            payment=payment,
                            user=request.user,
                            product=item.product,
                            quantity=item.quantity,
                            product_price=item.product.price,
                            total_amount=item.sub_total(),
                            ordered=True
                        )
                        order_product.save()

                        # Add variation combination
                        order_product.variation_combination = item.variation_combination
                        if item.variation_combination:
                            order_product.color = item.variation_combination.color_variation.variation_value if item.variation_combination.color_variation else ''
                            order_product.size = item.variation_combination.size_variation.variation_value if item.variation_combination.size_variation else ''
                            print(f"DEBUG: Set OrderProduct color: '{order_product.color}', size: '{order_product.size}'")
                        else:
                            print("DEBUG: No variation combination for OrderProduct")
                        order_product.save()

                    # Clear cart
                    CartItem.objects.filter(user=current_user).delete()

                    # Set order status
                    if payment_method == 'Cash on Delivery':
                        order.is_ordered = True
                        order.status = 'New'
                    else:
                        # For SSLcommerz, wait for payment confirmation
                        order.is_ordered = False
                        order.status = 'Pending'
                    order.save()

                    # Send confirmation email
                    send_order_confirmation_email(order)

                    # Clear checkout form data from session after successful order
                    if 'checkout_form_data' in request.session:
                        del request.session['checkout_form_data']

                    # Redirect based on payment method
                    if payment_method == 'SSLcommerz':
                        # SSLcommerz payment flow
                        sslcommerz_url = "https://sandbox.sslcommerz.com/gwprocess/v4/api.php"
                        payload = {
                            'store_id': settings.SSLCOMMERZ_STORE_ID,
                            'store_passwd': settings.SSLCOMMERZ_STORE_PASS,
                            'total_amount': float(order.order_total),
                            'currency': 'BDT',
                            'tran_id': order.order_number,
                            'success_url': f'{settings.BASE_URL}/orders/payment-success/',
                            'fail_url': f'{settings.BASE_URL}/orders/payment-failed/',
                            'cancel_url': f'{settings.BASE_URL}/orders/payment-cancel/',
                            'cus_name': order.full_name(),
                            'cus_email': order.email,
                            'cus_phone': order.phone,
                            'cus_add1': order.address_line_1,
                            'cus_city': city_obj.city_name,
                            'cus_state': zone_obj.zone_name,
                            'cus_country': 'Bangladesh',
                            'ship_name': order.full_name(),
                            'ship_add1': order.address_line_1,
                            'ship_city': city_obj.city_name,
                            'ship_state': zone_obj.zone_name,
                            'ship_postcode': '1200',
                            'ship_country': 'Bangladesh',
                            'shipping_method': 'Courier',
                            'product_name': 'Products',
                            'product_category': 'General',
                            'product_profile': 'general',
                        }
                        response = requests.post(sslcommerz_url, data=payload)
                        if response.status_code != 200:
                            logger.error(f"SSLcommerz API error: {response.status_code} - {response.text}")
                            messages.error(request, "Payment gateway error. Please try again.")
                            return redirect('payment_failed')
                        ssl_response = response.json()
                        logger.debug(f"SSLcommerz response: {ssl_response}")
                        if 'GatewayPageURL' not in ssl_response or not ssl_response['GatewayPageURL']:
                            logger.error(f"SSLcommerz response missing or empty GatewayPageURL: {ssl_response}")
                            messages.error(request, "Payment gateway error. Please try again.")
                            return redirect('payment_failed')
                        return redirect(ssl_response['GatewayPageURL'])
                    else:
                        # Cash on Delivery
                        return redirect('order_complete', order_number=order.order_number)

            except Exception as e:
                logger.exception(f"Error in place_order: {e}")
                messages.error(request, "An error occurred while placing your order. Please try again.")
                return redirect('checkout')
        else:
            # Form validation failed
            if not form.is_valid():
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f"{field}: {error}")
            if not city_id or not zone_id or not area_id:
                messages.error(request, "Please select a valid city, zone, and area.")
            return redirect('checkout')

    # GET request - show checkout form
    form = OrderForm()

    # Pre-populate form with session data if available
    checkout_data = request.session.get('checkout_form_data')
    if checkout_data:
        form = OrderForm(initial=checkout_data)

    context = {
        'form': form,
        'cities': cities,
        'cart_items': cart_items,
        'total': total,
        'discount': discount,
        'grand_total': grand_total,
    }
    return render(request, 'store/checkout.html', context)

# orders/views.py
@require_GET
def get_zones(request):
    """Fetch zones for a city."""
    city_id = request.GET.get("city_id")
    if not city_id:
        return JsonResponse({"error": "Invalid city ID"}, status=400)

    try:
        # Try to get zones from database first
        zones = list(PathaoZone.objects.filter(
            city__city_id=city_id, 
            is_active=True
        ).values("zone_id", "zone_name"))
        
        # If no zones in database, fetch from API
        if not zones:
            pathao_client = PathaoAPIClient()
            if pathao_client.access_token:
                raw_zones = pathao_client.get_zones(city_id)
                zones = [
                    {
                        "zone_id": zone.get("zone_id"),
                        "zone_name": zone.get("zone_name")
                    }
                    for zone in raw_zones
                ]
        
        return JsonResponse({"zones": zones})
    except Exception as e:
        logger.exception("Failed to fetch zones")
        return JsonResponse({"error": str(e)}, status=500)

@require_GET
def get_areas(request):
    """Fetch areas for a zone."""
    zone_id = request.GET.get("zone_id")
    if not zone_id:
        return JsonResponse({"error": "Invalid zone ID"}, status=400)

    try:
        # Try to get areas from database first
        areas = list(PathaoArea.objects.filter(
            zone__zone_id=zone_id, 
            is_active=True
        ).values("area_id", "area_name"))
        
        # If no areas in database, fetch from API
        if not areas:
            pathao_client = PathaoAPIClient()
            if pathao_client.access_token:
                raw_areas = pathao_client.get_areas(zone_id)
                areas = [
                    {
                        "area_id": area.get("area_id"),
                        "area_name": area.get("area_name")
                    }
                    for area in raw_areas
                ]
        
        return JsonResponse({"areas": areas})
    except Exception as e:
        logger.exception("Failed to fetch areas")
        return JsonResponse({"error": str(e)}, status=500)

def track_parcel(request, order_number):
    try:
        order = Order.objects.get(order_number=order_number, user=request.user, is_ordered=True)
        logger.debug(f"Found order: {order_number} for user: {request.user}")
        
        pathao_courier = PathaoCourier.objects.get(order=order)
        logger.debug(f"Found PathaoCourier: {pathao_courier.consignment_id}")
        
        if not pathao_courier.consignment_id:
            logger.warning(f"No consignment_id for order {order_number}")
            messages.warning(request, "Tracking is not available yet. The courier order is being processed.")
            return render(request, 'orders/track_parcel.html', {
                'order': order,
                'pathao_courier': pathao_courier,
                'tracking_data': {}
            })

        pathao_client = PathaoAPIClient()
        if not pathao_client.authenticate():
            logger.error(f"Pathao API authentication failed for order {order_number}")
            messages.error(request, "Unable to connect to courier service. Please try again later.")
            return render(request, 'orders/track_parcel.html', {
                'order': order,
                'pathao_courier': pathao_courier,
                'tracking_data': {}
            })

        tracking_data = pathao_client.track_order(pathao_courier.consignment_id)
        logger.debug(f"Tracking data for consignment {pathao_courier.consignment_id}: {tracking_data}")
        
        if tracking_data and isinstance(tracking_data, dict) and 'data' in tracking_data:
            order_status = tracking_data['data'].get('order_status')
            if order_status:
                pathao_courier.delivery_status = order_status
                pathao_courier.save()
                
                status_map = {
                    'Pending': 'New',
                    'Picked': 'Accepted',
                    'In Transit': 'On the way',
                    'Delivered': 'Completed',
                    'Cancelled': 'Cancelled'
                }
                order.status = status_map.get(order_status, order.status)
                order.save()
                logger.info(f"Updated order {order_number} status to {order.status}")
            else:
                logger.warning(f"No 'order_status' in tracking data for consignment {pathao_courier.consignment_id}")
                messages.warning(request, "Tracking status not available yet.")
        else:
            logger.warning(f"Invalid or empty tracking data for consignment {pathao_courier.consignment_id}")
            messages.warning(request, "Tracking information is currently unavailable.")
        
        context = {
            'order': order,
            'pathao_courier': pathao_courier,
            'tracking_data': tracking_data if tracking_data else {}
        }
        return render(request, 'orders/track_parcel.html', context)
    
    except Order.DoesNotExist:
        logger.error(f"Order {order_number} not found for user {request.user}")
        messages.error(request, "Order not found.")
        return redirect('store')
    except PathaoCourier.DoesNotExist:
        logger.error(f"PathaoCourier not found for order {order_number}")
        messages.error(request, "Tracking information not found for this order.")
        return redirect('store')
    except Exception as e:
        logger.error(f"Unexpected error in track_parcel for order {order_number}: {str(e)}")
        messages.error(request, "An error occurred while tracking your order. Please try again later.")
        return redirect('store')




@csrf_exempt
def pathao_webhook(request):
    if request.method == 'POST':
        try:
            payload = json.loads(request.body)
            consignment_id = payload.get('consignment_id')
            status = payload.get('order_status')
            
            pathao_courier = PathaoCourier.objects.get(consignment_id=consignment_id)
            pathao_courier.delivery_status = status
            pathao_courier.save()

            status_map = {
                'Pending': 'New',
                'Picked': 'Accepted',
                'In Transit': 'On the way',
                'Delivered': 'Completed',
                'Cancelled': 'Cancelled'
            }
            order = pathao_courier.order
            order.status = status_map.get(status, order.status)
            order.save()

            return HttpResponse(status=200)
        except (PathaoCourier.DoesNotExist, json.JSONDecodeError):
            return HttpResponse(status=400)
    return HttpResponse(status=405)

@csrf_exempt
def order_complete(request, order_number):
    try:
        order = Order.objects.get(order_number=order_number, is_ordered=True, user=request.user)
        ordered_products = OrderProduct.objects.filter(order=order).select_related('product')
        pathao_courier = PathaoCourier.objects.filter(order=order).first()

        # Convert all values to Decimal to ensure consistent data types
        subtotal = Decimal(sum(float(item.product_price) * item.quantity for item in ordered_products))
        discount = subtotal * Decimal('0.5')

        # Handle delivery fee (convert to Decimal if it exists)
        delivery_fee = Decimal(0)
        if pathao_courier and pathao_courier.delivery_fee:
            delivery_fee = Decimal(str(pathao_courier.delivery_fee))

        grand_total = subtotal - discount + delivery_fee

        transID = request.POST.get('tran_id') or request.GET.get('tran_id')

        context = {
            'order': order,
            'ordered_products': ordered_products,
            'subtotal': subtotal,
            'discount': discount,
            'grand_total': grand_total,
            'transaction_id': transID,
            'pathao_courier': pathao_courier,
        }
        return render(request, 'orders/order_complete.html', context)
    except Order.DoesNotExist:
        messages.error(request, "Order not found.")
        return redirect('store')





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
                # Re-authenticate the user since session may be lost during payment gateway redirect
                if not request.user.is_authenticated or request.user != order.user:
                    auth.login(request, order.user)
                    print(f"User {order.user} logged back in after payment.")
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
    subtotal = sum(item.product_price * item.quantity for item in ordered_products)

    # Update the existing payment status
    payment = Payment.objects.get(payment_id=tran_id)
    payment.status = 'Success'
    payment.save()

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




# def get_zones(request):
#     city_id = request.GET.get('city_id')
#     if city_id:
#         pathao_client = PathaoAPIClient()
#         zones = pathao_client.get_zones(city_id)
#         return JsonResponse({'zones': zones})
#     return JsonResponse({'error': 'Invalid city ID'}, status=400)

# def get_areas(request):
#     zone_id = request.GET.get('zone_id')
#     if zone_id:
#         pathao_client = PathaoAPIClient()
#         areas = pathao_client.get_areas(zone_id)
#         return JsonResponse({'areas': areas})
#     return JsonResponse({'error': 'Invalid zone ID'}, status=400)



@staff_member_required
def batch_create_orders(request):
        if request.method == 'POST':
            order_ids = request.POST.getlist('order_ids')
            pathao_client = PathaoAPIClient()
            results = []
            
            for order_id in order_ids:
                try:
                    order = Order.objects.get(id=order_id, is_ordered=True, pathao_courier__isnull=True)
                    total_weight = sum(item.quantity for item in order.orderproduct_set.all())
                    delivery_cost = pathao_client.get_delivery_cost(
                        city_id=order.pathao_city_id,
                        zone_id=order.pathao_zone_id,
                        delivery_type=48,
                        item_type=2,
                        store_id = settings.PATHAO_STORE_ID,
                        item_weight=total_weight
                    )
                    delivery_fee = Decimal(str(delivery_cost['price']))
                    order.order_total += delivery_fee
                    order.save()

                    pathao_order = pathao_client.create_order(
                        store_id=order.store_id,
                        merchant_order_id=order.order_number,
                        sender_name=order.full_name(),
                        sender_phone=order.phone,
                        recipient_name=order.full_name(),
                        recipient_phone=order.phone,
                        recipient_address=order.full_address(),
                        city_id=order.pathao_city_id,
                        zone_id=order.pathao_zone_id,
                        area_id=order.pathao_area_id,
                        special_instruction=order.order_note or "None",
                        item_quantity=total_weight,
                        item_weight=total_weight,
                        amount_to_collect=float(order.order_total) if order.payment_method == 'Cash on Delivery' else 0,
                        item_description="E-commerce products",
                        delivery_type=48,
                        item_type=2,
                        price=order.order_total
                    )

                    pathao_courier = PathaoCourier(
                        order=order,
                        consignment_id=pathao_order['consignment_id'],
                        merchant_order_id=order.order_number,
                        delivery_status=pathao_order['order_status'],
                        delivery_fee=delivery_fee
                    )
                    pathao_courier.save()
                    results.append({'order_number': order.order_number, 'status': 'Success'})
                except Exception as e:
                    pathao_client.notify_admin_error(f"Batch order creation failed for {order.order_number}: {str(e)}")
                    results.append({'order_number': order.order_number, 'status': 'Failed', 'error': str(e)})

            context = {'results': results}
            return render(request, 'orders/batch_results.html', context)
        orders = Order.objects.filter(is_ordered=True, pathao_courier__isnull=True)
        return render(request, 'orders/batch_orders.html', {'orders': orders})


# def send_order_confirmation_email(order):
#     subject = 'Order Confirmation'
#     message = (
#         f"Dear {order.full_name()},\n\n"
#         f"Your order has been successfully placed!\n"
#         f"Order Number: {order.order_number}\n"
#         f"Total Amount: {order.order_total}\n\n"
#         f"Thank you for shopping with us!"
#     )
#     send_mail(
#         subject,
#         message,
#         settings.EMAIL_HOST_USER,
#         [order.email],
#         fail_silently=False,
#     )

# Update send_order_confirmation_email
def send_order_confirmation_email(order):
    pathao_courier = PathaoCourier.objects.filter(order=order).first()
    tracking_info = (
        f"\nPathao Consignment ID: {pathao_courier.consignment_id}\n"
        f"Track your order: {settings.BASE_URL}/orders/track-parcel/{order.order_number}/\n"
        f"Estimated Delivery: { '24-48 hours' if pathao_courier.delivery_fee == 48 else '4-6 hours' }"
    ) if pathao_courier else ""

    subject = 'Order Confirmation'
    message = (
        f"Dear {order.full_name()},\n\n"
        f"Your order has been successfully placed!\n"
        f"Order Number: {order.order_number}\n"
        f"Total Amount: {order.order_total}\n"
        f"{tracking_info}\n\n"
        f"Thank you for shopping with us!"
    )
    send_mail(
        subject,
        message,
        settings.EMAIL_HOST_USER,
        [order.email],
        fail_silently=False,
    )



@csrf_exempt
def calculate_delivery_cost(request):
    if request.method == 'POST':
        city_id = request.POST.get('city_id')
        zone_id = request.POST.get('zone_id')
        
        try:
            pathao_client = PathaoAPIClient()
            total_weight = 1  # Default weight, you might calculate this based on cart items
            
            delivery_cost = pathao_client.get_delivery_cost(
                city_id=int(city_id),
                zone_id=int(zone_id),
                delivery_type=48,
                item_type=2,
                item_weight=total_weight
            )
            
            if delivery_cost and 'data' in delivery_cost:
                return JsonResponse({
                    'success': True,
                    'delivery_cost': delivery_cost['data']['total_price']
                })
            else:
                return JsonResponse({
                    'success': False,
                    'message': 'Could not calculate delivery cost',
                    'delivery_cost': 100  # Default cost
                })
                
        except Exception as e:
            logger.exception(f"Error calculating delivery cost: {e}")
            return JsonResponse({
                'success': False,
                'message': str(e),
                'delivery_cost': 100  # Default cost
            })
    
    return JsonResponse({'success': False, 'message': 'Invalid request'})