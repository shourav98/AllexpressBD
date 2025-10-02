from django.contrib import admin
from django.contrib.admin import ModelAdmin
from django.contrib.auth.admin import UserAdmin, UserChangeForm, UserCreationForm, AdminPasswordChangeForm
from django.utils.html import format_html
from django.urls import path, reverse
from django.utils.translation import gettext_lazy as _
from django.db.models import Sum
from unfold.admin import ModelAdmin
from unfold.views import DashboardView
from image_cropping import ImageCroppingMixin
from django.template.response import TemplateResponse

from accounts.models import Account, UserProfile
from orders.models import Order, OrderProduct, Payment
from store.models import Cart, CartItem, Category, Brand, Product, Variation, VariationCombination, ReviewRating, ProductGallery, InventoryLog

# Import the dashboard callback
from Allexpress.utils import dashboard_callback



from unfold.admin import ModelAdmin
from unfold.contrib.forms.widgets import WysiwygWidget
from django.contrib import admin

@admin.register(Order)
class OrderAdmin(ModelAdmin):
    dashboard_callback = dashboard_callback
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('dashboard/', self.admin_site.admin_view(self.dashboard_view), name='dashboard'),
        ]
        return custom_urls + urls
    
    def dashboard_view(self, request):
        context = {
            **self.admin_site.each_context(request),
            'title': 'Dashboard',
        }
        context = dashboard_callback(request, context)
        return TemplateResponse(request, "admin/dashboard.html", context)

class CustomDashboardView(DashboardView):
    template_name = 'admin/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return dashboard_callback(self.request, context)

class CustomAdminSite(admin.AdminSite):
    index_template = "admin/dashboard.html"
    site_title = _("Ecommerce Admin")
    site_header = _("Ecommerce Administration")
    index_title = _("Dashboard")
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('dashboard/', self.admin_view(CustomDashboardView.as_view()), name='dashboard'),
        ]
        return custom_urls + urls
    
    def index(self, request, extra_context=None):
        """
        Override the default admin index to use our dashboard
        """
        context = {
            **self.each_context(request),
            'title': self.index_title,
            'subtitle': None,
            **(extra_context or {}),
        }
        
        context = dashboard_callback(request, context)
        
        request.current_app = self.name
        return TemplateResponse(request, self.index_template, context)

# Create custom admin site instance
admin_site = CustomAdminSite(name='custom_admin')

# Now register all models with the custom admin site
@admin_site.register(Account)
class AccountAdmin(UserAdmin, ModelAdmin):
    list_display = ("email", "first_name", "last_name", "username", "last_login", "date_joined", "is_active")
    list_display_links = ("email", "first_name", "last_name")
    readonly_fields = ("last_login", "date_joined")
    ordering = ("-date_joined",)
    filter_horizontal = ("groups", "user_permissions")
    list_filter = ("is_staff", "is_superuser", "is_active", "groups")
    search_fields = ("email", "first_name", "last_name", "username")

    form = UserChangeForm
    add_form = UserCreationForm
    change_password_form = AdminPasswordChangeForm

    fieldsets = (
        ("Login Credentials", {"fields": ("email", "password")}),
        ("Personal Info", {"fields": ("first_name", "last_name", "username", "phone_number")}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )

@admin_site.register(UserProfile)
class UserProfileAdmin(ModelAdmin):
    def thumbnail(self, obj):
        if obj.profile_picture:
            return format_html('<img src="{}" width="30" style="border-radius:50%;" />', obj.profile_picture.url)
        return "No image"

    thumbnail.short_description = "Profile Picture"

    list_display = ("thumbnail", "user", "city", "state", "country")
    list_display_links = ("user",)
    list_filter = ("city", "state", "country")
    search_fields = ("user__email", "city", "state", "country")
    ordering = ("user__email",)

@admin_site.register(Cart)
class CartAdmin(ModelAdmin):
    list_display = ("cart_id", "date_added")
    search_fields = ("cart_id",)

@admin_site.register(CartItem)
class CartItemAdmin(ModelAdmin):
    list_display = ("product", "cart", "quantity", "is_active")
    list_filter = ("is_active", "product")
    search_fields = ("product__name",)

@admin_site.register(Category)
class CategoryAdmin(ModelAdmin):
    list_display = ("category_name", "slug", "parent", "is_active")
    list_editable = ("is_active",)
    search_fields = ("category_name",)
    prepopulated_fields = {"slug": ("category_name",)}
    list_filter = ("is_active", "parent")

@admin_site.register(Brand)
class BrandAdmin(ModelAdmin):
    list_display = ("brand_name", "slug", "is_active")
    list_filter = ("is_active",)
    search_fields = ("brand_name", "description")
    prepopulated_fields = {"slug": ("brand_name",)}

@admin_site.register(Order)
class OrderAdmin(ModelAdmin):
    list_display = ("order_number", "user", "order_total", "status", "created_at")
    list_filter = ("status", "payment_method", "created_at")
    search_fields = ("order_number", "user__email", "first_name", "last_name")
    readonly_fields = ("order_number", "created_at", "updated_at")
    list_per_page = 20

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')

@admin_site.register(OrderProduct)
class OrderProductAdmin(ModelAdmin):
    list_display = ("order", "product", "quantity", "product_price", "total_amount")
    list_filter = ("created_at",)
    search_fields = ("order__order_number", "product__name")
    list_per_page = 20

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('order', 'product')

@admin_site.register(Payment)
class PaymentAdmin(ModelAdmin):
    list_display = ("payment_id", "user", "amount_paid", "payment_method", "status", "created_at")
    list_filter = ("status", "payment_method", "created_at")
    search_fields = ("payment_id", "user__email")
    list_per_page = 20

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')

@admin_site.register(Product)
class ProductAdmin(ModelAdmin):
    list_display = ("name", "price", "stock", "category", "brand", "is_available", "low_stock")
    list_editable = ("stock", "is_available", "price")
    list_filter = ("is_available", "category", "brand")
    search_fields = ("name", "description")
    prepopulated_fields = {"slug": ("name",)}
    list_per_page = 20

    def low_stock(self, obj):
        return obj.stock < 5
    low_stock.boolean = True
    low_stock.short_description = "Low Stock"

@admin_site.register(Variation)
class VariationAdmin(ModelAdmin):
    list_display = ("product", "variation_category", "variation_value", "is_active")
    list_editable = ("is_active",)
    list_filter = ("variation_category", "is_active", "product")
    search_fields = ("product__name", "variation_value")
    list_per_page = 20

@admin_site.register(VariationCombination)
class VariationCombinationAdmin(ModelAdmin):
    list_display = ("product", "size_variation", "color_variation", "stock", "is_active")
    list_editable = ("stock", "is_active")
    list_filter = ("product", "size_variation", "color_variation")
    search_fields = ("product__name", "size_variation__variation_value", "color_variation__variation_value")
    list_per_page = 20

@admin_site.register(ReviewRating)
class ReviewRatingAdmin(ModelAdmin):
    list_display = ("product", "user", "rating", "status", "created_at")
    list_filter = ("rating", "status", "created_at")
    search_fields = ("product__name", "user__email", "subject")
    list_editable = ("status",)
    list_per_page = 20

@admin_site.register(InventoryLog)
class InventoryLogAdmin(ModelAdmin):
    list_display = ("product", "variation_combination", "change", "reason", "created_at")
    list_filter = ("reason", "created_at")
    search_fields = ("product__name", "variation_combination__size_variation__variation_value", "variation_combination__color_variation__variation_value")
    readonly_fields = ("created_at",)
    list_per_page = 20

# ProductGallery inline
class ProductGalleryInline(admin.TabularInline):
    model = ProductGallery
    extra = 1
    classes = ('collapse',)

# Add the inline to ProductAdmin
ProductAdmin.inlines = [ProductGalleryInline]

# Replace the default admin site
admin.site = admin_site