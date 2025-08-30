# category/models.py
from django.db import models
from django.urls import reverse
from django.utils.text import slugify

class Category(models.Model):
    category_name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(max_length=255, blank=True)
    cat_image = models.ImageField(upload_to="photos/categories", blank=True)
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='subcategories'
    )
    is_active = models.BooleanField(default=True)

    def get_subcategories(self):
        return self.subcategories.filter(is_active=True)

    class Meta:
        verbose_name = "Category"
        verbose_name_plural = "Categories"

    def get_url(self):
        return reverse('products_by_category', args=[self.slug])

    def __str__(self):
        if self.parent:
            return f"{self.parent.category_name} > {self.category_name}"
        return self.category_name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.category_name)
        super(Category, self).save(*args, **kwargs)

    def is_parent(self):
        return self.parent is None

    def get_subcategories(self):
        return self.subcategories.filter(is_active=True)
    




class Brand(models.Model):
    brand_name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    brand_image = models.ImageField(upload_to="photos/brands", blank=True, null=True)
    description = models.TextField(max_length=500, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Brand"
        verbose_name_plural = "Brands"

    def get_url(self):
        return reverse('products_by_brand', args=[self.slug])

    def __str__(self):
        return self.brand_name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.brand_name)
        super(Brand, self).save(*args, **kwargs)