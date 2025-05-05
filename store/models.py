from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.contrib.auth.hashers import make_password, check_password

class UsersManager(BaseUserManager):
    def create_user(self, email, name, password=None):
        if not email:
            raise ValueError('Users must have an email address')
        user = self.model(
            email=self.normalize_email(email),
            name=name,
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, name, password=None):
        user = self.create_user(email, name, password)
        user.type = 'admin'
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user
        
    def create_staff_user(self, email, name, password=None):
        """Create a staff user with admin privileges but not superuser"""
        user = self.create_user(email, name, password)
        user.type = 'admin'
        user.is_staff = True
        user.save(using=self._db)
        return user

class Users(AbstractBaseUser):
    # Django automatically adds an 'id' field as the primary key (AutoField)
    # So the 'id integer(10)' from the ERD is implicitly handled.
    name = models.CharField(max_length=50)
    email = models.EmailField(max_length=50, unique=True)
    type = models.CharField(
        max_length=20, 
        choices=(('admin', 'Admin'), ('user', 'User')), 
        default='user'
    )
    status = models.CharField(
        max_length=20, 
        choices=(('active', 'Active'), ('inactive', 'Inactive')), 
        default='active'
    )
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)

    objects = UsersManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name']

    def __str__(self):
        return self.email

    # Basic properties/methods needed for Django's authentication system
    # if we want to use login/logout functions (even with custom backend)
    def is_active(self):
        return self.status == 'active'

    def has_perm(self, perm, obj=None):
        return self.is_staff or self.is_superuser

    def has_module_perms(self, app_label):
        return self.is_staff or self.is_superuser

    # Required for admin login if not using default User
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
    image_url = models.CharField(max_length=200, blank=True, null=True) # Consider using ImageField or URLField
    stock = models.IntegerField()
    sold = models.IntegerField(default=0)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='books') # Maps Categoryid

    def __str__(self):
        return self.title

class Order(models.Model):
    # id integer(10) - Handled by Django
    # Allow blank/null based on 'N' in ERD
    number = models.CharField(max_length=15, blank=True, null=True)
    # Allow blank/null based on 'N' in ERD
    address = models.CharField(max_length=255, blank=True, null=True)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    # Allow blank/null based on 'N' in ERD
    payment_status = models.CharField(max_length=10, blank=True, null=True)
     # Allow blank/null based on 'N' in ERD
    status = models.CharField(max_length=20, blank=True, null=True)
    user = models.ForeignKey(Users, on_delete=models.CASCADE, related_name='orders') # Maps Usersid

    def __str__(self):
        return f"Order {self.number} by {self.user.name}"

class OrderItem(models.Model):
    # id integer(10) - Handled by Django
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items') # Maps Orderid
    book = models.ForeignKey(Books, on_delete=models.CASCADE) # Maps Booksid
    quantity = models.IntegerField()

    def __str__(self):
        return f"{self.quantity} of {self.book.title} in Order {self.order.number}"

class Cart(models.Model):
    # id integer(10) - Handled by Django
    user = models.ForeignKey(Users, on_delete=models.CASCADE, related_name='carts') # Maps Usersid2
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
