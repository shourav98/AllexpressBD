#  ACCOUNTS
from unfold.admin import ModelAdmin
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from unfold.forms import UserChangeForm, UserCreationForm, AdminPasswordChangeForm
from django.utils.html import format_html
from .models import Account, UserProfile


@admin.register(Account)
class AccountAdmin(BaseUserAdmin, ModelAdmin):
    list_display = ("email", "first_name", "last_name", "username", "last_login", "date_joined", "is_active")
    list_display_links = ("email", "first_name", "last_name")
    readonly_fields = ("last_login", "date_joined")
    ordering = ("-date_joined",)
    filter_horizontal = ("groups", "user_permissions")
    list_filter = ("is_staff", "is_superuser", "is_active", "groups")

    form = UserChangeForm
    add_form = UserCreationForm
    change_password_form = AdminPasswordChangeForm

    fieldsets = (
        ("Login Credentials", {"fields": ("email", "password")}),
        ("Personal Info", {"fields": ("first_name", "last_name", "username", "phone_number")}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )


@admin.register(UserProfile)
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




# from unfold.admin import ModelAdmin
# from django.contrib import admin
# from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
# from unfold.forms import UserChangeForm, UserCreationForm, AdminPasswordChangeForm
# from django.utils.html import format_html
# from .models import Account, UserProfile

# @admin.register(Account)
# class AccountAdmin(BaseUserAdmin, ModelAdmin):
#     list_display = ('email', 'first_name', 'last_name', 'username', 'last_login', 'date_joined', 'is_active')
#     list_display_links = ('email', 'first_name', 'last_name')
#     readonly_fields = ('last_login', 'date_joined')
#     ordering = ('date_joined',)
#     filter_horizontal = ('groups', 'user_permissions')  # These fields exist on Account
#     list_filter = ('is_staff', 'is_superuser', 'is_active', 'groups')

#     form = UserChangeForm
#     add_form = UserCreationForm
#     change_password_form = AdminPasswordChangeForm

#     fieldsets = (
#         (None, {'fields': ('email', 'password')}),
#         ('Personal Info', {'fields': ('first_name', 'last_name', 'username', 'phone_number')}),
#         ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
#         ('Important dates', {'fields': ('last_login', 'date_joined')}),
#     )

# @admin.register(UserProfile)
# class UserProfileAdmin(ModelAdmin):  # Remove BaseUserAdmin
#     def thumbnail(self, obj):  # Use 'obj' instead of 'object' for clarity
#         if obj.profile_picture:
#             return format_html('<img src="{}" width="30" style="border-radius:50%;">'.format(obj.profile_picture.url))
#         return "No image"
    
#     thumbnail.short_description = 'Profile Picture'
#     list_display = ('thumbnail', 'user', 'city', 'state', 'country')
#     list_display_links = ('user',)
#     list_filter = ('city', 'state', 'country')  # Filter by fields on UserProfile
#     search_fields = ('user__email', 'city', 'state', 'country')  # Search by related Account fields
#     ordering = ('user__email',)  # Order by related Account field
#     fieldsets = (
#         (None, {'fields': ('user', 'profile_picture', 'address_line_1', 'address_line_2', 'city', 'state', 'country')}),
#     )

