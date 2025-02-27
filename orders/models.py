from django.db import models
from accounts.models import Account
from store.models import Product, Variation
from django.conf import settings

# Create your models here.
from django.db import models
from django.contrib.auth.models import User

class Payment(models.Model):
    PAYMENT_STATUS = (
        ('Success', 'Success'),
        ('Failed', 'Failed'),
        ('Pending', 'Pending'),
    )

    PAYMENT_METHOD = (
        ('Cash on Delivery', 'Cash on Delivery'),
        ('SSLcommerz', 'SSLcommerz'),
    )

    # user = models.ForeignKey(User, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    payment_id = models.CharField(max_length=100)
    payment_method = models.CharField(max_length=50, choices=PAYMENT_METHOD, default="Cash on Delivery")  # Add choices here
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=10, choices=PAYMENT_STATUS)
    created_at = models.DateTimeField(auto_now_add=True)

    def _str_(self):
        return f"Payment {self.user.username} - {self.payment_id} - {self.status}"

class Order(models.Model):
    PAYMENT_METHOD =(
        ('Cash on Delivery', 'Cash on Delivery'),
        ('SSLcommerz', 'SSLcommerz'),

    )
    STATUS = (
        ('New', 'New'),
        ('Accepted', 'Accepted'),
        ('on the way', 'On the way'),
        ('Completed', 'Completed'),
        ('Cancelled', 'Cancelled'),
        ('Shipped', 'Shipped'),
    )
    
    user = models.ForeignKey(Account, on_delete=models.SET_NULL, null=True)
    payment = models.ForeignKey(Payment, on_delete=models.SET_NULL, blank=True, null=True)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD, default="Cash on Delivery")
    order_number = models.CharField(max_length=20)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    phone = models.CharField(max_length=15)
    email = models.EmailField(max_length=50)
    address_line_1 = models.CharField(max_length=50)
    address_line_2 = models.CharField(max_length=50)
    country = models.CharField(max_length=50)
    state = models.CharField(max_length=50)
    city = models.CharField(max_length=50)
    order_note = models.CharField(max_length=100, blank=True)
    order_total = models.FloatField()
    discount = models.FloatField()
    status = models.CharField(max_length=10, choices=STATUS, default="New")
    ip = models.CharField(blank=True, max_length=20)
    is_ordered = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    
    def full_address(self):
        return f"{self.address_line_1}, {self.address_line_2}"
    
    def __str__(self):
        return self.first_name

    
class OrderProduct(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    payment = models.ForeignKey(Payment, on_delete=models.SET_NULL, blank=True, null=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    #variations = models.ForeignKey(Variation, on_delete=models.CASCADE)
    variations = models.ForeignKey(Variation, on_delete=models.SET_NULL, null=True)
    color = models.CharField(max_length=100)
    size = models.CharField(max_length=100)
    quantity = models.IntegerField()
    product_price = models.FloatField()
    total_amount = models.IntegerField(default=10)
    ordered = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.product.price
    
    def __str__(self):
        # Using product name and price for a meaningful string representation
        return f"{self.product.product_name} - {self.product_price} TK "

    
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    def full_address(self):
        return f"{self.address_line_1}, {self.address_line_2}"
    

    
    
    
