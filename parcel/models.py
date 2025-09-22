from django.db import models
from orders.models import Order

# New models for Pathao city/zone/area mapping
class PathaoCity(models.Model):
    city_id = models.IntegerField(unique=True)
    city_name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.city_name

    class Meta:
        verbose_name = "Pathao City"
        verbose_name_plural = "Pathao Cities"

class PathaoZone(models.Model):
    zone_id = models.IntegerField(unique=True)
    zone_name = models.CharField(max_length=100)
    city = models.ForeignKey(PathaoCity, on_delete=models.CASCADE, related_name='zones')
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.zone_name} ({self.city.city_name})"

    class Meta:
        verbose_name = "Pathao Zone"
        verbose_name_plural = "Pathao Zones"

class PathaoArea(models.Model):
    area_id = models.IntegerField(unique=True)
    area_name = models.CharField(max_length=100)
    zone = models.ForeignKey(PathaoZone, on_delete=models.CASCADE, related_name='areas')
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.area_name} ({self.zone.zone_name})"

    class Meta:
        verbose_name = "Pathao Area"
        verbose_name_plural = "Pathao Areas"

class PathaoCourier(models.Model):
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='pathao_courier')
    consignment_id = models.CharField(max_length=50, unique=True, null=True, blank=True)
    merchant_order_id = models.CharField(max_length=100, null=True, blank=True)
    delivery_status = models.CharField(max_length=50, default='Pending')
    delivery_fee = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Pathao Courier for Order {self.order.order_number} - {self.consignment_id}"

    class Meta:
        verbose_name = "Pathao Courier"
        verbose_name_plural = "Pathao Couriers"




# Pathao API client is now in pathao_integration.py



    


    