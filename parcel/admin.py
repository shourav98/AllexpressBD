from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from django.contrib import messages
from .models import PathaoCourier, PathaoCity, PathaoZone, PathaoArea
from .pathao_integration import PathaoAPIClient, get_parcel_status, cancel_parcel_shipment
from django.conf import settings
from django.core.mail import send_mail
from unfold.admin import ModelAdmin








import logging
from django.http import HttpResponse
import csv

logger = logging.getLogger(__name__)

@admin.register(PathaoCourier)
class PathaoCourierAdmin(admin.ModelAdmin):
    list_display = ('order_link', 'consignment_id', 'delivery_status', 'delivery_fee', 'created_at', 'get_list_actions')
    list_filter = ('delivery_status', 'created_at')
    search_fields = ('consignment_id', 'merchant_order_id', 'order__order_number')
    readonly_fields = ('created_at', 'updated_at')
    actions = ['refresh_status', 'cancel_shipments', 'export_selected', 'retry_create_pathao_order']

    def order_link(self, obj):
        url = reverse('admin:orders_order_change', args=[obj.order.id])
        return format_html('<a href="{}">{}</a>', url, obj.order.order_number)
    order_link.short_description = 'Order'

    def get_list_actions(self, obj):
        actions = []
        if obj.consignment_id:
            actions.append(format_html(
                '<a href="{}" class="button" target="_blank">Track</a>',
                reverse('parcel_detail', args=[obj.consignment_id])
            ))

            if obj.delivery_status not in ['Delivered', 'Cancelled']:
                actions.append(format_html(
                    '<a href="{}" class="button">Refresh</a>',
                    reverse('refresh_parcel_status', args=[obj.consignment_id])
                ))

                actions.append(format_html(
                    '<a href="{}" class="button" onclick="return confirm(\'Are you sure?\')">Cancel</a>',
                    reverse('cancel_parcel', args=[obj.consignment_id])
                ))
        else:
            actions.append(format_html(
                '<span>No consignment ID</span>'
            ))

        return format_html(' '.join(actions))
    get_list_actions.short_description = 'Actions'

    def retry_create_pathao_order(self, request, queryset):
        """Retry creating Pathao orders for selected couriers with no consignment_id"""
        success_count = 0
        error_count = 0

        pathao_client = PathaoAPIClient()
        if not pathao_client.authenticate():
            self.message_user(request, "Pathao API authentication failed.", level='error')
            return

        for courier in queryset.filter(consignment_id__isnull=True):
            try:
                order = courier.order
                total_weight = sum(item.quantity for item in order.orderproduct_set.all())
                
                pathao_order_data = {
                    "store_id": settings.PATHAO_STORE_ID,
                    "merchant_order_id": order.order_number,
                    "sender_name": order.full_name(),
                    "sender_phone": order.phone,
                    "recipient_name": order.full_name(),
                    "recipient_phone": order.phone,
                    "recipient_address": order.full_address(),
                    "recipient_city": order.pathao_city_id,
                    "recipient_zone": order.pathao_zone_id,
                    "recipient_area": order.pathao_area_id,
                    "special_instruction": order.order_note or "None",
                    "item_quantity": total_weight,
                    "item_weight": total_weight,
                    "amount_to_collect": float(order.order_total) if order.payment_method == 'Cash on Delivery' else 0,
                    "item_description": "E-commerce products",
                    "delivery_type": 48,
                    "item_type": 2
                }

                pathao_order = pathao_client.create_order(pathao_order_data)
                logger.debug(f"Retry Pathao order for {order.order_number}: {pathao_order}")

                if pathao_order and 'data' in pathao_order and 'consignment_id' in pathao_order['data']:
                    courier.consignment_id = pathao_order['data']['consignment_id']
                    courier.delivery_status = pathao_order['data'].get('order_status', 'Pending')
                    courier.save()
                    success_count += 1
                    self.message_user(request, f"Successfully created Pathao order for {order.order_number}", level='success')
                else:
                    logger.error(f"Failed to retry Pathao order for {order.order_number}: {pathao_order}")
                    error_count += 1
                    self.message_user(request, f"Failed to create Pathao order for {order.order_number}", level='warning')

            except Exception as e:
                logger.error(f"Error retrying Pathao order for {courier.order.order_number}: {str(e)}")
                error_count += 1
                self.message_user(request, f"Error for {courier.order.order_number}: {str(e)}", level='error')

        if success_count > 0:
            self.message_user(request, f"Successfully created {success_count} Pathao orders")
        if error_count > 0:
            self.message_user(request, f"Failed to create {error_count} Pathao orders", level='error')

    retry_create_pathao_order.short_description = "Retry creating Pathao order"

    def refresh_status(self, request, queryset):
        """Refresh status for selected parcels"""
        success_count = 0
        error_count = 0

        for courier in queryset:
            if courier.consignment_id:
                tracking_data = get_parcel_status(courier.consignment_id)
                if tracking_data and 'order_status' in tracking_data:
                    old_status = courier.delivery_status
                    courier.delivery_status = tracking_data['order_status']
                    courier.save()

                    status_map = {
                        'Pending': 'New',
                        'Picked': 'Accepted',
                        'In Transit': 'On the way',
                        'Delivered': 'Completed',
                        'Cancelled': 'Cancelled'
                    }
                    courier.order.status = status_map.get(tracking_data['order_status'], courier.order.status)
                    courier.order.save()

                    success_count += 1
                else:
                    error_count += 1
            else:
                error_count += 1
                self.message_user(request, f"No consignment ID for order {courier.order.order_number}", level='warning')

        if success_count > 0:
            self.message_user(request, f"Successfully refreshed {success_count} parcels")
        if error_count > 0:
            self.message_user(request, f"Failed to refresh {error_count} parcels", level='warning')

    refresh_status.short_description = "Refresh status from Pathao"

    def cancel_shipments(self, request, queryset):
        """Cancel selected shipments"""
        cancelled_count = 0
        error_count = 0

        for courier in queryset:
            if courier.delivery_status not in ['Delivered', 'Cancelled'] and courier.consignment_id:
                success = cancel_parcel_shipment(courier.consignment_id)
                if success:
                    courier.delivery_status = 'Cancelled'
                    courier.save()
                    courier.order.status = 'Cancelled'
                    courier.order.save()
                    cancelled_count += 1
                else:
                    error_count += 1
            else:
                error_count += 1

        if cancelled_count > 0:
            self.message_user(request, f"Successfully cancelled {cancelled_count} shipments")
        if error_count > 0:
            self.message_user(request, f"Failed to cancel {error_count} shipments", level='error')

    cancel_shipments.short_description = "Cancel selected shipments"

    def export_selected(self, request, queryset):
        """Export selected parcels to CSV"""
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="parcels.csv"'

        writer = csv.writer(response)
        writer.writerow(['Order Number', 'Consignment ID', 'Status', 'Delivery Fee', 'Created At'])

        for courier in queryset:
            writer.writerow([
                courier.order.order_number,
                courier.consignment_id or '-',
                courier.delivery_status,
                courier.delivery_fee,
                courier.created_at
            ])

        return response

    export_selected.short_description = "Export selected to CSV"


    

@admin.register(PathaoCity)
class PathaoCityAdmin(ModelAdmin):
    list_display = ('city_id', 'city_name', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('city_name',)

@admin.register(PathaoZone)
class PathaoZoneAdmin(ModelAdmin):
    list_display = ('zone_id', 'zone_name', 'city', 'is_active')
    list_filter = ('city', 'is_active')
    search_fields = ('zone_name',)

@admin.register(PathaoArea)
class PathaoAreaAdmin(ModelAdmin):
    list_display = ('area_id', 'area_name', 'zone', 'is_active')
    list_filter = ('zone', 'is_active')
    search_fields = ('area_name',)