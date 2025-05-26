from django import forms
from django.core.validators import MinValueValidator, MaxValueValidator
from main.models import Product, Category, UserProfile
from .models import SystemSettings
from main.forms import CategoryForm  # Import CategoryForm từ main/forms.py
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserChangeForm, UserCreationForm as BaseUserCreationForm
import cloudinary.uploader
import re
from django.utils.text import slugify
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class ProductForm(forms.ModelForm):
    image_file = forms.ImageField(
        required=False,
        help_text="Upload hình ảnh sản phẩm (sẽ được lưu trên Cloudinary)",
        widget=forms.FileInput(attrs={'class': 'form-control'})
    )

    class Meta:
        model = Product
        fields = ['name', 'description', 'price', 'discount', 'category', 'stock', 'is_active', 'featured']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'price': forms.NumberInput(attrs={'class': 'form-control'}),
            'discount': forms.NumberInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'stock': forms.NumberInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'featured': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean_price(self):
        price = self.cleaned_data.get('price')
        if price <= 0:
            raise forms.ValidationError("Price must be greater than zero")
        return price

    def clean_discount(self):
        discount = self.cleaned_data.get('discount')
        if discount < 0 or discount > 100:
            raise forms.ValidationError("Discount must be between 0 and 100")
        return discount

    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Nếu có file ảnh mới được upload
        if 'image_file' in self.files:
            try:
                # Tạo public_id hợp lệ từ tên sản phẩm
                # Lấy tên sản phẩm và chuyển thành slug
                name_slug = slugify(instance.name)
                # Loại bỏ các ký tự không hợp lệ, chỉ giữ lại chữ cái, số, dấu gạch ngang và gạch dưới
                valid_public_id = re.sub(r'[^a-z0-9-_]', '', name_slug)
                # Thêm timestamp để đảm bảo tính duy nhất
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                public_id = f"product_{valid_public_id}_{timestamp}"
                
                # Upload lên Cloudinary
                result = cloudinary.uploader.upload(
                    self.files['image_file'],
                    folder="bookstore/products",
                    public_id=public_id,
                    resource_type="image"
                )
                # Lưu URL vào trường image
                instance.image = result['secure_url']
            except Exception as e:
                raise forms.ValidationError(f"Lỗi khi upload ảnh lên Cloudinary: {str(e)}")
        
        if commit:
            instance.save()
        return instance

class SystemSettingsForm(forms.ModelForm):
    WEBSITE_STATUS_CHOICES = [
        ('active', 'Website hoạt động'),
        ('maintenance', 'Chế độ bảo trì'),
    ]
    
    website_status = forms.ChoiceField(
        choices=WEBSITE_STATUS_CHOICES,
        widget=forms.RadioSelect,
        initial='active',
        label='Trạng thái website',
        required=True
    )

    class Meta:
        model = SystemSettings
        fields = ['site_name', 'site_description', 'contact_email', 'phone_number', 'address', 'website_status']
        widgets = {
            'site_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nhập tên website'}),
            'site_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Nhập mô tả website'}),
            'contact_email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Nhập email liên hệ'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nhập số điện thoại'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Nhập địa chỉ'}),
        }
        labels = {
            'site_name': 'Tên website',
            'site_description': 'Mô tả website',
            'contact_email': 'Email liên hệ',
            'phone_number': 'Số điện thoại',
            'address': 'Địa chỉ',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            # Set initial value for website_status based on instance values
            if self.instance.maintenance_mode:
                self.initial['website_status'] = 'maintenance'
            else:
                self.initial['website_status'] = 'active'

    def save(self, commit=True):
        instance = super().save(commit=False)
        # Update maintenance_mode and is_active based on website_status
        status = self.cleaned_data.get('website_status')
        if status == 'maintenance':
            instance.maintenance_mode = True
            instance.is_active = False
        else:  # active
            instance.maintenance_mode = False
            instance.is_active = True
        
        if commit:
            instance.save()
        return instance

class OrderStatusForm(forms.Form):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('PROCESSING', 'Processing'),
        ('SHIPPED', 'Shipped'),
        ('DELIVERED', 'Delivered'),
        ('CANCELLED', 'Cancelled')
    ]

    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

class PaymentStatusForm(forms.Form):
    PAYMENT_STATUS_CHOICES = [
        ('Đang chờ thanh toán', 'Đang chờ thanh toán'),
        ('Đã thanh toán', 'Đã thanh toán'),
    ]

    payment_status = forms.ChoiceField(
        choices=PAYMENT_STATUS_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

# Form for editing user details in admin panel
class UserAdminEditForm(forms.ModelForm):
    username = forms.CharField(label="Tên đăng nhập", required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(label="Email", required=False, widget=forms.EmailInput(attrs={'class': 'form-control'}))
    first_name = forms.CharField(label="Tên", required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(label="Họ", required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    phone_number = forms.CharField(label="Số điện thoại", max_length=20, required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nhập số điện thoại'}))
    address = forms.CharField(label="Địa chỉ", required=False, widget=forms.Textarea(attrs={'rows': 3, 'class': 'form-control', 'placeholder': 'Nhập địa chỉ'}))
    avatar = forms.ImageField(label="Ảnh đại diện", required=False, widget=forms.FileInput(attrs={'class': 'form-control'}))

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'is_active', 'is_staff', 'is_superuser']
        widgets = {
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_staff': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_superuser': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and hasattr(self.instance, 'userprofile'):
            profile = self.instance.userprofile
            self.fields['phone_number'].initial = profile.phone_number
            self.fields['address'].initial = profile.address

    def save(self, commit=True):
        user = super().save(commit=False)
        if commit:
            user.save()
            profile, created = UserProfile.objects.get_or_create(user=user)
            profile.phone_number = self.cleaned_data.get('phone_number')
            profile.address = self.cleaned_data.get('address')
            
            # Xử lý upload avatar lên Cloudinary
            avatar_file = self.cleaned_data.get('avatar')
            if avatar_file:
                try:
                    # Upload ảnh lên Cloudinary
                    result = cloudinary.uploader.upload(
                        avatar_file,
                        folder="avatars",
                        resource_type="image",
                        transformation=[
                            {'width': 400, 'height': 400, 'crop': 'fill'},
                            {'quality': 'auto'},
                            {'fetch_format': 'auto'}
                        ]
                    )
                    # Lưu URL ảnh vào trường avatar
                    profile.avatar = result['secure_url']
                except Exception as e:
                    logger.error(f"Lỗi khi upload avatar: {str(e)}")
                    raise forms.ValidationError(f"Không thể upload avatar: {str(e)}")
            elif avatar_file is False:
                profile.avatar = None
                
            profile.save()
        return user

class UserCreationForm(BaseUserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30, required=False)
    last_name = forms.CharField(max_length=30, required=False)
    phone_number = forms.CharField(max_length=15, required=False)
    is_staff = forms.BooleanField(required=False, initial=False)
    is_active = forms.BooleanField(required=False, initial=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'password1', 'password2', 
                 'is_staff', 'is_active')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.is_staff = self.cleaned_data['is_staff']
        user.is_active = self.cleaned_data['is_active']
        
        if commit:
            user.save()
            # Tạo UserProfile nếu chưa tồn tại
            profile, created = UserProfile.objects.get_or_create(user=user)
            if self.cleaned_data.get('phone_number'):
                profile.phone_number = self.cleaned_data['phone_number']
                profile.save()
        return user

class UserEditForm(forms.ModelForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30, required=False)
    last_name = forms.CharField(max_length=30, required=False)
    phone_number = forms.CharField(max_length=15, required=False)
    is_staff = forms.BooleanField(required=False)
    is_active = forms.BooleanField(required=False)
    is_superuser = forms.BooleanField(required=False)

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'is_active', 'is_superuser')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            try:
                self.fields['phone_number'].initial = self.instance.userprofile.phone_number
            except UserProfile.DoesNotExist:
                pass

    def save(self, commit=True):
        user = super().save(commit=False)
        if commit:
            user.save()
            # Cập nhật UserProfile
            profile, created = UserProfile.objects.get_or_create(user=user)
            if self.cleaned_data.get('phone_number'):
                profile.phone_number = self.cleaned_data['phone_number']
                profile.save()
        return user
