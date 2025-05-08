from django.contrib import admin
from .models import Users, Category, Books, Order, OrderItem, Cart, CartBooks

# Register your models here.

from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.http import urlencode

@admin.register(Users)
class UsersAdmin(admin.ModelAdmin):
    model = Users
    list_per_page = 25
    
    list_display = ['name', 'email', 'type', 'status', 'is_staff', 'is_superuser', 'action_buttons']
    list_filter = ['type', 'status', 'is_staff', 'is_superuser']
    search_fields = ['name', 'email']
    ordering = ['email']
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('name',)}),
        ('Permissions', {'fields': ('type', 'status', 'is_staff', 'is_superuser')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'name', 'password1', 'password2'),
        }),
        ('Permissions', {
            'fields': ('type', 'status', 'is_staff', 'is_superuser'),
        }),
    )

    actions = ['reset_password', 'make_active', 'make_inactive', 'make_staff', 'remove_staff']

    def action_buttons(self, obj):
        """Custom action buttons for each user"""
        if not obj.is_superuser:  # Don't show buttons for superusers
            buttons = []
            
            # Reset Password button
            buttons.append(format_html(
                '<a class="button" href="{}?user_id={}">Reset Password</a>',
                reverse('store:admin_reset_user_password'),
                obj.id
            ))
            
            # Change Role button
            buttons.append(format_html(
                '<a class="button" href="{}?user_id={}">Change Role</a>',
                reverse('store:admin_change_user_role'),
                obj.id
            ))

            return format_html('&nbsp;'.join(buttons))
        return ''
    
    action_buttons.short_description = 'Actions'

    def reset_password(self, request, queryset):
        """Reset password to default for selected users"""
        count = 0
        for user in queryset:
            if not user.is_superuser:  # Don't allow resetting superuser passwords
                user.set_password('default123')
                user.save()
                count += 1
        self.message_user(request, f'Reset password for {count} users')
    reset_password.short_description = 'Reset password to default'

    def make_active(self, request, queryset):
        """Make selected users active"""
        queryset.update(status='active')
        self.message_user(request, f'Made {queryset.count()} users active')
    make_active.short_description = 'Mark selected users as active'

    def make_inactive(self, request, queryset):
        """Make selected users inactive"""
        queryset.update(status='inactive')
        self.message_user(request, f'Made {queryset.count()} users inactive')
    make_inactive.short_description = 'Mark selected users as inactive'

    def make_staff(self, request, queryset):
        """Grant staff status to selected users"""
        count = 0
        for user in queryset:
            if not user.is_superuser:
                user.is_staff = True
                user.type = 'admin'
                user.save()
                count += 1
        self.message_user(request, f'Granted staff status to {count} users')
    make_staff.short_description = 'Grant staff status'

    def remove_staff(self, request, queryset):
        """Remove staff status from selected users"""
        queryset.update(is_staff=False, type='user')
        self.message_user(request, f'Removed staff status from {queryset.count()} users')
    remove_staff.short_description = 'Remove staff status'

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'total_books')
    search_fields = ('name',)

@admin.register(Books)
class BooksAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'price', 'stock', 'sold')
    search_fields = ('title', 'category__name')
    list_filter = ('category', 'stock')
    # If you want to select category easily in admin
    raw_id_fields = ('category',)

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('number', 'user', 'total_amount', 'status', 'payment_status')
    search_fields = ('number', 'user__name')
    list_filter = ('status', 'payment_status')
    raw_id_fields = ('user',)

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'book', 'quantity')
    raw_id_fields = ('order', 'book')

@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('user',)
    raw_id_fields = ('user',)

@admin.register(CartBooks)
class CartBooksAdmin(admin.ModelAdmin):
    list_display = ('cart', 'book', 'quantity')
    raw_id_fields = ('cart', 'book')
