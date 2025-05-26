from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.utils.html import format_html
from .models import UserProfile, Order, Category
import cloudinary.uploader
import logging

logger = logging.getLogger(__name__)

class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        label='Email',
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Nhập địa chỉ email của bạn'})
    )
    first_name = forms.CharField(
        required=True,
        label='Tên',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nhập tên của bạn'})
    )
    last_name = forms.CharField(
        required=True,
        label='Họ',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nhập họ của bạn'})
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'password1', 'password2')
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nhập tên đăng nhập'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].label = 'Tên đăng nhập'
        self.fields['password1'].label = 'Mật khẩu'
        self.fields['password2'].label = 'Xác nhận mật khẩu'
        
        # Cập nhật help_text cho các trường
        self.fields['username'].help_text = 'Bắt buộc. 150 ký tự hoặc ít hơn. Chỉ bao gồm chữ cái, số và @/./+/-/_'
        self.fields['password1'].help_text = '''
            <ul class="text-muted small">
                <li>Mật khẩu phải có ít nhất 8 ký tự</li>
                <li>Không được quá đơn giản</li>
                <li>Không được chỉ chứa số</li>
                <li>Không được trùng với thông tin cá nhân</li>
            </ul>
        '''
        self.fields['password2'].help_text = 'Nhập lại mật khẩu để xác nhận'

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        
        if commit:
            user.save()
            
        return user

class UserEditForm(forms.ModelForm):
    first_name = forms.CharField(max_length=30, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(max_length=30, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class': 'form-control'}))
    avatar = forms.ImageField(required=False, widget=forms.FileInput(attrs={'class': 'form-control'}))

    class Meta:
        model = UserProfile
        fields = ('avatar',)

    def __init__(self, *args, **kwargs):
        instance = kwargs.get('instance', None)
        super().__init__(*args, **kwargs)
        if instance:
            user = instance.user
            self.fields['first_name'].initial = user.first_name
            self.fields['last_name'].initial = user.last_name
            self.fields['email'].initial = user.email

    def save(self, user, commit=True):
        profile = super().save(commit=False)
        if commit:
            user.first_name = self.cleaned_data['first_name']
            user.last_name = self.cleaned_data['last_name']
            user.email = self.cleaned_data['email']
            user.save()

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

            profile.save()
        return profile

class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ('shipping_address', 'phone_number')
        widgets = {
            'shipping_address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
        }

class CategoryForm(forms.ModelForm):
    image_file = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': 'image/*'
        }),
        help_text='Chọn ảnh để upload (JPG, PNG, GIF)'
    )

    class Meta:
        model = Category
        fields = ['name', 'slug', 'description', 'parent', 'image_file']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'slug': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'parent': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.image:
            self.fields['image_file'].help_text = 'Upload ảnh mới để thay thế ảnh hiện tại'

    def save(self, commit=True):
        try:
            category = super().save(commit=False)
            
            # Xử lý upload ảnh
            image_file = self.cleaned_data.get('image_file')
            if image_file:
                logger.info(f"Bắt đầu upload ảnh cho category: {category.name}")
                try:
                    # Upload ảnh lên Cloudinary
                    result = cloudinary.uploader.upload(
                        image_file,
                        folder="categories",
                        resource_type="image",
                        transformation=[
                            {'width': 800, 'height': 800, 'crop': 'fill'},
                            {'quality': 'auto'},
                            {'fetch_format': 'auto'}
                        ]
                    )
                    logger.info(f"Upload ảnh thành công: {result['secure_url']}")
                    # Lưu URL ảnh vào trường image
                    category.image = result['secure_url']
                except Exception as e:
                    logger.error(f"Lỗi khi upload ảnh: {str(e)}")
                    raise forms.ValidationError(f"Không thể upload ảnh: {str(e)}")
            
            if commit:
                category.save()
                logger.info(f"Đã lưu category: {category.name}")
            return category
        except Exception as e:
            logger.error(f"Lỗi khi lưu category: {str(e)}")
            raise
