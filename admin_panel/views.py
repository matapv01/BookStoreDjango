from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import login, logout, authenticate, update_session_auth_hash
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Count, Sum, Q
from django.utils import timezone
from datetime import timedelta
from django.db import transaction
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.contrib.auth.models import User
from django.contrib.auth.forms import PasswordChangeForm, UserCreationForm as BaseUserCreationForm
from main.models import Product, Category, Order, UserProfile
from .models import SystemSettings, Notification
from .forms import (
    ProductForm, CategoryForm, SystemSettingsForm, UserAdminEditForm,
    UserCreationForm, UserEditForm
)
import cloudinary
import logging
from django.contrib.auth.hashers import make_password
from django.utils.crypto import get_random_string
from django.db.utils import IntegrityError
import json
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

logger = logging.getLogger(__name__)

def is_admin(user):
    # Cho phép cả staff và superuser truy cập
    return user.is_authenticated and (user.is_staff or user.is_superuser)

def is_superuser(user):
    return user.is_authenticated and user.is_superuser

@csrf_exempt
@require_http_methods(["GET", "POST"])
def admin_login(request):
    # Check if user is already logged in
    if request.user.is_authenticated and (request.user.is_staff or request.user.is_superuser):
        # If it's an API request, return JSON
        if request.headers.get('Accept') == 'application/json' or request.headers.get('Content-Type') == 'application/json':
            return JsonResponse({
                'success': True,
                'message': 'Đã đăng nhập',
                'user': {
                    'id': request.user.id,
                    'username': request.user.username,
                    'email': request.user.email,
                    'is_staff': request.user.is_staff,
                    'is_superuser': request.user.is_superuser
                }
            })
        # If it's a web request, redirect to dashboard
        return redirect('admin_panel:dashboard')

    # Debug logging
    logger.info(f"Request method: {request.method}")
    logger.info(f"Request headers: {dict(request.headers)}")
    logger.info(f"Request body: {request.body}")

    # Check if this is an API request
    is_api_request = (
        request.headers.get('Accept') == 'application/json' or
        request.headers.get('Content-Type') == 'application/json'
    )
    logger.info(f"Is API request: {is_api_request}")

    # If it's an API request, handle it differently
    if is_api_request:
        if request.method == 'GET':
            return JsonResponse({
                'success': False,
                'message': 'Method not allowed'
            }, status=405)

        if request.method == 'POST':
            try:
                data = json.loads(request.body)
                username = data.get('username')
                password = data.get('password')
                logger.info(f"API login attempt for user: {username}")

                if not username or not password:
                    return JsonResponse({
                        'success': False,
                        'message': 'Username và password không được để trống'
                    }, status=400)

                user = authenticate(request, username=username, password=password)
                
                if user is not None:
                    if user.is_staff or user.is_superuser:
                        login(request, user)
                        logger.info(f"Login successful for user: {username}")
                        return JsonResponse({
                            'success': True,
                            'message': 'Đăng nhập thành công',
                            'user': {
                                'id': user.id,
                                'username': user.username,
                                'email': user.email,
                                'is_staff': user.is_staff,
                                'is_superuser': user.is_superuser
                            }
                        })
                    else:
                        logger.warning(f"Unauthorized access attempt for user: {username}")
                        return JsonResponse({
                            'success': False,
                            'message': 'Bạn không có quyền truy cập trang quản trị'
                        }, status=403)
                else:
                    logger.warning(f"Failed login attempt for user: {username}")
                    return JsonResponse({
                        'success': False,
                        'message': 'Tên đăng nhập hoặc mật khẩu không đúng'
                    }, status=401)
            except json.JSONDecodeError:
                logger.error("Invalid JSON data in request body")
                return JsonResponse({
                    'success': False,
                    'message': 'Invalid JSON data'
                }, status=400)

    # Handle web requests
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        logger.info(f"Web login attempt for user: {username}")

        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            if user.is_staff or user.is_superuser:
                login(request, user)
                logger.info(f"Login successful for user: {username}")
                return redirect('admin_panel:dashboard')
            else:
                messages.error(request, 'Bạn không có quyền truy cập trang quản trị')
        else:
            messages.error(request, 'Tên đăng nhập hoặc mật khẩu không đúng')

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
    
    return render(request, 'admin/dashboard_new.html', context)

@csrf_exempt
@user_passes_test(is_admin, login_url='admin_panel:login')
def product_list(request):
    # Lấy các tham số từ request
    search_query = request.GET.get('search', '')
    sort_by = request.GET.get('sort', '-created_at')
    category_id = request.GET.get('category', '')
    page_size = request.GET.get('page_size', '10')
    
    # Khởi tạo queryset
    products = Product.objects.select_related('category').all()
    
    # Áp dụng tìm kiếm
    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) |
            Q(sku__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    
    # Áp dụng lọc theo danh mục
    if category_id:
        products = products.filter(categories__id=category_id)
    
    # Áp dụng sắp xếp
    valid_sort_fields = {
        '-created_at': '-created_at',
        'created_at': 'created_at',
        'name': 'name',
        '-name': '-name',
        'price': 'price',
        '-price': '-price'
    }
    sort_field = valid_sort_fields.get(sort_by, '-created_at')
    products = products.order_by(sort_field)
    
    # Lấy danh sách danh mục cho filter
    categories = Category.objects.all()
    
    # Phân trang
    try:
        page_size = int(page_size)
        if page_size not in [5, 10, 15, 20]:
            page_size = 10
    except ValueError:
        page_size = 10
        
    paginator = Paginator(products, page_size)
    page = request.GET.get('page')
    try:
        products = paginator.get_page(page)
    except PageNotAnInteger:
        products = paginator.get_page(1)
    except EmptyPage:
        products = paginator.get_page(paginator.num_pages)
        
    context = {
        'products': products,
        'categories': categories,
        'search_query': search_query,
        'sort_by': sort_by,
        'category_id': category_id,
        'page_size': page_size
    }
    return render(request, 'admin/product_list.html', context)

@csrf_exempt
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

@csrf_exempt
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

@csrf_exempt
@user_passes_test(is_admin, login_url='admin_panel:login')
def delete_product(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        product.delete()
        messages.success(request, 'Product deleted successfully')
        return redirect('admin_panel:products')
    return render(request, 'admin/delete_confirm.html', {'object': product})

@csrf_exempt
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

@csrf_exempt
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

@login_required
def category_list(request):
    # Get filter parameters
    search_query = request.GET.get('search', '')
    sort_by = request.GET.get('sort', '-created_at')
    page_size = int(request.GET.get('page_size', 10))

    # Base queryset
    categories = Category.objects.all()

    # Apply search filter
    if search_query:
        categories = categories.filter(
            Q(name__icontains=search_query) |
            Q(slug__icontains=search_query)
        )

    # Apply sorting
    categories = categories.order_by(sort_by)

    # Pagination
    paginator = Paginator(categories, page_size)
    page = request.GET.get('page', 1)
    try:
        categories = paginator.page(page)
    except PageNotAnInteger:
        categories = paginator.page(1)
    except EmptyPage:
        categories = paginator.page(paginator.num_pages)

    context = {
        'categories': categories,
        'search_query': search_query,
        'sort_by': sort_by,
        'page_size': page_size,
    }
    return render(request, 'admin/category_list.html', context)

@csrf_exempt
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

@csrf_exempt
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

@csrf_exempt
@user_passes_test(is_admin, login_url='admin_panel:login')
def delete_category(request, pk):
    category = get_object_or_404(Category, pk=pk)
    if request.method == 'POST':
        category.delete()
        messages.success(request, 'Danh mục đã được xóa thành công')
        return redirect('admin_panel:categories')
    return render(request, 'admin/delete_confirm.html', {'object': category})

@csrf_exempt
@user_passes_test(is_admin, login_url='admin_panel:login')
def order_list(request):
    # Lấy các tham số từ request
    search_query = request.GET.get('search', '')
    sort_by = request.GET.get('sort', '-created_at')
    status = request.GET.get('status', '')
    page_size = request.GET.get('page_size', '10')
    
    # Khởi tạo queryset
    orders = Order.objects.select_related('user').all()
    
    # Áp dụng tìm kiếm
    if search_query:
        orders = orders.filter(
            Q(id__icontains=search_query) |
            Q(user__username__icontains=search_query) |
            Q(user__email__icontains=search_query) |
            Q(user__first_name__icontains=search_query) |
            Q(user__last_name__icontains=search_query)
        )
    
    # Áp dụng lọc theo trạng thái
    if status:
        orders = orders.filter(status=status.upper())
    
    # Áp dụng sắp xếp
    valid_sort_fields = {
        '-created_at': '-created_at',
        'created_at': 'created_at',
        'total_amount': 'total_amount',
        '-total_amount': '-total_amount'
    }
    sort_field = valid_sort_fields.get(sort_by, '-created_at')
    orders = orders.order_by(sort_field)
    
    # Phân trang
    try:
        page_size = int(page_size)
        if page_size not in [5, 10, 15, 20]:
            page_size = 10
    except ValueError:
        page_size = 10
        
    paginator = Paginator(orders, page_size)
    page = request.GET.get('page')
    try:
        orders = paginator.get_page(page)
    except PageNotAnInteger:
        orders = paginator.get_page(1)
    except EmptyPage:
        orders = paginator.get_page(paginator.num_pages)
        
    context = {
        'orders': orders,
        'search_query': search_query,
        'sort_by': sort_by,
        'status': status,
        'page_size': page_size,
        'order_status_choices': Order.STATUS_CHOICES
    }
    return render(request, 'admin/order_list.html', context)

@csrf_exempt
@user_passes_test(is_admin, login_url='admin_panel:login')
def order_detail(request, pk):
    order = get_object_or_404(
        Order.objects.select_related('user')
                    .prefetch_related(
                        'orderitem_set',
                        'orderitem_set__product',
                        'orderitem_set__product__category'
                    ),
        pk=pk
    )
    
    # Debug print
    print("\n=== Order Items Debug ===")
    for item in order.orderitem_set.all():
        print(f"\nProduct: {item.product.name}")
        print(f"Image URL: {item.product.image}")
        if item.product.image:
            # Try to fix the URL if it's not a complete Cloudinary URL
            if not item.product.image.startswith('http'):
                fixed_url = f"https://res.cloudinary.com/dqvede4dm/image/upload/{item.product.image}"
                print(f"Fixed URL: {fixed_url}")
                item.product.image = fixed_url
    print("=== End Debug ===\n")
    
    return render(request, 'admin/order_detail.html', {
        'order': order,
        'order_status_choices': Order.STATUS_CHOICES
    })

@csrf_exempt
@user_passes_test(is_admin, login_url='admin_panel:login')
def update_order_status(request, pk):
    if request.method == 'POST':
        try:
            logger.info(f"Updating order status for order {pk}")
            logger.info(f"Request POST data: {request.POST}")
            
            order = get_object_or_404(Order, pk=pk)
            new_status = request.POST.get('status')
            notes = request.POST.get('notes', '')

            logger.info(f"Current order status: {order.status}")
            logger.info(f"New status requested: {new_status}")

            # Validate status
            if not new_status:
                logger.error("Status is empty")
                return JsonResponse({
                    'success': False,
                    'message': 'Trạng thái đơn hàng không được để trống'
                }, status=400)

            # Kiểm tra trạng thái hợp lệ
            valid_statuses = [status[0] for status in Order.STATUS_CHOICES]
            if new_status not in valid_statuses:
                logger.error(f"Invalid status: {new_status}. Valid statuses: {valid_statuses}")
                return JsonResponse({
                    'success': False,
                    'message': f'Trạng thái đơn hàng không hợp lệ. Các trạng thái hợp lệ: {", ".join(valid_statuses)}'
                }, status=400)

            # Kiểm tra nếu trạng thái không thay đổi
            if new_status == order.status:
                logger.info("Status unchanged")
                return JsonResponse({
                    'success': False,
                    'message': 'Trạng thái đơn hàng không thay đổi'
                }, status=400)

            # Cập nhật trạng thái
            old_status = order.status
            order.status = new_status
            
            # Nếu đơn hàng bị hủy, cập nhật trạng thái thanh toán thành "Đang chờ thanh toán"
            if new_status == 'CANCELLED':
                order.payment_status = 'Đang chờ thanh toán'
                message = f'Đã hủy đơn hàng #{order.order_number} thành công'
            else:
                message = 'Cập nhật trạng thái đơn hàng thành công'
            
            order.save()
            logger.info(f"Order status updated from {old_status} to {new_status}")

            # Tạo thông báo
            if new_status == 'CANCELLED':
                Notification.create_order_notification(order, 'order_cancelled')
            else:
                Notification.create_order_notification(order, 'order_status')

            # Kiểm tra nếu là AJAX request
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': message,
                    'new_status': new_status,
                    'old_status': old_status,
                    'payment_status': order.payment_status
                })
            else:
                # Nếu không phải AJAX request, redirect về trang chi tiết đơn hàng
                messages.success(request, message)
                return redirect('admin_panel:order_detail', pk=pk)

        except Exception as e:
            logger.error(f'Error updating order status: {str(e)}')
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'message': f'Có lỗi xảy ra khi cập nhật trạng thái: {str(e)}'
                }, status=500)
            else:
                messages.error(request, f'Có lỗi xảy ra khi cập nhật trạng thái: {str(e)}')
                return redirect('admin_panel:order_detail', pk=pk)

    return JsonResponse({
        'success': False,
        'message': 'Phương thức không được hỗ trợ'
    }, status=405)

@csrf_exempt
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
            valid_statuses = ['Đang chờ thanh toán', 'Đã thanh toán']
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

@csrf_exempt
@user_passes_test(is_admin, login_url='admin_panel:login')
def user_list(request):
    # Lấy các tham số từ request
    search_query = request.GET.get('search', '')
    sort_by = request.GET.get('sort', '-date_joined')
    role = request.GET.get('role', '')
    page_size = request.GET.get('page_size', '10')
    
    # Khởi tạo queryset với select_related để tối ưu query
    users = User.objects.select_related('userprofile').all()
    
    # Áp dụng tìm kiếm
    if search_query:
        users = users.filter(
            Q(username__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(userprofile__phone_number__icontains=search_query)
        ).distinct()
    
    # Áp dụng lọc theo vai trò
    if role:
        if role == 'admin':
            users = users.filter(is_superuser=True)
        elif role == 'staff':
            users = users.filter(is_staff=True, is_superuser=False)
        elif role == 'user':
            users = users.filter(is_staff=False, is_superuser=False)
    
    # Áp dụng sắp xếp
    valid_sort_fields = {
        '-date_joined': '-date_joined',
        'date_joined': 'date_joined',
        'username': 'username',
        '-username': '-username'
    }
    sort_field = valid_sort_fields.get(sort_by, '-date_joined')
    users = users.order_by(sort_field)
    
    # Phân trang
    try:
        page_size = int(page_size)
        if page_size not in [5, 10, 15, 20]:
            page_size = 10
    except ValueError:
        page_size = 10
        
    paginator = Paginator(users, page_size)
    page = request.GET.get('page')
    try:
        users = paginator.get_page(page)
    except PageNotAnInteger:
        users = paginator.get_page(1)
    except EmptyPage:
        users = paginator.get_page(paginator.num_pages)
        
    # Lấy thống kê người dùng
    total_users = User.objects.count()
    admin_users = User.objects.filter(is_superuser=True).count()
    staff_users = User.objects.filter(is_staff=True, is_superuser=False).count()
    regular_users = User.objects.filter(is_staff=False, is_superuser=False).count()
        
    context = {
        'users': users,
        'search_query': search_query,
        'sort_by': sort_by,
        'role': role,
        'page_size': page_size,
        'total_users': total_users,
        'admin_users': admin_users,
        'staff_users': staff_users,
        'regular_users': regular_users
    }
    return render(request, 'admin/user_list.html', context)

@csrf_exempt
@user_passes_test(is_admin, login_url='admin_panel:login')
def user_detail(request, pk):
    user = get_object_or_404(User.objects.select_related('userprofile'), pk=pk)
    orders = Order.objects.filter(user=user)
    # The context key should ideally be 'user' to match the template variable
    return render(request, 'admin/user_detail.html', {'user': user, 'user_orders': orders})

@csrf_exempt
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

@csrf_exempt
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

@csrf_exempt
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
            try:
                # Log the form data for debugging
                logger.info(f"Form data: {form.cleaned_data}")
                
                # Save the form
                instance = form.save()
                
                # Log the saved instance for debugging
                logger.info(f"Saved settings: maintenance_mode={instance.maintenance_mode}, is_active={instance.is_active}")
                
                messages.success(request, 'Đã cập nhật cài đặt hệ thống thành công')
                return redirect('admin_panel:settings')
            except Exception as e:
                logger.error(f"Error saving settings: {str(e)}")
                messages.error(request, f'Có lỗi xảy ra khi lưu cài đặt: {str(e)}')
        else:
            # Log form errors for debugging
            logger.error(f"Form errors: {form.errors}")
            messages.error(request, 'Vui lòng sửa các lỗi bên dưới.')
    else:
        form = SystemSettingsForm(instance=settings)
    
    context = {
        'form': form,
        'settings': settings
    }
    return render(request, 'admin/system_settings_form.html', context)

@csrf_exempt
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

@csrf_exempt
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

@csrf_exempt
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

@csrf_exempt
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
        
        return JsonResponse({
            'success': True,
            'new_password': new_password
        })
        
    return JsonResponse({'success': False, 'message': 'Invalid request method'})

@csrf_exempt
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

@csrf_exempt
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

@csrf_exempt
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

@csrf_exempt
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

@csrf_exempt
@user_passes_test(is_admin, login_url='admin_panel:login')
def add_user(request):
    if request.method == 'POST':
        form = UserAdminEditForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = True
            user.save()
            messages.success(request, 'Thêm người dùng mới thành công!')
            return redirect('admin_panel:users')
    else:
        form = UserAdminEditForm()
    
    context = {
        'form': form,
        'user_obj': None,  # None vì đây là thêm mới
        'title': 'Thêm người dùng mới'
    }
    return render(request, 'admin/user_edit.html', context)

@csrf_exempt
@user_passes_test(is_admin, login_url='admin_panel:login')
def edit_user(request, pk):
    user = get_object_or_404(User.objects.select_related('userprofile'), pk=pk)
    
    # Kiểm tra quyền chỉnh sửa
    if not request.user.is_superuser and (user.is_staff or user.is_superuser):
        messages.error(request, 'Bạn không có quyền chỉnh sửa thông tin của tài khoản này.')
        return redirect('admin_panel:user_detail', pk=pk)
    
    if request.method == 'POST':
        form = UserAdminEditForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Cập nhật thông tin người dùng thành công!')
            return redirect('admin_panel:users')
    else:
        form = UserAdminEditForm(instance=user)
    
    context = {
        'form': form,
        'user_obj': user,
        'title': 'Chỉnh sửa thông tin người dùng'
    }
    return render(request, 'admin/user_edit.html', context)

@csrf_exempt
@user_passes_test(is_admin, login_url='admin_panel:login')
def delete_user(request, pk):
    user = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        if user.is_superuser and not request.user.is_superuser:
            messages.error(request, 'Bạn không có quyền xóa tài khoản quản trị viên!')
        else:
            username = user.username
            user.delete()
            messages.success(request, f'Đã xóa người dùng {username} thành công!')
        return redirect('admin_panel:users')
    return render(request, 'admin/user_confirm_delete.html', {'user': user})
