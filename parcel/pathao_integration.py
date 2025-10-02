# Pathao API Integration
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, JsonResponse
import json
import requests
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from .models import PathaoCourier, PathaoCity, PathaoZone, PathaoArea
import logging
import time

logger = logging.getLogger(__name__)





class PathaoAPIClient:
    """Enhanced Pathao API Client with improved error handling and functionality"""

    def __init__(self):
        self.base_url = getattr(settings, 'PATHAO_BASE_URL', 'https://api-hermes.pathao.com')
        self.client_id = getattr(settings, 'PATHAO_CLIENT_ID', '')
        self.client_secret = getattr(settings, 'PATHAO_CLIENT_SECRET', '')
        self.username = getattr(settings, 'PATHAO_USERNAME', '')
        self.password = getattr(settings, 'PATHAO_PASSWORD', '')
        self.store_id = getattr(settings, 'PATHAO_STORE_ID', '')
        self.access_token = None
        self.token_expires_at = None
        self.max_retries = 3
        self.timeout = 30

        # Validate required settings (store_id can be obtained from API)
        if not all([self.client_id, self.client_secret, self.username, self.password]):
            raise ValidationError("Missing required Pathao API settings")

    def authenticate(self):
        """Authenticate with Pathao API and get access token"""
        url = f"{self.base_url}/aladdin/api/v1/issue-token"
        payload = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'username': self.username,
            'password': self.password,
            'grant_type': 'password'
        }
        headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}

        try:
            logger.info("Authenticating with Pathao API")
            logger.info(f"Auth URL: {url}")
            logger.info(f"Auth payload keys: {list(payload.keys())}")  # Don't log sensitive data
            response = requests.post(url, json=payload, headers=headers, timeout=self.timeout)
            logger.info(f"Auth response status: {response.status_code}")
            logger.info(f"Auth response: {response.text}")

            if response.status_code == 200:
                data = response.json()
                self.access_token = data.get('access_token')
                self.token_expires_at = data.get('expires_in')
                if self.access_token:
                    logger.info("Pathao authentication successful")
                    # Try to get stores after successful authentication
                    stores = self.get_stores()
                    if stores and len(stores) > 0:
                        # Update store_id if not set or different
                        api_store_id = stores[0].get('store_id')
                        if api_store_id and str(api_store_id) != str(self.store_id):
                            logger.info(f"Updating store_id from {self.store_id} to {api_store_id}")
                            self.store_id = str(api_store_id)
                    return True
                else:
                    logger.error(f"No access token received from Pathao. Response: {data}")
                    return False
            else:
                logger.error(f"Pathao authentication failed: {response.status_code} - {response.text}")
                # Try alternative base URL if sandbox fails
                if "courier-api-sandbox" in self.base_url:
                    alt_url = self.base_url.replace("courier-api-sandbox", "api-hermes")
                    logger.info(f"Trying alternative URL: {alt_url}")
                    alt_response = requests.post(alt_url + "/aladdin/api/v1/issue-token", json=payload, headers=headers, timeout=self.timeout)
                    logger.info(f"Alt auth response status: {alt_response.status_code}")
                    if alt_response.status_code == 200:
                        alt_data = alt_response.json()
                        self.access_token = alt_data.get('access_token')
                        if self.access_token:
                            logger.info("Pathao authentication successful with alternative URL")
                            self.base_url = alt_url
                            return True
                return False

        except requests.exceptions.RequestException as e:
            logger.error(f"Pathao authentication request error: {str(e)}")
            return False

    def get_headers(self):
        """Get headers with authorization token"""
        if not self.access_token:
            if not self.authenticate():
                raise ValidationError("Failed to authenticate with Pathao API")

        return {
            'Authorization': f'Bearer {self.access_token}',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }

    def _make_request(self, method, url, **kwargs):
        """Make HTTP request with retry logic"""
        headers = kwargs.pop('headers', self.get_headers())
        kwargs['headers'] = headers
        kwargs['timeout'] = kwargs.get('timeout', self.timeout)

        for attempt in range(self.max_retries):
            try:
                response = requests.request(method, url, **kwargs)

                # Handle token expiration
                if response.status_code == 401:
                    logger.warning("Token expired, re-authenticating")
                    self.access_token = None
                    headers = self.get_headers()
                    kwargs['headers'] = headers
                    response = requests.request(method, url, **kwargs)

                return response

            except requests.exceptions.RequestException as e:
                logger.error(f"Request error on attempt {attempt + 1}: {str(e)}")
                if attempt < self.max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    raise

    def get_cities(self):
        """Get list of cities from Pathao"""
        url = f"{self.base_url}/aladdin/api/v1/city-list"

        try:
            response = self._make_request('GET', url)

            if response.status_code == 200:
                data = response.json()
                logger.info("Cities API response received")

                # Extract cities from nested data structure
                cities = []
                if 'data' in data and 'data' in data['data']:
                    cities = data['data']['data']

                # Update database
                for city in cities:
                    PathaoCity.objects.update_or_create(
                        city_id=city['city_id'],
                        defaults={'city_name': city['city_name'], 'is_active': True}
                    )

                return cities
            else:
                logger.error(f"Failed to get cities: {response.status_code} - {response.text}")
                return []

        except Exception as e:
            logger.error(f"Error getting cities: {str(e)}")
            return []

    def get_zones(self, city_id):
        """Get list of zones for a city"""
        url = f"{self.base_url}/aladdin/api/v1/cities/{city_id}/zone-list"

        try:
            response = self._make_request('GET', url)

            if response.status_code == 200:
                data = response.json()
                logger.info(f"Zones API response received for city {city_id}")

                zones = []
                if 'data' in data and 'data' in data['data']:
                    zones = data['data']['data']

                # Update database
                try:
                    city = PathaoCity.objects.get(city_id=city_id)
                    for zone in zones:
                        PathaoZone.objects.update_or_create(
                            zone_id=zone['zone_id'],
                            defaults={'zone_name': zone['zone_name'], 'city': city, 'is_active': True}
                        )
                except PathaoCity.DoesNotExist:
                    logger.error(f"City {city_id} not found in database")

                return zones
            else:
                logger.error(f"Failed to get zones: {response.status_code} - {response.text}")
                return []

        except Exception as e:
            logger.error(f"Error getting zones: {str(e)}")
            return []

    def get_stores(self):
        """Get list of stores from Pathao"""
        url = f"{self.base_url}/aladdin/api/v1/stores"

        try:
            response = self._make_request('GET', url)

            if response.status_code == 200:
                data = response.json()
                logger.info("Stores API response received")
                logger.info(f"Stores data: {data}")

                # Extract stores from nested data structure
                stores = []
                if 'data' in data and 'data' in data['data']:
                    stores = data['data']['data']
                    logger.info(f"Found {len(stores)} stores")
                    for store in stores:
                        logger.info(f"Store: ID={store.get('store_id')}, Name={store.get('store_name')}")

                return stores
            else:
                logger.error(f"Failed to get stores: {response.status_code} - {response.text}")
                return []

        except Exception as e:
            logger.error(f"Error getting stores: {str(e)}")
            return []

    def get_areas(self, zone_id):
        """Get list of areas for a zone"""
        url = f"{self.base_url}/aladdin/api/v1/zones/{zone_id}/area-list"

        try:
            response = self._make_request('GET', url)

            if response.status_code == 200:
                data = response.json()
                logger.info(f"Areas API response received for zone {zone_id}")

                areas = []
                if 'data' in data and 'data' in data['data']:
                    areas = data['data']['data']

                # Update database
                try:
                    zone = PathaoZone.objects.get(zone_id=zone_id)
                    for area in areas:
                        PathaoArea.objects.update_or_create(
                            area_id=area['area_id'],
                            defaults={'area_name': area['area_name'], 'zone': zone, 'is_active': True}
                        )
                except PathaoZone.DoesNotExist:
                    logger.error(f"Zone {zone_id} not found in database")

                return areas
            else:
                logger.error(f"Failed to get areas: {response.status_code} - {response.text}")
                return []

        except Exception as e:
            logger.error(f"Error getting areas: {str(e)}")
            return []

    def get_delivery_cost(self, city_id, zone_id, delivery_type=48, item_type=2, item_weight=1):
        """Calculate delivery cost"""
        url = f"{self.base_url}/aladdin/api/v1/merchant/price-plan"
        payload = {
            'store_id': self.store_id,
            'item_type': item_type,
            'delivery_type': delivery_type,
            'item_weight': item_weight,
            'recipient_city': city_id,
            'recipient_zone': zone_id
        }

        try:
            response = self._make_request('POST', url, json=payload)

            if response.status_code == 200:
                data = response.json()
                logger.info("Delivery cost calculated successfully")
                # Transform response to match expected format
                if 'data' in data and 'price' in data['data']:
                    return {'data': {'total_price': data['data']['price']}}
                return data
            else:
                logger.error(f"Failed to calculate delivery cost: {response.status_code} - {response.text}")
                return None

        except Exception as e:
            logger.error(f"Error calculating delivery cost: {str(e)}")
            return None

    # parcel/pathao_integration.py - Update the create_order method to notify admin on failure

    # parcel/pathao_integration.py - Update the create_order method to notify admin on failure

    def create_order(self, order_data):
        """Create a new order"""
        url = f"{self.base_url}/aladdin/api/v1/orders"

        # Validate required fields
        required_fields = [
            'store_id', 'merchant_order_id', 'recipient_name', 'recipient_phone',
            'recipient_address', 'item_quantity', 'item_weight', 'amount_to_collect'
        ]  # According to Pathao API documentation

        for field in required_fields:
            if field not in order_data:
                logger.error(f"Missing required field: {field}")
                self.notify_admin_error(f"Missing required field in order creation: {field}", order_data)
                return None

        # Set defaults
        order_data.setdefault('delivery_type', 48)
        order_data.setdefault('item_type', 2)
        order_data.setdefault('special_instruction', '')

        try:
            response = self._make_request('POST', url, json=order_data)

            if response.status_code == 200:
                data = response.json()
                logger.info(f"Order created successfully: {order_data.get('merchant_order_id')}")
                return data
            else:
                logger.error(f"Failed to create order: {response.status_code} - {response.text}")
                self.notify_admin_error("Order creation failed", {"response": response.text, "payload": order_data})
                return None

        except Exception as e:
            logger.error(f"Error creating order: {str(e)}")
            self.notify_admin_error("Exception in order creation", {"error": str(e), "payload": order_data})
            return None

    def track_order(self, consignment_id):
        """Track an order by consignment ID"""
        url = f"{self.base_url}/aladdin/api/v1/orders/{consignment_id}"

        try:
            response = self._make_request('GET', url)

            if response.status_code == 200:
                data = response.json()
                logger.info(f"Order tracking successful for: {consignment_id}")
                return data
            else:
                logger.error(f"Failed to track order: {response.status_code} - {response.text}")
                return None

        except Exception as e:
            logger.error(f"Error tracking order: {str(e)}")
            return None

    def cancel_order(self, consignment_id):
        """Cancel an order"""
        url = f"{self.base_url}/aladdin/api/v1/orders/{consignment_id}/cancel"

        try:
            response = self._make_request('POST', url)

            if response.status_code == 200:
                data = response.json()
                logger.info(f"Order cancelled successfully: {consignment_id}")
                return data
            else:
                logger.error(f"Failed to cancel order: {response.status_code} - {response.text}")
                return None

        except Exception as e:
            logger.error(f"Error cancelling order: {str(e)}")
            return None

    def notify_admin_error(self, message, payload=None):
        """Notify admin about API errors"""
        try:
            subject = f"Pathao API Error: {message}"
            body = f"Error: {message}\n\n"
            if payload:
                body += f"Payload: {json.dumps(payload, indent=2)}\n\n"

            send_mail(
                subject,
                body,
                settings.EMAIL_HOST_USER,
                [getattr(settings, 'ADMIN_EMAIL', settings.EMAIL_HOST_USER)],
                fail_silently=True,
            )
            logger.info("Admin notification sent for Pathao API error")
        except Exception as e:
            logger.error(f"Failed to send admin notification: {str(e)}")

@csrf_exempt
def pathao_webhook(request):
    """Handle Pathao webhook updates for order status changes"""
    if request.method == 'POST':
        try:
            payload = json.loads(request.body)
            logger.info(f"Pathao webhook received: {payload}")

            consignment_id = payload.get('consignment_id')
            status = payload.get('order_status')

            if not consignment_id or not status:
                logger.error("Missing consignment_id or order_status in webhook payload")
                return HttpResponse(status=400)

            # Update PathaoCourier
            try:
                pathao_courier = PathaoCourier.objects.get(consignment_id=consignment_id)
                pathao_courier.delivery_status = status
                pathao_courier.save()
                logger.info(f"Updated PathaoCourier {consignment_id} status to {status}")
            except PathaoCourier.DoesNotExist:
                logger.error(f"PathaoCourier with consignment_id {consignment_id} not found")
                return HttpResponse(status=404)

            # Update Order status
            status_map = {
                'Pending': 'New',
                'Picked': 'Accepted',
                'In Transit': 'On the way',
                'Delivered': 'Completed',
                'Cancelled': 'Cancelled',
                'Returned': 'Returned'
            }

            order = pathao_courier.order
            old_status = order.status
            new_status = status_map.get(status, order.status)

            if old_status != new_status:
                order.status = new_status
                order.save()
                logger.info(f"Updated Order {order.order_number} status from {old_status} to {new_status}")

                # Handle inventory adjustments for cancellations/returns
                if new_status in ['Cancelled', 'Returned']:
                    _handle_inventory_return(order)

            return HttpResponse(status=200)

        except json.JSONDecodeError:
            logger.error("Invalid JSON in webhook payload")
            return HttpResponse(status=400)
        except Exception as e:
            logger.error(f"Error processing webhook: {str(e)}")
            return HttpResponse(status=500)

    return HttpResponse(status=405)


def _handle_inventory_return(order):
    """Handle inventory return for cancelled/returned orders"""
    from store.models import InventoryLog

    try:
        for order_product in order.orderproduct_set.all():
            if order_product.variation_combination:
                order_product.variation_combination.stock += order_product.quantity
                order_product.variation_combination.save()

                # Log the inventory change
                InventoryLog.objects.create(
                    product=order_product.product,
                    variation_combination=order_product.variation_combination,
                    change=order_product.quantity,
                    reason='cancel'
                )
            else:
                order_product.product.stock += order_product.quantity
                order_product.product.save()

                # Log the inventory change
                InventoryLog.objects.create(
                    product=order_product.product,
                    change=order_product.quantity,
                    reason='cancel'
                )

        logger.info(f"Inventory returned for cancelled order {order.order_number}")

    except Exception as e:
        logger.error(f"Error handling inventory return for order {order.order_number}: {str(e)}")


def create_pathao_shipment(order):
    """Create a Pathao shipment for an order"""
    from orders.models import OrderProduct

    try:
        pathao_client = PathaoAPIClient()

        # Calculate total weight and quantity
        total_weight = 0
        total_quantity = 0
        item_descriptions = []

        for order_product in order.orderproduct_set.all():
            total_weight += order_product.quantity
            total_quantity += order_product.quantity
            item_descriptions.append(f"{order_product.product.name} (x{order_product.quantity})")

        # Prepare order data
        order_data = {
            'store_id': pathao_client.store_id,
            'merchant_order_id': order.order_number,
            'sender_name': f"{order.first_name} {order.last_name}",
            'sender_phone': order.phone,
            'recipient_name': f"{order.first_name} {order.last_name}",
            'recipient_phone': order.phone,
            'recipient_address': order.full_address(),
            'city_id': order.pathao_city_id,
            'zone_id': order.pathao_zone_id,
            'area_id': order.pathao_area_id,
            'special_instruction': order.order_note or '',
            'item_quantity': total_quantity,
            'item_weight': total_weight,
            'amount_to_collect': float(order.order_total) if order.payment_method == 'Cash on Delivery' else 0,
            'item_description': ', '.join(item_descriptions[:3]),  # Limit to first 3 items
            'delivery_type': 48,  # Standard delivery
            'item_type': 2  # Parcel
        }

        # Create Pathao order
        pathao_response = pathao_client.create_order(order_data)

        if pathao_response and 'data' in pathao_response:
            pathao_data = pathao_response['data']

            # Create PathaoCourier record
            pathao_courier = PathaoCourier.objects.create(
                order=order,
                consignment_id=pathao_data.get('consignment_id'),
                merchant_order_id=order.order_number,
                delivery_status=pathao_data.get('order_status', 'Pending'),
                delivery_fee=pathao_data.get('delivery_fee', 0)
            )

            logger.info(f"Pathao shipment created for order {order.order_number}")
            return pathao_courier

        else:
            logger.error(f"Failed to create Pathao shipment for order {order.order_number}")
            return None

    except Exception as e:
        logger.error(f"Error creating Pathao shipment for order {order.order_number}: {str(e)}")
        return None


def get_parcel_status(consignment_id):
    """Get current status of a parcel"""
    try:
        pathao_client = PathaoAPIClient()
        tracking_data = pathao_client.track_order(consignment_id)

        if tracking_data and 'data' in tracking_data:
            return tracking_data['data']
        else:
            logger.error(f"Failed to get tracking data for {consignment_id}")
            return None

    except Exception as e:
        logger.error(f"Error getting parcel status for {consignment_id}: {str(e)}")
        return None


def cancel_parcel_shipment(consignment_id):
    """Cancel a parcel shipment"""
    try:
        pathao_client = PathaoAPIClient()
        cancel_response = pathao_client.cancel_order(consignment_id)

        if cancel_response:
            logger.info(f"Parcel shipment cancelled: {consignment_id}")
            return True
        else:
            logger.error(f"Failed to cancel parcel shipment: {consignment_id}")
            return False

    except Exception as e:
        logger.error(f"Error cancelling parcel shipment {consignment_id}: {str(e)}")
        return False