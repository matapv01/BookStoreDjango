from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import login, logout, authenticate, update_session_auth_hash
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Count, Sum
from django.utils import timezone
from datetime import timedelta
from django.db import transaction
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
# Import the new form
from .forms import ProductForm, CategoryForm, SystemSettingsForm, UserAdminEditForm
from django.contrib.auth.models import User
from main.models import Product, Category, Order, UserProfile
from .models import SystemSettings, Notification
from django.contrib.auth.forms import PasswordChangeForm
from django import forms
from django.db.utils import IntegrityError
import cloudinary
import logging
from django.contrib.auth.hashers import make_password
from django.utils.crypto import get_random_string

logger = logging.getLogger(__name__)

def is_admin(user):
    # Cho phép cả staff và superuser truy cập
    return user.is_authenticated and (user.is_staff or user.is_superuser)

def is_superuser(user):
    return user.is_authenticated and user.is_superuser

def admin_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is None:
            messages.error(request, 'Tên đăng nhập hoặc mật khẩu không đúng. Vui lòng thử lại.')
        elif not user.is_staff:
            messages.error(request, 'Tài khoản của bạn không có quyền truy cập vào trang quản trị.')
        else:
            login(request, user)
            next_url = request.GET.get('next', 'admin_panel:dashboard')
            messages.success(request, 'Đăng nhập thành công!')
            return redirect(next_url)
            
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

    # Chỉ tính doanh thu từ các đơn hàng đã hoàn thành (đã giao hàng và đã thanh toán)
    completed_orders = Order.objects.filter(
        status='DELIVERED',
        payment_status='Đã thanh toán'
    )
    
    # Tính tổng doanh thu và doanh thu tháng
    total_sales = completed_orders.aggregate(total=Sum('total_amount'))['total'] or 0
    monthly_sales = completed_orders.filter(
        created_at__gte=thirty_days_ago
    ).aggregate(total=Sum('total_amount'))['total'] or 0

    # Lấy danh sách đơn hàng gần đây (chỉ hiển thị các đơn chưa hoàn thành)
    recent_orders = Order.objects.select_related('user').exclude(
        status='DELIVERED',
        payment_status='Đã thanh toán'
    ).order_by('-created_at')[:10]

    context = {
        'total_orders': Order.objects.count(),
        'monthly_orders': Order.objects.filter(created_at__gte=thirty_days_ago).count(),
        'total_sales': total_sales,
        'monthly_sales': monthly_sales,
        'total_users': User.objects.count(),
        'admin_users': User.objects.filter(is_staff=True).count(),
        'total_products': Product.objects.count(),
        'recent_orders': recent_orders,
    }
    
    # Ensure admin_users is an integer
    context['admin_users'] = context['admin_users'] if isinstance(context['admin_users'], int) else 0
    
    return render(request, 'admin/dashboard.html', context)

@user_passes_test(is_admin, login_url='admin_panel:login') # Add login_url
def product_list(request):
    products = Product.objects.select_related('category').all()
    return render(request, 'admin/product_list.html', {'products': products})

@user_passes_test(is_admin, login_url='admin_panel:login')
def add_product(request):
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, 'Sản phẩm đã được thêm thành công')
                return redirect('admin_panel:products')
            except forms.ValidationError as e:
                messages.error(request, str(e))
            except IntegrityError:
                messages.error(request, 'Sản phẩm này đã tồn tại trong hệ thống. Vui lòng kiểm tra lại tên sản phẩm.')
    else:
        form = ProductForm()
    return render(request, 'admin/product_form.html', {'form': form, 'title': 'Thêm sản phẩm mới'})

@user_passes_test(is_admin, login_url='admin_panel:login')
def edit_product(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, 'Sản phẩm đã được cập nhật thành công')
                return redirect('admin_panel:products')
            except forms.ValidationError as e:
                messages.error(request, str(e))
    else:
        form = ProductForm(instance=product)
    return render(request, 'admin/product_form.html', {'form': form, 'title': 'Sửa sản phẩm'})

@user_passes_test(is_admin, login_url='admin_panel:login') # Add login_url
def delete_product(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        product.delete()
        messages.success(request, 'Product deleted successfully')
        return redirect('admin_panel:products')
    return render(request, 'admin/delete_confirm.html', {'object': product})

@user_passes_test(is_admin, login_url='admin_panel:login')
def update_product_status(request, pk):
    if request.method == 'POST':
        product = get_object_or_404(Product, pk=pk)
        try:
            product.is_active = request.POST.get('is_active') == 'true'
            product.save()
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
    return JsonResponse({'success': False, 'message': 'Invalid request method'})

@user_passes_test(is_admin, login_url='admin_panel:login')
def update_product_featured(request, pk):
    if request.method == 'POST':
        product = get_object_or_404(Product, pk=pk)
        try:
            product.featured = request.POST.get('featured') == 'true'
            product.save()
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
    return JsonResponse({'success': False, 'message': 'Invalid request method'})

@user_passes_test(is_admin, login_url='admin_panel:login') # Add login_url
def category_list(request):
    category_list = Category.objects.all()
    paginator = Paginator(category_list, 10)  # 10 danh mục mỗi trang
    page = request.GET.get('page')
    try:
        categories = paginator.get_page(page)
    except PageNotAnInteger:
        categories = paginator.get_page(1)
    except EmptyPage:
        categories = paginator.get_page(paginator.num_pages)
    return render(request, 'admin/category_list.html', {'categories': categories})

@user_passes_test(is_admin, login_url='admin_panel:login')
def add_category(request):
    if request.method == 'POST':
        form = CategoryForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Danh mục đã được thêm thành công')
            return redirect('admin_panel:categories')
    else:
        form = CategoryForm()
    return render(request, 'admin/category_form.html', {'form': form, 'title': 'Thêm danh mục'})

@user_passes_test(is_admin, login_url='admin_panel:login')
def edit_category(request, pk):
    category = get_object_or_404(Category, pk=pk)
    if request.method == 'POST':
        form = CategoryForm(request.POST, request.FILES, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, 'Danh mục đã được cập nhật thành công')
            return redirect('admin_panel:categories')
    else:
        form = CategoryForm(instance=category)
    return render(request, 'admin/category_form.html', {'form': form, 'title': 'Sửa danh mục'})

@user_passes_test(is_admin, login_url='admin_panel:login')
def delete_category(request, pk):
    category = get_object_or_404(Category, pk=pk)
    if request.method == 'POST':
        category.delete()
        messages.success(request, 'Danh mục đã được xóa thành công')
        return redirect('admin_panel:categories')
    return render(request, 'admin/delete_confirm.html', {'object': category})

@user_passes_test(is_admin, login_url='admin_panel:login') # Add login_url
def order_list(request):
    order_list = Order.objects.select_related('user').all()
    paginator = Paginator(order_list, 10)  # 10 đơn hàng mỗi trang
    page = request.GET.get('page')
    try:
        orders = paginator.get_page(page)
    except PageNotAnInteger:
        orders = paginator.get_page(1)
    except EmptyPage:
        orders = paginator.get_page(paginator.num_pages)
    return render(request, 'admin/order_list.html', {
        'orders': orders,
        'order_status_choices': Order.STATUS_CHOICES,
    })

@user_passes_test(is_admin, login_url='admin_panel:login') # Add login_url
def order_detail(request, pk):
    order = get_object_or_404(
        Order.objects.select_related('user')
                    .prefetch_related('orderitem_set__product'),
        pk=pk
    )
    return render(request, 'admin/order_detail.html', {
        'order': order,
        'order_status_choices': Order.STATUS_CHOICES
    })

@user_passes_test(is_admin, login_url='admin_panel:login')
def update_order_status(request, pk):
    if request.method == 'POST':
        try:
            order = get_object_or_404(Order, pk=pk)
            new_status = request.POST.get('status')
            notes = request.POST.get('notes', '')

            # Validate status
            if not new_status:
                return JsonResponse({
                    'success': False,
                    'message': 'Trạng thái đơn hàng không được để trống'
                }, status=400)

            # Kiểm tra trạng thái hợp lệ
            valid_statuses = [status[0] for status in Order.STATUS_CHOICES]
            if new_status not in valid_statuses:
                return JsonResponse({
                    'success': False,
                    'message': f'Trạng thái đơn hàng không hợp lệ. Các trạng thái hợp lệ: {", ".join(valid_statuses)}'
                }, status=400)

            # Kiểm tra nếu trạng thái không thay đổi
            if new_status == order.status:
                return JsonResponse({
                    'success': False,
                    'message': 'Trạng thái đơn hàng không thay đổi'
                }, status=400)

            # Cập nhật trạng thái
            old_status = order.status
            order.status = new_status
            order.save()

            # Tạo thông báo
            if new_status == 'CANCELLED':
                Notification.create_order_notification(order, 'order_cancelled')
            else:
                Notification.create_order_notification(order, 'order_status')

            # Log thay đổi trạng thái
            logger.info(f'Order {order.id} status changed from {old_status} to {new_status} by {request.user.username}')

            return JsonResponse({
                'success': True,
                'message': 'Cập nhật trạng thái đơn hàng thành công',
                'new_status': new_status,
                'old_status': old_status
            })

        except Exception as e:
            logger.error(f'Error updating order status: {str(e)}')
            return JsonResponse({
                'success': False,
                'message': f'Có lỗi xảy ra khi cập nhật trạng thái: {str(e)}'
            }, status=500)

    return JsonResponse({
        'success': False,
        'message': 'Phương thức không được hỗ trợ'
    }, status=405)

@user_passes_test(is_admin, login_url='admin_panel:login')
def update_payment_status(request, pk):
    if request.method == 'POST':
        try:
            order = get_object_or_404(Order, pk=pk)
            new_status = request.POST.get('payment_status')

            # Validate status
            if not new_status:
                return JsonResponse({
                    'success': False,
                    'message': 'Trạng thái thanh toán không được để trống'
                }, status=400)

            # Kiểm tra trạng thái hợp lệ
            valid_statuses = ['Chưa thanh toán', 'Đã thanh toán', 'Đã hủy']
            if new_status not in valid_statuses:
                return JsonResponse({
                    'success': False,
                    'message': f'Trạng thái thanh toán không hợp lệ. Các trạng thái hợp lệ: {", ".join(valid_statuses)}'
                }, status=400)

            # Kiểm tra nếu trạng thái không thay đổi
            if new_status == order.payment_status:
                return JsonResponse({
                    'success': False,
                    'message': 'Trạng thái thanh toán không thay đổi'
                }, status=400)

            # Cập nhật trạng thái
            old_status = order.payment_status
            order.payment_status = new_status
            order.save()

            # Tạo thông báo
            Notification.create_order_notification(order, 'payment_status')

            # Log thay đổi trạng thái
            logger.info(f'Order {order.id} payment status changed from {old_status} to {new_status} by {request.user.username}')

            return JsonResponse({
                'success': True,
                'message': 'Cập nhật trạng thái thanh toán thành công',
                'new_status': new_status,
                'old_status': old_status
            })

        except Exception as e:
            logger.error(f'Error updating payment status: {str(e)}')
            return JsonResponse({
                'success': False,
                'message': f'Có lỗi xảy ra khi cập nhật trạng thái thanh toán: {str(e)}'
            }, status=500)

    return JsonResponse({
        'success': False,
        'message': 'Phương thức không được hỗ trợ'
    }, status=405)

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
    
    # Kiểm tra quyền chỉnh sửa
    # Staff chỉ có thể chỉnh sửa thông tin của khách hàng
    if not request.user.is_superuser and (user_to_edit.is_staff or user_to_edit.is_superuser):
        messages.error(request, 'Bạn không có quyền chỉnh sửa thông tin của tài khoản này.')
        return redirect('admin_panel:user_detail', pk=pk)
    
    if request.method == 'POST':
        form = UserAdminEditForm(request.POST, request.FILES, instance=user_to_edit)
        if form.is_valid():
            # Kiểm tra lại quyền trước khi lưu
            if not request.user.is_superuser and (user_to_edit.is_staff or user_to_edit.is_superuser):
                messages.error(request, 'Bạn không có quyền chỉnh sửa thông tin của tài khoản này.')
                return redirect('admin_panel:user_detail', pk=pk)
                
            form.save()
            messages.success(request, f"Đã cập nhật thông tin người dùng '{user_to_edit.username}' thành công.")
            return redirect('admin_panel:user_detail', pk=pk)
        else:
            messages.error(request, "Vui lòng sửa các lỗi bên dưới.")
    else:
        form = UserAdminEditForm(instance=user_to_edit)

    context = {
        'form': form,
        'user_obj': user_to_edit
    }
    return render(request, 'admin/user_edit.html', context)

@user_passes_test(is_admin, login_url='admin_panel:login')
def toggle_user_status(request, pk):
    if request.method == 'POST':
        try:
            user = get_object_or_404(User, pk=pk)
            
            # Kiểm tra quyền
            if not request.user.is_superuser and (user.is_staff or user.is_superuser):
                return JsonResponse({
                    'success': False,
                    'message': 'Bạn không có quyền thay đổi trạng thái của tài khoản này.'
                }, status=403)
                
            # Không cho phép tự tắt trạng thái của chính mình
            if user == request.user:
                return JsonResponse({
                    'success': False,
                    'message': 'Bạn không thể tự vô hiệu hóa tài khoản của mình.'
                }, status=403)
                
            # Không cho phép tắt trạng thái của superuser
            if user.is_superuser and not request.user.is_superuser:
                return JsonResponse({
                    'success': False,
                    'message': 'Không thể vô hiệu hóa tài khoản quản trị viên.'
                }, status=403)
                
            user.is_active = not user.is_active
            user.save()
            
            status_text = "kích hoạt" if user.is_active else "vô hiệu hóa"
            return JsonResponse({
                'success': True,
                'message': f'Đã {status_text} tài khoản thành công'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Có lỗi xảy ra: {str(e)}'
            })
    return JsonResponse({'success': False, 'message': 'Invalid request method'})

@user_passes_test(is_superuser, login_url='admin_panel:dashboard')
def system_settings(request):
    # Kiểm tra nếu user là staff nhưng không phải superuser
    if request.user.is_staff and not request.user.is_superuser:
        messages.error(request, 'Chỉ quản trị viên mới có quyền truy cập vào trang cài đặt hệ thống.')
        return redirect('admin_panel:dashboard')
        
    settings = SystemSettings.get_settings()
    if request.method == 'POST':
        form = SystemSettingsForm(request.POST, instance=settings)
        if form.is_valid():
            form.save()
            messages.success(request, 'Đã cập nhật cài đặt hệ thống thành công')
            return redirect('admin_panel:settings')
    else:
        form = SystemSettingsForm(instance=settings)
    return render(request, 'admin/system_settings_form.html', {'form': form})

@user_passes_test(is_admin, login_url='admin_panel:login')
def user_profile(request):
    # Get or create user profile
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Update user information
                user = request.user
                user.email = request.POST.get('email', '').strip()
                
                # Handle full name
                full_name = request.POST.get('full_name', '').strip()
                name_parts = full_name.split(' ', 1)
                user.first_name = name_parts[0] if name_parts else ''
                user.last_name = name_parts[1] if len(name_parts) > 1 else ''
                
                # Update profile fields
                user_profile.phone_number = request.POST.get('phone', '').strip()
                user_profile.address = request.POST.get('address', '').strip()
                
                # Handle avatar upload
                if 'avatar' in request.FILES:
                    try:
                        # Upload ảnh lên Cloudinary
                        result = cloudinary.uploader.upload(
                            request.FILES['avatar'],
                            folder="avatars",
                            resource_type="image",
                            transformation=[
                                {'width': 400, 'height': 400, 'crop': 'fill'},
                                {'quality': 'auto'},
                                {'fetch_format': 'auto'}
                            ]
                        )
                        # Lưu URL ảnh vào trường avatar
                        user_profile.avatar = result['secure_url']
                    except Exception as e:
                        logger.error(f"Lỗi khi upload avatar: {str(e)}")
                        raise forms.ValidationError(f"Không thể upload avatar: {str(e)}")
                
                # Save changes
                user.save()
                user_profile.save()
                
                messages.success(request, 'Thông tin cá nhân đã được cập nhật thành công')
                return redirect('admin_panel:profile')
                
        except Exception as e:
            messages.error(request, f'Có lỗi xảy ra khi cập nhật thông tin: {str(e)}')
    
    # Prepare context with combined user and profile data
    context = {
        'user': request.user,
        'user_profile': user_profile,
        'last_login': request.user.last_login,
        'date_joined': request.user.date_joined
    }
    return render(request, 'admin/profile.html', context)

@login_required
def admin_password_change(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Cập nhật session để không bị logout
            messages.success(request, 'Mật khẩu đã được thay đổi thành công!')
            return redirect('admin_panel:profile')
        else:
            messages.error(request, 'Vui lòng sửa các lỗi bên dưới.')
    else:
        form = PasswordChangeForm(request.user)
    
    return render(request, 'admin/password_change.html', {
        'form': form,
        'title': 'Đổi mật khẩu'
    })

@user_passes_test(is_admin, login_url='admin_panel:login')
def user_delete(request, pk):
    user_to_delete = get_object_or_404(User, pk=pk)
    
    # Kiểm tra quyền xóa ở backend
    if not request.user.is_superuser and (user_to_delete.is_staff or user_to_delete.is_superuser):
        messages.error(request, 'Bạn không có quyền xóa tài khoản của quản trị viên hoặc nhân viên.')
        return redirect('admin_panel:user_detail', pk=pk)
        
    # Không cho phép xóa chính mình
    if user_to_delete == request.user:
        messages.error(request, 'Bạn không thể xóa tài khoản của chính mình.')
        return redirect('admin_panel:user_detail', pk=pk)
    
    if request.method == 'POST':
        username = user_to_delete.username
        user_to_delete.delete()
        messages.success(request, f'Đã xóa tài khoản "{username}" thành công.')
        return redirect('admin_panel:users')
    return redirect('admin_panel:user_detail', pk=pk)

@user_passes_test(is_admin, login_url='admin_panel:login')
def reset_user_password(request, pk):
    if request.method == 'POST':
        user = get_object_or_404(User, pk=pk)
        
        # Kiểm tra quyền reset mật khẩu ở backend
        if not request.user.is_superuser and (user.is_staff or user.is_superuser):
            return JsonResponse({
                'success': False,
                'message': 'Bạn không có quyền reset mật khẩu của quản trị viên hoặc nhân viên.'
            })
            
        # Không cho phép reset mật khẩu của chính mình
        if user == request.user:
            return JsonResponse({
                'success': False,
                'message': 'Bạn không thể reset mật khẩu của chính mình.'
            })
            
        # Tạo mật khẩu ngẫu nhiên 8 ký tự
        new_password = get_random_string(8)
        user.set_password(new_password)
        user.save()
        
        messages.success(request, f'Đã reset mật khẩu của người dùng "{user.username}". Mật khẩu mới: {new_password}')
        return JsonResponse({
            'success': True,
            'message': new_password,
            'username': user.username
        })
        
    return JsonResponse({'success': False, 'message': 'Invalid request method'})

@user_passes_test(is_admin, login_url='admin_panel:login')
def get_notifications(request):
    try:
        notifications = Notification.objects.filter(
            is_read=False
        ).order_by('-created_at')[:10]
        
        notifications_data = [{
            'id': notification.id,
            'message': notification.message,
            'type': notification.get_notification_type_display(),
            'link': notification.link,
            'created_at': notification.created_at.strftime('%H:%M, %d/%m/%Y'),
            'is_read': notification.is_read
        } for notification in notifications]
        
        return JsonResponse({'notifications': notifications_data})
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Có lỗi xảy ra: {str(e)}'
        })

@user_passes_test(is_admin, login_url='admin_panel:login')
def mark_notification_read(request, notification_id):
    if request.method == 'POST':
        try:
            notification = get_object_or_404(Notification, id=notification_id)
            notification.is_read = True
            notification.save()
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Có lỗi xảy ra: {str(e)}'
            })
    return JsonResponse({'success': False, 'message': 'Invalid request method'})

@user_passes_test(is_admin, login_url='admin_panel:login')
def delete_notification(request, notification_id):
    if request.method == 'POST':
        try:
            notification = get_object_or_404(Notification, id=notification_id)
            notification.delete()
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Có lỗi xảy ra: {str(e)}'
            })
    return JsonResponse({'success': False, 'message': 'Invalid request method'})

@user_passes_test(is_admin, login_url='admin_panel:login')
def mark_all_notifications_read(request):
    if request.method == 'POST':
        try:
            Notification.objects.filter(is_read=False).update(is_read=True)
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Có lỗi xảy ra: {str(e)}'
            })
    return JsonResponse({'success': False, 'message': 'Invalid request method'})
