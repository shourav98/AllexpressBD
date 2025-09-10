from django.db import models
from store.models import Product, Variation
from accounts.models import Account


from django.core.exceptions import ValidationError

# Create your models here.
class Cart(models.Model):
    cart_id = models.CharField(max_length=200, blank=True)
    date_added = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.cart_id

class CartItem(models.Model):
    user = models.ForeignKey(Account, on_delete = models.CASCADE, null = True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    variations = models.ManyToManyField(Variation, blank=True)
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, null = True)
    quantity = models.IntegerField()
    is_active = models.BooleanField(default=True)

    def sub_total(self):
        return self.product.price * self.quantity
    
    def __unicode__(self):
        # return self.product
        return self.product


    def clean(self):
        # Check if enough stock exists
        if self.variations.exists():
            for variation in self.variations.all():
                if self.quantity > variation.stock:
                    raise ValidationError(f"Not enough stock for {variation.variation_value}")
        else:
            if self.quantity > self.product.stock:
                raise ValidationError("Not enough stock available")
