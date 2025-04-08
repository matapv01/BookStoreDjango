from django import forms
from django.core.validators import MinValueValidator, MaxValueValidator
from main.models import Product, Category, SystemSettings, UserProfile # Added UserProfile
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserChangeForm

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'category', 'description', 'price', 'discount',
                 'stock', 'image', 'is_active', 'featured']
        widgets = {
            'description': forms.Textarea(attrs={
                'rows': 4,
                'class': 'form-control'
            }),
            'price': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'step': '0.01'
            }),
            'discount': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'max': '100',
                'step': '0.01'
            }),
            'stock': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0'
            }),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'featured': forms.CheckboxInput(attrs={'class': 'form-check-input'})
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

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'description', 'image', 'parent']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={
                'rows': 4,
                'class': 'form-control'
            }),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
            'parent': forms.Select(attrs={'class': 'form-select'})
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            # Exclude self and descendants from parent choices
            self.fields['parent'].queryset = Category.objects.exclude(
                pk__in=[self.instance.pk] +
                list(self.instance.children.values_list('id', flat=True))
            )
        self.fields['parent'].required = False
        self.fields['image'].required = False

class SystemSettingsForm(forms.ModelForm):
    class Meta:
        model = SystemSettings
        fields = ['site_name', 'site_description', 'contact_email',
                 'phone_number', 'address', 'facebook_url', 'twitter_url',
                 'instagram_url', 'maintenance_mode', 'is_active']
        widgets = {
            'site_name': forms.TextInput(attrs={'class': 'form-control'}),
            'site_description': forms.Textarea(attrs={
                'rows': 4,
                'class': 'form-control'
            }),
            'contact_email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={
                'rows': 3,
                'class': 'form-control'
            }),
            'facebook_url': forms.URLInput(attrs={'class': 'form-control'}),
            'twitter_url': forms.URLInput(attrs={'class': 'form-control'}),
            'instagram_url': forms.URLInput(attrs={'class': 'form-control'}),
            'maintenance_mode': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'})
        }

    def clean_contact_email(self):
        email = self.cleaned_data.get('contact_email')
        if not email:
            raise forms.ValidationError("Contact email is required")
        return email

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
        ('PENDING', 'Pending'),
        ('PAID', 'Paid'),
        ('FAILED', 'Failed'),
        ('REFUNDED', 'Refunded')
    ]

    payment_status = forms.ChoiceField(
        choices=PAYMENT_STATUS_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

# Form for editing user details in admin panel
class UserAdminEditForm(forms.ModelForm):
    # Add fields from UserProfile if needed
    phone_number = forms.CharField(label="Phone Number", max_length=20, required=False, widget=forms.TextInput(attrs={'class': 'form-control'})) # Changed 'phone' to 'phone_number' and added label
    address = forms.CharField(widget=forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}), required=False)
    avatar = forms.ImageField(required=False, widget=forms.FileInput(attrs={'class': 'form-control'}))

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'is_active', 'is_staff', 'is_superuser']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_staff': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_superuser': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Populate profile fields if instance exists
        if self.instance and hasattr(self.instance, 'userprofile'):
            profile = self.instance.userprofile
            self.fields['phone_number'].initial = profile.phone_number # Changed 'phone' to 'phone_number'
            self.fields['address'].initial = profile.address
            # Don't set initial for FileField, it's handled differently
            # self.fields['avatar'].initial = profile.avatar
        # Make username readonly if needed
        # self.fields['username'].widget.attrs['readonly'] = True

    def save(self, commit=True):
        user = super().save(commit=False)
        if commit:
            user.save()
            # Save profile fields
            profile, created = UserProfile.objects.get_or_create(user=user)
            profile.phone_number = self.cleaned_data.get('phone_number') # Changed 'phone' to 'phone_number'
            profile.address = self.cleaned_data.get('address')
            # Handle avatar upload carefully
            avatar_file = self.cleaned_data.get('avatar')
            if avatar_file: # Check if a new file was uploaded
                 profile.avatar = avatar_file
            elif avatar_file is False: # Check if clear checkbox was checked (if using ClearableFileInput)
                 profile.avatar = None # Or set to default avatar path
            # If avatar_file is None, it means no change, so don't update profile.avatar

            profile.save()
        return user
