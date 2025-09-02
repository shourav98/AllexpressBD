from django.db import models
from category.models import Category
from django.urls import reverse
from accounts.models import Account
from django.db.models import Avg, Count
from django.utils.text import slugify
from django.core.exceptions import ValidationError
from category.models import Brand
from django.urls import NoReverseMatch


# Create your models here.



class Product(models.Model):
    name = models.CharField(max_length=255)
    product_name = models.CharField(max_length=200, unique=True)
    slug = models.SlugField(max_length=200, unique=True)
    description = models.TextField(max_length=500, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    images = models.ImageField(upload_to='photos/products')
    stock = models.IntegerField()
    is_available = models.BooleanField(default=True)
    # category = models.ForeignKey(Category, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products', null=True, blank=True)
    created_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now=True)

    brand = models.ForeignKey(Brand, on_delete=models.CASCADE, null=True, blank=True)  # New field


    @property
    def discounted_price(self):
        if self.discount_percentage and self.discount_percentage > 0:
            return self.price - (self.price * self.discount_percentage / 100)
        return self.price

    # def get_url(self):
    #     return reverse('product_detail', args=[self.category.slug, self.slug])

    def get_url(self):
        try:
            if self.category:
                return reverse("product_detail", args=[self.category.slug, self.slug])
            elif self.brand:
                return reverse("product_detail_by_brand", args=[self.brand.slug, self.slug])
        except NoReverseMatch:
            return "#"

    def __str__(self):
        return self.product_name

    def averageReviews(self):
        reviews = ReviewRating.objects.filter(product=self, status=True).aggregate(average=Avg('rating'))
        return float(reviews['average']) if reviews['average'] is not None else 0

    def countReview(self):
        reviews = ReviewRating.objects.filter(product=self, status=True).aggregate(count=Count('id'))
        return int(reviews['count']) if reviews['count'] is not None else 0
    

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.product_name)

        # Require at least a category or brand
        if not self.category and not self.brand:
            raise ValidationError("A product must be assigned to a category or a brand.")

        # If category is selected, ensure it's a subcategory
        if self.category:
            if self.category.parent is None:
                raise ValidationError(
                    "Products can only be assigned to subcategories, not parent categories."
                )

        super(Product, self).save(*args, **kwargs)
    

    # def save(self, *args, **kwargs):
    #     if not self.slug:
    #         self.slug = slugify(self.product_name)
    #     # Check if the category has a parent (i.e., is a subcategory)
    #     if self.category.parent is None:  # Changed from self.category.parent() to self.category.parent is None
    #         raise ValidationError("Products can only be assigned to subcategories, not parent categories.")
    #     super(Product, self).save(*args, **kwargs)

    # def save(self, *args, **kwargs):
    #     if not self.slug:
    #         self.slug = slugify(self.product_name)
    #     # Optional: Ensure products are only assigned to subcategories
    #     if self.category.parent():
    #         raise ValidationError("Products can only be assigned to subcategories, not parent categories.")
    #     super(Product, self).save(*args, **kwargs)
    


class VariationManager(models.Manager):
    def colors(self):
        return super(VariationManager, self).filter(variation_category='color', is_active = True)

    def sizes(self):
        return super(VariationManager, self).filter(variation_category='size', is_active = True)


variation_category_choice=(
    ('color', 'color'),
    ('size', 'size'),
)

class Variation(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    variation_category = models.CharField(max_length=100, choices=variation_category_choice)
    variation_value = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    created_date = models.DateTimeField(auto_now=True)

    objects = VariationManager()

    def __str__(self):
        return self.variation_value

class ReviewRating(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    user = models.ForeignKey('accounts.Account', on_delete=models.CASCADE)
    subject = models.CharField(max_length=100, blank=True)
    review = models.TextField(max_length=500, blank=True)
    rating = models.FloatField()
    ip = models.CharField(max_length=20, blank=True)
    status = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.subject
    
    
class ProductGallery(models.Model):
    product = models.ForeignKey(Product, default = None, on_delete=models.CASCADE)
    image = models.ImageField(upload_to = 'store/products', max_length =255)
    
    def __str__(self):
        return self.product.product_name
    
    class Meta:
        verbose_name = "Productgallery"
        verbose_name_plural = "product galleries"