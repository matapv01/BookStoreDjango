from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin 
from django.contrib.auth.hashers import make_password, check_password
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from decimal import Decimal
from django.utils import timezone
import time # Cho việc tạo order number
import uuid
from cloudinary.models import CloudinaryField

# --- ĐỊNH NGHĨA CHOICES Ở CẤP ĐỘ MODULE ---
USER_TYPE_CHOICES = ( # <<< Đặt ở đây
    ('admin', 'Admin'),
    ('user', 'User'),
)

STATUS_CHOICES = ( # <<< Đặt ở đây
    ('active', 'Active'),
    ('inactive', 'Inactive'),
)
# -----------------------------------------

class UsersManager(BaseUserManager):
    def create_user(self, email, name, password=None, **extra_fields): # Thêm **extra_fields
        if not email:
            raise ValueError('Users must have an email address')
        user = self.model(
            email=self.normalize_email(email),
            name=name,
            **extra_fields # Cho phép truyền type, status từ create_superuser/create_staff_user
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, name, password=None):
        # Sử dụng **extra_fields để truyền type và status
        extra_fields = {
            'type': 'admin',      # <<< Sử dụng key trực tiếp
            'status': 'active',   # <<< Sử dụng key trực tiếp
            'is_staff': True,
            'is_superuser': True
        }
        user = self.create_user(email, name, password, **extra_fields)
        # Các trường is_staff, is_superuser đã được set trong extra_fields
        return user

    def create_staff_user(self, email, name, password=None):
        """Create a staff user with admin privileges but not superuser"""
        extra_fields = {
            'type': 'admin',      # <<< Sử dụng key trực tiếp
            'status': 'active',   # <<< Sử dụng key trực tiếp
            'is_staff': True
        }
        user = self.create_user(email, name, password, **extra_fields)
        return user

class Users(AbstractBaseUser):
    name = models.CharField(max_length=50)
    email = models.EmailField(max_length=50, unique=True)

    date_joined = models.DateTimeField(default=timezone.now)
    last_login = models.DateTimeField(blank=True, null=True)

    type = models.CharField(
        max_length=20,
        choices=USER_TYPE_CHOICES, # <<< Tham chiếu đến biến module-level
        default='user'             # <<< Vẫn dùng key trực tiếp cho default
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,   # <<< Tham chiếu đến biến module-level
        default='active'           # <<< Vẫn dùng key trực tiếp cho default
    )
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)

    objects = UsersManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name']

    def __str__(self):
        return self.email

    # --- Sửa đổi phương thức is_active ---
    # Giữ nguyên là phương thức, nhưng sử dụng key trực tiếp để so sánh
    # Hoặc nếu muốn nhất quán, có thể tạo hằng số key ở module-level
    # ví dụ: STATUS_ACTIVE_KEY = 'active'
    def is_active(self):
        return self.status == 'active' # So sánh với key 'active'

    def has_perm(self, perm, obj=None):
        # Giữ nguyên logic này nếu phù hợp
        return (self.status == 'active') and (self.is_staff or self.is_superuser)

    def has_module_perms(self, app_label):
        # Giữ nguyên logic này nếu phù hợp
        return (self.status == 'active') and (self.is_staff or self.is_superuser)

    def get_username(self):
        return self.email

class Category(models.Model):
    # id integer(10) - Handled by Django
    name = models.CharField(max_length=20)
    description = models.CharField(max_length=200, blank=True, null=True) # Assuming N means not mandatory here
    total_books = models.IntegerField(blank=True, null=True) # Assuming N means not mandatory

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Category"
        verbose_name_plural = "Categories"

class Books(models.Model):
    # id integer(10) - Handled by Django
    title = models.CharField(max_length=100)
    description = models.CharField(max_length=256, blank=True, null=True) # Assuming N means not mandatory
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = CloudinaryField(
        'image', # Tên thư mục trên Cloudinary bạn muốn lưu ảnh (tùy chọn)
        null=True,
        blank=True,
        help_text="Hình ảnh sản phẩm sách (tải lên Cloudinary)"
    )
    stock = models.IntegerField()
    sold = models.IntegerField(default=0)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='books') # Maps Categoryid

    def __str__(self):
        return self.title

    # Thêm thuộc tính để dễ dàng lấy URL ảnh (nếu dùng CloudinaryField)
    @property
    def image_public_url(self):
        if self.image and hasattr(self.image, 'url'):
            return self.image.url
        return None # Hoặc một URL placeholder mặc định

class Order(models.Model):
    # Trạng thái Đơn hàng
    PENDING = 'pending'
    PROCESSING = 'processing'
    DELIVERING = 'delivering'
    DELIVERED = 'delivered'
    COMPLETED = 'completed'
    CANCELLED = 'cancelled'
    ORDER_STATUS_CHOICES = [
        (PENDING, 'Chờ duyệt'),
        (PROCESSING, 'Đang xử lý'),
        (DELIVERING, 'Đang giao hàng'),
        (DELIVERED, 'Đã giao hàng'),
        (COMPLETED, 'Đã hoàn thành'),
        (CANCELLED, 'Đã hủy'),
    ]

    # Trạng thái Thanh toán
    UNPAID = 'unpaid'
    PAID = 'paid'
    REFUNDED = 'refunded'
    PAYMENT_STATUS_CHOICES = [
        (UNPAID, 'Chưa thanh toán'),
        (PAID, 'Đã thanh toán'),
        (REFUNDED, 'Đã hoàn tiền'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True, # Cho phép guest checkout nếu muốn, hoặc bỏ blank=True nếu user là bắt buộc
        related_name='orders_placed'
    )
    number = models.CharField(
        max_length=50,
        unique=True,
        blank=True, # Sẽ được tạo trong phương thức save
        help_text="Mã đơn hàng, sẽ được tạo tự động",
        null=True,
        editable=False
    )
    shipping_address = models.TextField(blank=True, null=True) # Địa chỉ giao hàng
    total_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00')
    )
    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default=UNPAID
    )
    status = models.CharField(
        max_length=20,
        choices=ORDER_STATUS_CHOICES,
        default=PENDING
    )
    # Thêm các trường khác nếu cần: payment_method, notes,...
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        user_identifier = self.user.email if self.user else "Guest"
        return f"Order {self.number or self.id} by {user_identifier}"

    def save(self, *args, **kwargs):
        if not self.number:
            # Tạo UUID version 4 (ngẫu nhiên) và lấy phần hex
            self.number = f"ORD-{uuid.uuid4().hex}"
        super().save(*args, **kwargs)

    def calculate_order_total(self):
        """Tính toán lại tổng tiền cho đơn hàng dựa trên các OrderItem."""
        # Đảm bảo self đã có pk
        if not self.pk:
            return self.total_amount # Chưa lưu, chưa có items

        order_total = self.items.aggregate( # Giả sử related_name của OrderItem là 'items'
            total=models.Sum(models.F('quantity') * models.F('price_at_purchase'), output_field=models.DecimalField())
        )['total'] or Decimal('0.00')

        if self.total_amount != order_total:
            self.total_amount = order_total
            self.save(update_fields=['total_amount']) # Chỉ lưu trường total_amount
        return self.total_amount


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE, # Nếu xóa Order, các OrderItem liên quan cũng bị xóa
        related_name='items'      # Dùng 'items' để truy cập các item từ một đối tượng Order: order.items.all()
    )
    book = models.ForeignKey(
        Books,
        on_delete=models.SET_NULL, # Hoặc models.PROTECT tùy logic của bạn
        null=True,                 # Cho phép null nếu sách bị xóa khỏi hệ thống sau khi đơn hàng được tạo
        related_name='order_items'
    )
    quantity = models.PositiveIntegerField(
        default=1,
        help_text="Số lượng sách trong mục đơn hàng này"
    )
    price_at_purchase = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Giá của một cuốn sách tại thời điểm đơn hàng được tạo",
        default=Decimal('0.00')
    )
    # Bạn có thể thêm các trường khác nếu cần, ví dụ:
    # discount_applied = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))

    class Meta:
        # unique_together = ('order', 'book') # Đảm bảo mỗi sách chỉ xuất hiện một lần trong một đơn hàng
        # Dòng trên có thể hữu ích, nhưng nếu bạn muốn cho phép cùng 1 sách được thêm nhiều lần
        # (ví dụ như các dòng khuyến mãi khác nhau cho cùng 1 sách), thì bỏ nó đi.
        # Thông thường, logic nghiệp vụ sẽ gộp số lượng lại.
        ordering = ['id'] # Sắp xếp mặc định (tùy chọn)

    def __str__(self):
        book_title = self.book.title if self.book else "Sách không xác định"
        return f"{self.quantity} x {book_title} (Đơn hàng: {self.order.number or self.order.id})"

    @property
    def item_total(self):
        """Tính tổng tiền cho mục đơn hàng này."""
        return self.price_at_purchase * self.quantity

    def save(self, *args, **kwargs):
        # Tự động gán price_at_purchase khi một OrderItem mới được tạo
        # và chưa có giá trị price_at_purchase được gán thủ công
        if not self.pk and self.book and not hasattr(self, '_price_at_purchase_already_set'):
            self.price_at_purchase = self.book.price
            # Đánh dấu để tránh ghi đè nếu giá được set từ bên ngoài trước khi save
            self._price_at_purchase_already_set = True
        super().save(*args, **kwargs)

class Cart(models.Model):
    # id integer(10) - Handled by Django
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='cart' # Đổi tên related_name thành số ít 'cart'
    )
    books = models.ManyToManyField(Books, through='CartBooks') # Defines the M2M relationship

    def __str__(self):
        return f"Cart for {self.user.name}"

class CartBooks(models.Model):
    # This is the intermediate model for the Cart-Books ManyToMany relationship
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE) # Maps Cartid
    book = models.ForeignKey(Books, on_delete=models.CASCADE) # Maps Booksid
    quantity = models.IntegerField()

    class Meta:
        unique_together = ('cart', 'book') # Ensure a book appears only once per cart directly

    def __str__(self):
        return f"{self.quantity} of {self.book.title} in Cart {self.cart.id}"
