from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Count, Sum
from django.utils import timezone
from datetime import timedelta
# Import the new form
from .forms import ProductForm, CategoryForm, SystemSettingsForm, UserAdminEditForm
from django.contrib.auth.models import User
from main.models import Product, Category, Order, UserProfile
from .models import SystemSettings

def is_admin(user):
    return user.is_authenticated and user.is_staff

def admin_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user and user.is_staff:
            login(request, user)
            return redirect('admin_panel:dashboard')
        messages.error(request, 'Invalid credentials or insufficient permissions')
    return render(request, 'admin/login.html')

@login_required
def admin_logout(request):
    logout(request)
    return redirect('admin_panel:login')

def admin_panel_index(request):
    """Redirects to dashboard if admin, otherwise to login."""
    if is_admin(request.user):
        return redirect('admin_panel:dashboard')
    return redirect('admin_panel:login')

@user_passes_test(is_admin, login_url='admin_panel:login')
def dashboard(request):
    # Get statistics for the dashboard
    today = timezone.now()
    thirty_days_ago = today - timedelta(days=30)

    context = {
        'total_orders': Order.objects.count(),
        'monthly_orders': Order.objects.filter(created_at__gte=thirty_days_ago).count(),
        'total_sales': Order.objects.aggregate(total=Sum('total_amount'))['total'] or 0,
        'monthly_sales': Order.objects.filter(created_at__gte=thirty_days_ago).aggregate(total=Sum('total_amount'))['total'] or 0,
        'total_users': User.objects.count(),
        'admin_users': User.objects.filter(is_staff=True).count(),
        'total_products': Product.objects.count(),
        'recent_orders': Order.objects.select_related('user').order_by('-created_at')[:10],
    }
    # Ensure admin_users is an integer
    context['admin_users'] = context['admin_users'] if isinstance(context['admin_users'], int) else 0
    return render(request, 'admin/dashboard.html', context)

@user_passes_test(is_admin, login_url='admin_panel:login') # Add login_url
def product_list(request):
    products = Product.objects.select_related('category').all()
    return render(request, 'admin/product_list.html', {'products': products})

@user_passes_test(is_admin, login_url='admin_panel:login') # Add login_url
def add_product(request):
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Product added successfully')
            return redirect('admin_panel:products')
    else:
        form = ProductForm()
    return render(request, 'admin/product_form.html', {'form': form, 'title': 'Add Product'})

@user_passes_test(is_admin, login_url='admin_panel:login') # Add login_url
def edit_product(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, 'Product updated successfully')
            return redirect('admin_panel:products')
    else:
        form = ProductForm(instance=product)
    return render(request, 'admin/product_form.html', {'form': form, 'title': 'Edit Product'})

@user_passes_test(is_admin, login_url='admin_panel:login') # Add login_url
def delete_product(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        product.delete()
        messages.success(request, 'Product deleted successfully')
        return redirect('admin_panel:products')
    return render(request, 'admin/delete_confirm.html', {'object': product})

@user_passes_test(is_admin, login_url='admin_panel:login') # Add login_url
def update_product_status(request, pk):
    if request.method == 'POST':
        product = get_object_or_404(Product, pk=pk)
        product.is_active = request.POST.get('is_active') == 'true'
        product.save()
        return JsonResponse({'success': True})
    return JsonResponse({'success': False})

@user_passes_test(is_admin, login_url='admin_panel:login') # Add login_url
def update_product_featured(request, pk):
    if request.method == 'POST':
        product = get_object_or_404(Product, pk=pk)
        product.featured = request.POST.get('featured') == 'true'
        product.save()
        return JsonResponse({'success': True})
    return JsonResponse({'success': False})

@user_passes_test(is_admin, login_url='admin_panel:login') # Add login_url
def category_list(request):
    categories = Category.objects.all()
    return render(request, 'admin/category_list.html', {'categories': categories})

@user_passes_test(is_admin, login_url='admin_panel:login') # Add login_url
def add_category(request):
    if request.method == 'POST':
        form = CategoryForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Category added successfully')
            return redirect('admin_panel:categories')
    else:
        form = CategoryForm()
    return render(request, 'admin/category_form.html', {'form': form, 'title': 'Add Category'})

@user_passes_test(is_admin, login_url='admin_panel:login') # Add login_url
def edit_category(request, pk):
    category = get_object_or_404(Category, pk=pk)
    if request.method == 'POST':
        form = CategoryForm(request.POST, request.FILES, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, 'Category updated successfully')
            return redirect('admin_panel:categories')
    else:
        form = CategoryForm(instance=category)
    return render(request, 'admin/category_form.html', {'form': form, 'title': 'Edit Category'})

@user_passes_test(is_admin, login_url='admin_panel:login') # Add login_url
def delete_category(request, pk):
    category = get_object_or_404(Category, pk=pk)
    if request.method == 'POST':
        category.delete()
        messages.success(request, 'Category deleted successfully')
        return redirect('admin_panel:categories')
    return render(request, 'admin/delete_confirm.html', {'object': category})

@user_passes_test(is_admin, login_url='admin_panel:login') # Add login_url
def order_list(request):
    orders = Order.objects.select_related('user').all()
    return render(request, 'admin/order_list.html', {
        'orders': orders,
        'order_status_choices': Order.STATUS_CHOICES,
    })

@user_passes_test(is_admin, login_url='admin_panel:login') # Add login_url
def order_detail(request, pk):
    order = get_object_or_404(Order.objects.select_related('user'), pk=pk)
    return render(request, 'admin/order_detail.html', {
        'order': order,
        'order_status_choices': Order.STATUS_CHOICES
    })

@user_passes_test(is_admin, login_url='admin_panel:login')
def update_order_status(request, pk):
    order = get_object_or_404(Order, pk=pk)
    if order.status == 'CANCELLED':
        messages.error(request, 'Không thể cập nhật trạng thái đơn hàng đã hủy')
    elif request.method == 'POST':
        status_value = request.POST.get('status')
        
        # Map between display values and status codes if needed
        status_map = {
            'Đang chờ xử lý': 'PENDING',
            'Đang xử lý': 'PROCESSING',
            'Đã giao cho vận chuyển': 'SHIPPED',
            'Đã giao hàng': 'DELIVERED',
            'Đã hủy': 'CANCELLED'
        }
        
        # If the status is a display value, map it to the code
        if status_value in status_map:
            order.status = status_map[status_value]
        else:
            # Otherwise assume it's already a valid code
            order.status = status_value
            
        order.save()
        messages.success(request, 'Cập nhật trạng thái đơn hàng thành công')
        return redirect('admin_panel:order_detail', pk=pk)
    return redirect('admin_panel:orders')

@user_passes_test(is_admin, login_url='admin_panel:login')
def update_payment_status(request, pk):
    order = get_object_or_404(Order, pk=pk)
    if request.method == 'POST':
        payment_status = request.POST.get('payment_status')
        if payment_status in ['Đang chờ thanh toán', 'Đã thanh toán']:
            order.payment_status = payment_status
            order.save()
            messages.success(request, 'Cập nhật trạng thái thanh toán thành công')
        else:
            messages.error(request, 'Trạng thái thanh toán không hợp lệ')
        return redirect('admin_panel:order_detail', pk=pk)
    return redirect('admin_panel:orders')

@user_passes_test(is_admin, login_url='admin_panel:login') # Add login_url
def user_list(request):
    users = User.objects.select_related('userprofile').all()
    return render(request, 'admin/user_list.html', {'users': users})

@user_passes_test(is_admin, login_url='admin_panel:login') # Add login_url
def user_detail(request, pk):
    user = get_object_or_404(User.objects.select_related('userprofile'), pk=pk)
    orders = Order.objects.filter(user=user)
    # The context key should ideally be 'user' to match the template variable
    return render(request, 'admin/user_detail.html', {'user': user, 'user_orders': orders})

@user_passes_test(is_admin, login_url='admin_panel:login')
def user_edit(request, pk):
    user_to_edit = get_object_or_404(User.objects.select_related('userprofile'), pk=pk)
    if request.method == 'POST':
        # Pass request.FILES for avatar upload
        form = UserAdminEditForm(request.POST, request.FILES, instance=user_to_edit)
        if form.is_valid():
            form.save()
            messages.success(request, f"User '{user_to_edit.username}' updated successfully.")
            return redirect('admin_panel:user_detail', pk=pk)
        else:
             messages.error(request, "Please correct the errors below.")
    else:
        form = UserAdminEditForm(instance=user_to_edit)

    context = {
        'form': form,
        'user_obj': user_to_edit # Pass user object to template for context (e.g., title)
    }
    return render(request, 'admin/user_edit.html', context)


@user_passes_test(is_admin, login_url='admin_panel:login') # Add login_url
def toggle_user_status(request, pk):
    if request.method == 'POST':
        user = get_object_or_404(User, pk=pk)
        user.is_active = not user.is_active
        user.save()
        return JsonResponse({'success': True})
    return JsonResponse({'success': False})

@user_passes_test(is_admin, login_url='admin_panel:login') # Add login_url
def system_settings(request):
    settings = SystemSettings.get_settings()
    if request.method == 'POST':
        form = SystemSettingsForm(request.POST, instance=settings)
        if form.is_valid():
            form.save()
            messages.success(request, 'Settings updated successfully')
            return redirect('admin_panel:settings')
    else:
        form = SystemSettingsForm(instance=settings)
    return render(request, 'admin/system_settings.html', {'form': form})

@user_passes_test(is_admin, login_url='admin_panel:login') # Add login_url
def user_profile(request):
    # Get or create user profile
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        # Handle form submission
        request.user.email = request.POST.get('email', '')
        
        # Handle full name
        full_name = request.POST.get('full_name', '').strip()
        name_parts = full_name.split(' ', 1)
        request.user.first_name = name_parts[0] if name_parts else ''
        request.user.last_name = name_parts[1] if len(name_parts) > 1 else ''
        request.user.save()
        
        # Update profile fields
        user_profile.phone_number = request.POST.get('phone', '')
        user_profile.address = request.POST.get('address', '')
        
        # Handle avatar upload
        if 'avatar' in request.FILES:
            user_profile.avatar = request.FILES['avatar']
        
        user_profile.save()
        messages.success(request, 'Profile updated successfully')
        return redirect('admin_panel:profile')
    
    # Prepare context with combined user and profile data
    context = {
        'user': request.user,
        'user_profile': user_profile
    }
    return render(request, 'admin/profile.html', context)
