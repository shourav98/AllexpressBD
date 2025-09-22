from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator

from .models import PathaoCourier, PathaoCity, PathaoZone, PathaoArea
from .pathao_integration import PathaoAPIClient, get_parcel_status, cancel_parcel_shipment
from orders.models import Order


@staff_member_required
def parcel_dashboard(request):
    """Admin dashboard for parcel management"""
    # Get parcel statistics
    total_parcels = PathaoCourier.objects.count()
    pending_parcels = PathaoCourier.objects.filter(delivery_status='Pending').count()
    delivered_parcels = PathaoCourier.objects.filter(delivery_status='Delivered').count()
    cancelled_parcels = PathaoCourier.objects.filter(delivery_status='Cancelled').count()

    # Get recent parcels
    recent_parcels = PathaoCourier.objects.select_related('order').order_by('-created_at')[:10]

    context = {
        'total_parcels': total_parcels,
        'pending_parcels': pending_parcels,
        'delivered_parcels': delivered_parcels,
        'cancelled_parcels': cancelled_parcels,
        'recent_parcels': recent_parcels,
    }

    return render(request, 'parcel/dashboard.html', context)


@staff_member_required
def parcel_list(request):
    """List all parcels with filtering and pagination"""
    parcels = PathaoCourier.objects.select_related('order').order_by('-created_at')

    # Filtering
    status = request.GET.get('status')
    if status:
        parcels = parcels.filter(delivery_status=status)

    search = request.GET.get('search')
    if search:
        parcels = parcels.filter(
            consignment_id__icontains=search
        ) | parcels.filter(
            order__order_number__icontains=search
        )

    # Pagination
    paginator = Paginator(parcels, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'status_filter': status,
        'search_query': search,
    }

    return render(request, 'parcel/parcel_list.html', context)


@staff_member_required
def parcel_detail(request, consignment_id):
    """View detailed information about a specific parcel"""
    parcel = get_object_or_404(PathaoCourier, consignment_id=consignment_id)

    # Get tracking information
    tracking_data = get_parcel_status(consignment_id)

    context = {
        'parcel': parcel,
        'tracking_data': tracking_data,
    }

    return render(request, 'parcel/parcel_detail.html', context)


@staff_member_required
@require_POST
def refresh_parcel_status(request, consignment_id):
    """Refresh parcel status from Pathao API"""
    parcel = get_object_or_404(PathaoCourier, consignment_id=consignment_id)

    tracking_data = get_parcel_status(consignment_id)

    if tracking_data:
        # Update parcel status
        if 'order_status' in tracking_data:
            parcel.delivery_status = tracking_data['order_status']
            parcel.save()

            # Update order status
            status_map = {
                'Pending': 'New',
                'Picked': 'Accepted',
                'In Transit': 'On the way',
                'Delivered': 'Completed',
                'Cancelled': 'Cancelled'
            }
            parcel.order.status = status_map.get(tracking_data['order_status'], parcel.order.status)
            parcel.order.save()

        messages.success(request, f"Status updated for parcel {consignment_id}")
    else:
        messages.error(request, f"Failed to refresh status for parcel {consignment_id}")

    return redirect('parcel_detail', consignment_id=consignment_id)


@staff_member_required
@require_POST
def cancel_parcel(request, consignment_id):
    """Cancel a parcel shipment"""
    parcel = get_object_or_404(PathaoCourier, consignment_id=consignment_id)

    if parcel.delivery_status in ['Delivered', 'Cancelled']:
        messages.error(request, "Cannot cancel a delivered or already cancelled parcel")
        return redirect('parcel_detail', consignment_id=consignment_id)

    success = cancel_parcel_shipment(consignment_id)

    if success:
        parcel.delivery_status = 'Cancelled'
        parcel.save()
        parcel.order.status = 'Cancelled'
        parcel.order.save()
        messages.success(request, f"Parcel {consignment_id} has been cancelled")
    else:
        messages.error(request, f"Failed to cancel parcel {consignment_id}")

    return redirect('parcel_detail', consignment_id=consignment_id)


@staff_member_required
def bulk_parcel_actions(request):
    """Handle bulk actions on parcels"""
    if request.method == 'POST':
        action = request.POST.get('action')
        parcel_ids = request.POST.getlist('parcel_ids')

        if not parcel_ids:
            messages.error(request, "No parcels selected")
            return redirect('parcel_list')

        parcels = PathaoCourier.objects.filter(id__in=parcel_ids)

        if action == 'refresh_status':
            success_count = 0
            for parcel in parcels:
                tracking_data = get_parcel_status(parcel.consignment_id)
                if tracking_data and 'order_status' in tracking_data:
                    parcel.delivery_status = tracking_data['order_status']
                    parcel.save()
                    success_count += 1

            messages.success(request, f"Status refreshed for {success_count} out of {len(parcel_ids)} parcels")

        elif action == 'mark_delivered':
            updated = parcels.filter(delivery_status__in=['In Transit', 'Picked']).update(delivery_status='Delivered')
            # Update corresponding orders
            for parcel in parcels.filter(delivery_status='Delivered'):
                parcel.order.status = 'Completed'
                parcel.order.save()

            messages.success(request, f"Marked {updated} parcels as delivered")

        elif action == 'export_csv':
            # This would implement CSV export functionality
            messages.info(request, "CSV export functionality to be implemented")

    return redirect('parcel_list')


# AJAX endpoints for dynamic content loading
def get_zones_ajax(request):
    """AJAX endpoint to get zones for a city"""
    city_id = request.GET.get('city_id')
    if not city_id:
        return JsonResponse({'error': 'City ID required'}, status=400)

    try:
        zones = list(PathaoZone.objects.filter(
            city__city_id=city_id,
            is_active=True
        ).values('zone_id', 'zone_name'))

        return JsonResponse({'zones': zones})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def get_areas_ajax(request):
    """AJAX endpoint to get areas for a zone"""
    zone_id = request.GET.get('zone_id')
    if not zone_id:
        return JsonResponse({'error': 'Zone ID required'}, status=400)

    try:
        areas = list(PathaoArea.objects.filter(
            zone__zone_id=zone_id,
            is_active=True
        ).values('area_id', 'area_name'))

        return JsonResponse({'areas': areas})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
