from django.contrib import admin
from django.utils.html import format_html
from .models import Category, Product, UserProfile, Cart, CartItem, Order, OrderItem
from .forms import CategoryForm
import logging

logger = logging.getLogger(__name__)

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    form = CategoryForm
    list_display = ('name', 'display_image', 'parent', 'created_at')
    list_filter = ('parent', 'created_at')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    
    fields = ('name', 'slug', 'description', 'parent', 'image_file')

    class Media:
        css = {
            'all': ('admin/css/category_admin.css',)
        }
        js = ('admin/js/category_admin.js',)

    def display_image(self, obj):
        if obj.image:
            try:
                return format_html(
                    '<div style="display: flex; align-items: center; gap: 10px;">'
                    '<img src="{}" style="width: 50px; height: 50px; object-fit: cover; border-radius: 5px;" />'
                    '<span>{}</span>'
                    '</div>',
                    obj.image,
                    obj.name
                )
            except Exception as e:
                logger.error(f"Lỗi khi hiển thị ảnh cho category {obj.name}: {str(e)}")
                return "Lỗi hiển thị ảnh"
        return "Chưa có ảnh"
    display_image.short_description = 'Ảnh danh mục'

    def save_model(self, request, obj, form, change):
        try:
            logger.info(f"Bắt đầu lưu category: {obj.name}")
            super().save_model(request, obj, form, change)
            logger.info(f"Đã lưu category thành công: {obj.name}")
        except Exception as e:
            logger.error(f"Lỗi khi lưu category {obj.name}: {str(e)}")
            raise

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
