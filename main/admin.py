from django.contrib import admin
from django.utils.html import format_html
from .models import Category, Product, UserProfile, Cart, CartItem, Order, OrderItem

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'parent', 'get_image', 'created_at')
    list_filter = ('parent', 'created_at')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    
    def get_image(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="50" height="50" />', obj.image.url)
        return '-'
    get_image.short_description = 'Image'

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'discounted_price', 'category', 'stock', 'is_active', 'featured')
    list_filter = ('category', 'is_active', 'featured', 'created_at')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ('price', 'stock', 'is_active', 'featured')

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone_number', 'get_address', 'created_at')
    search_fields = ('user__username', 'user__email', 'phone_number')
    
    def get_address(self, obj):
        return obj.address[:50] + '...' if len(obj.address) > 50 else obj.address
    get_address.short_description = 'Address'

@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('user', 'get_count', 'get_total', 'created_at')
    search_fields = ('user__username', 'user__email')
    
    def get_count(self, obj):
        return obj.count
    get_count.short_description = 'Items'
    
    def get_total(self, obj):
        return f'${obj.total:.2f}'
    get_total.short_description = 'Total'

@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ('cart', 'product', 'quantity', 'get_total')
    list_filter = ('cart__created_at',)
    search_fields = ('cart__user__username', 'product__name')
    
    def get_total(self, obj):
        return f'${obj.total:.2f}'
    get_total.short_description = 'Total'

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'user', 'total_amount', 'status', 'payment_status', 'created_at')
    list_filter = ('status', 'payment_status', 'payment_method', 'created_at')
    search_fields = ('order_number', 'user__username', 'user__email')
    readonly_fields = ('order_number', 'transaction_id')

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'product', 'quantity', 'price', 'get_total')
    list_filter = ('order__status', 'order__created_at')
    search_fields = ('order__order_number', 'product__name')
    
    def get_total(self, obj):
        return f'${obj.total:.2f}'
    get_total.short_description = 'Total'
