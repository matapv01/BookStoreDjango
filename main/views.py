from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, update_session_auth_hash, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm, AuthenticationForm
from django.contrib import messages
from django.db.models import Q
from django.db import transaction
from .forms import UserRegistrationForm, UserEditForm, OrderForm
from .models import Category, Product, Cart, CartItem, Order, OrderItem, UserProfile
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from admin_panel.models import Notification
from django.http import JsonResponse
from django.contrib.auth.models import User
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
import json
from django.urls import reverse
from django.contrib.auth.decorators import user_passes_test

def get_base_context():
    """Get base context data for all views"""
    return {
        'categories': Category.objects.filter(parent=None).order_by('name'),
    }

def home(request):
    # Bestselling products (featured products)
    bestsellers = Product.objects.filter(featured=True)[:6]
    
    # Latest products
    latest_products = Product.objects.order_by('-created_at')[:8]
    
    # Recommended products (can be customized based on user preferences)
    recommended_products = Product.objects.filter(is_active=True).order_by('?')[:6]
    
    context = {
        'bestsellers': bestsellers,
        'latest_products': latest_products,
        'recommended_products': recommended_products,
    }
    context.update(get_base_context())
    return render(request, 'main/home.html', context)

def category_list(request):
    # Get base categories (parent=None)
    categories = Category.objects.filter(parent=None).order_by('name')
    
    # Handle search
    search_query = request.GET.get('search', '')
    if search_query:
        categories = categories.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    
    # Handle sorting
    sort_by = request.GET.get('sort', 'name')
    if sort_by == 'name':
        categories = categories.order_by('name')
    elif sort_by == '-name':
        categories = categories.order_by('-name')
    elif sort_by == 'created_at':
        categories = categories.order_by('created_at')
    elif sort_by == '-created_at':
        categories = categories.order_by('-created_at')
    
    # Pagination with default values for web (9 items per page)
    page = request.GET.get('page', 1)
    page_size = int(request.GET.get('page_size', 9))  # Default 9 items per page for web
    paginator = Paginator(categories, page_size)
    
    try:
        categories_page = paginator.page(page)
    except (PageNotAnInteger, EmptyPage, ValueError):
        categories_page = paginator.page(1)
    
    # Get total products for each category
    for category in categories_page.object_list:
        category.total_products = category.product_set.filter(is_active=True).count()

    context = {
        'page_obj': categories_page,
        'search_query': search_query,
        'sort_by': sort_by,
        'total': paginator.count,
        'pages': paginator.num_pages,
        'current_page': categories_page.number,
        'page_size': page_size,
        'has_next': categories_page.has_next(),
        'has_previous': categories_page.has_previous(),
        'next_page': categories_page.next_page_number() if categories_page.has_next() else None,
        'previous_page': categories_page.previous_page_number() if categories_page.has_previous() else None
    }
    context.update(get_base_context())
    return render(request, 'main/category_list.html', context)

def category_detail(request, slug):
    category = get_object_or_404(Category, slug=slug)
    products = Product.objects.filter(
        Q(category=category) | Q(category__parent=category),
        is_active=True
    ).distinct().order_by('-created_at')
    
    # Phân trang
    paginator = Paginator(products, 12)  # 12 sản phẩm mỗi trang
    page = request.GET.get('page')
    products = paginator.get_page(page)
    
    subcategories = category.children.all()
    
    context = {
        'category': category,
        'products': products,
        'subcategories': subcategories,
    }
    context.update(get_base_context())
    return render(request, 'main/category_detail.html', context)

def product_list(request):
    products = Product.objects.filter(is_active=True)
    search_query = request.GET.get('q', '')
    category_slug = request.GET.get('category')
    sort_by = request.GET.get('sort')

    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query)
        )

    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)
        products = products.filter(category=category)

    if sort_by == 'price_asc':
        products = products.order_by('price')
    elif sort_by == 'price_desc':
        products = products.order_by('-price')
    elif sort_by == 'name':
        products = products.order_by('name')
    elif sort_by == 'newest':
        products = products.order_by('-created_at')

    # Pagination with default values for web (6 items per page)
    page = request.GET.get('page', 1)
    page_size = int(request.GET.get('page_size', 6))  # Default 6 items per page for web
    paginator = Paginator(products, page_size)
    
    try:
        products_page = paginator.page(page)
    except (PageNotAnInteger, EmptyPage, ValueError):
        products_page = paginator.page(1)

    context = {
        'products': products_page,
        'search_query': search_query,
        'category_slug': category_slug,
        'sort_by': sort_by,
        'total': paginator.count,
        'pages': paginator.num_pages,
        'current_page': products_page.number,
        'page_size': page_size,
        'has_next': products_page.has_next(),
        'has_previous': products_page.has_previous(),
        'next_page': products_page.next_page_number() if products_page.has_next() else None,
        'previous_page': products_page.previous_page_number() if products_page.has_previous() else None
    }
    context.update(get_base_context())
    return render(request, 'main/product_list.html', context)

def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug)
    related_products = Product.objects.filter(category=product.category).exclude(id=product.id)[:4]
    context = {
        'product': product,
        'related_products': related_products,
    }
    context.update(get_base_context())
    return render(request, 'main/product_detail.html', context)

@login_required
def cart(request):
    cart, created = Cart.objects.get_or_create(user=request.user)
    items = CartItem.objects.filter(cart=cart).select_related('product', 'product__category')
    context = {
        'items': items,
        'total': cart.total,
        'cart': cart,
    }
    return render(request, 'main/cart.html', context)

@login_required
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart, created = Cart.objects.get_or_create(user=request.user)
    cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)
    
    if not created:
        cart_item.quantity += 1
        cart_item.save()
        
    messages.success(request, f'Đã thêm {product.name} vào giỏ hàng')
    return redirect('main:cart')

@login_required
def remove_from_cart(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    product_name = cart_item.product.name
    cart_item.delete()
    messages.success(request, f'Đã xóa {product_name} khỏi giỏ hàng')
    return redirect('main:cart')

@login_required
def update_cart(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    
    try:
        quantity = int(request.POST.get('quantity', 1))
        if quantity > 0:
            if quantity <= cart_item.product.stock:
                cart_item.quantity = quantity
                cart_item.save()
                messages.success(request, 'Đã cập nhật số lượng')
            else:
                messages.error(request, 'Số lượng vượt quá hàng tồn kho')
        else:
            cart_item.delete()
            messages.success(request, 'Đã xóa sản phẩm khỏi giỏ hàng')
    except ValueError:
        messages.error(request, 'Số lượng không hợp lệ')
    
    return redirect('main:cart')

@login_required
def checkout(request):
    cart = get_object_or_404(Cart, user=request.user)
    
    if cart.items.count() == 0:
        messages.error(request, 'Giỏ hàng của bạn đang trống')
        return redirect('main:cart')
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Tạo đơn hàng mới với trạng thái mặc định
                order = Order(
                    user=request.user,
                    shipping_address=request.POST.get('shipping_address'),
                    phone_number=request.POST.get('phone_number'),
                    total_amount=cart.total,
                    payment_method=request.POST.get('payment_method', 'CASH'),
                    status='PENDING',  # Trạng thái đơn hàng: Đang chờ xử lý
                    payment_status='Đang chờ thanh toán'  # Trạng thái thanh toán: Đang chờ thanh toán
                )
                order.save()
                
                # Tạo các mục đơn hàng từ giỏ hàng
                for item in cart.items.all():
                    OrderItem.objects.create(
                        order=order,
                        product=item.product,
                        quantity=item.quantity,
                        price=item.product.discounted_price if item.product.discount else item.product.price
                    )
                
                # Tạo thông báo cho admin
                Notification.create_order_notification(order, 'new_order')
                
                # Xóa giỏ hàng
                cart.items.all().delete()
                
                messages.success(request, 'Đặt hàng thành công! Vui lòng chờ xác nhận từ chúng tôi.')
                return redirect('main:order_detail', order_id=order.id)
        except Exception as e:
            messages.error(request, f'Có lỗi xảy ra khi đặt hàng: {str(e)}')
            return redirect('main:cart')
    
    context = {
        'cart': cart,
        'payment_methods': Order.PAYMENT_METHOD_CHOICES,
    }
    return render(request, 'main/checkout.html', context)

@login_required
def order_history(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'main/order_list.html', {'orders': orders})

@login_required
def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'main/order_detail.html', {'order': order})

@login_required
def cancel_order(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    if request.method == 'POST':
        # Chỉ cho phép hủy đơn hàng khi đang ở trạng thái PENDING
        if order.status == 'PENDING':
            try:
                with transaction.atomic():
                    order.status = 'CANCELLED'
                    order.payment_status = 'Đã hủy'
                    order.save()
                    
                    # Tạo thông báo cho admin khi đơn hàng bị hủy
                    Notification.create_order_notification(order, 'order_cancelled')
                    
                    messages.success(request, 'Đơn hàng đã được hủy thành công.')
            except Exception as e:
                messages.error(request, f'Có lỗi xảy ra khi hủy đơn hàng: {str(e)}')
        else:
            messages.error(request, 'Chỉ có thể hủy đơn hàng đang ở trạng thái chờ xử lý.')
    else:
        messages.error(request, 'Yêu cầu không hợp lệ.')
    
    return redirect('main:order_detail', order_id=order.id)

@login_required
def profile(request):
    try:
        profile = request.user.userprofile
    except UserProfile.DoesNotExist:
        profile = UserProfile.objects.create(user=request.user)
    
    orders = Order.objects.filter(user=request.user).order_by('-created_at')[:5]
    
    context = {
        'profile': profile,
        'recent_orders': orders,
    }
    return render(request, 'main/profile.html', context)

@login_required
def profile_edit(request):
    if request.method == 'POST':
        try:
            profile = request.user.userprofile
        except UserProfile.DoesNotExist:
            profile = UserProfile.objects.create(user=request.user)
        form = UserEditForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save(user=request.user)
            messages.success(request, 'Thông tin cá nhân đã được cập nhật')
            return redirect('main:profile')
    else:
        try:
            profile = request.user.userprofile
        except UserProfile.DoesNotExist:
            profile = UserProfile.objects.create(user=request.user)
        form = UserEditForm(instance=profile)
    
    return render(request, 'main/profile_edit.html', {'form': form})

@login_required
def change_password(request):
    if request.method == 'POST':
        # Handle API request with JSON data
        if request.headers.get('Accept') == 'application/json':
            try:
                data = json.loads(request.body)
                form = PasswordChangeForm(request.user, data)
                if form.is_valid():
                    user = form.save()
                    update_session_auth_hash(request, user)
                    return JsonResponse({
                        'success': True,
                        'message': 'Mật khẩu đã được thay đổi thành công!'
                    })
                else:
                    return JsonResponse({
                        'success': False,
                        'message': 'Mật khẩu không hợp lệ',
                        'errors': form.errors
                    }, status=400)
            except json.JSONDecodeError:
                return JsonResponse({
                    'success': False,
                    'message': 'Invalid JSON data'
                }, status=400)
        
        # Handle web form request
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Mật khẩu đã được thay đổi thành công!')
            return redirect('main:profile')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = PasswordChangeForm(request.user)
    
    # For web requests, render the change password template
    if request.headers.get('Accept') != 'application/json':
        return render(request, 'main/change_password.html', {'form': form})
    
    # For API requests without POST data, return method not allowed
    return JsonResponse({
        'success': False,
        'message': 'Method not allowed'
    }, status=405)

def login_view(request):
    if request.user.is_authenticated:
        return redirect('main:home')
        
    if request.method == 'POST':
        # Handle API request with JSON data
        if request.headers.get('Accept') == 'application/json':
            try:
                data = json.loads(request.body)
                username = data.get('username')
                password = data.get('password')
                
                if not username or not password:
                    return JsonResponse({
                        'success': False,
                        'message': 'Username and password are required'
                    }, status=400)
                
                user = authenticate(username=username, password=password)
                if user is not None:
                    login(request, user)
                    return JsonResponse({
                        'success': True,
                        'message': 'Login successful',
                        'token': request.session.session_key,
                        'user': {
                            'id': user.id,
                            'username': user.username,
                            'email': user.email,
                            'first_name': user.first_name,
                            'last_name': user.last_name
                        }
                    })
                else:
                    return JsonResponse({
                        'success': False,
                        'message': 'Invalid username or password'
                    }, status=400)
            except json.JSONDecodeError:
                return JsonResponse({
                    'success': False,
                    'message': 'Invalid JSON data'
                }, status=400)
        
        # Handle web form request
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                next_url = request.GET.get('next', 'main:home')
                messages.success(request, 'Đăng nhập thành công!')
                return redirect(next_url)
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = AuthenticationForm()
    
    # For web requests, render the login template
    if request.headers.get('Accept') != 'application/json':
        return render(request, 'registration/login.html', {'form': form})
    
    # For API requests without POST data, return method not allowed
    return JsonResponse({
        'success': False,
        'message': 'Method not allowed'
    }, status=405)

def logout_view(request):
    if request.user.is_authenticated:
        logout(request)
        if request.headers.get('Accept') == 'application/json':
            return JsonResponse({
                'success': True,
                'message': 'Logout successful'
            })
        messages.success(request, 'Đăng xuất thành công!')
        return redirect('main:home')
    
    if request.headers.get('Accept') == 'application/json':
        return JsonResponse({
            'success': False,
            'message': 'User is not authenticated'
        }, status=401)
    return redirect('main:login')

def register(request):
    if request.user.is_authenticated:
        return redirect('main:home')
        
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    user = form.save()
                    if not hasattr(user, 'userprofile'):
                        UserProfile.objects.create(user=user)
                    login(request, user)
                    messages.success(request, 'Đăng ký thành công!')
                    return redirect('main:home')
            except Exception as e:
                print(f"Registration error: {str(e)}")
                messages.error(request, f'Có lỗi xảy ra khi đăng ký: {str(e)}')
                return redirect('main:register')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = UserRegistrationForm()
    return render(request, 'registration/register.html', {'form': form})

# API Views
@csrf_exempt
@require_http_methods(["GET"])
def api_categories(request):
    # Get base categories (parent=None)
    categories = Category.objects.filter(parent=None).order_by('name')
    
    # Handle search
    search = request.GET.get('search')
    if search:
        categories = categories.filter(
            Q(name__icontains=search) |
            Q(description__icontains=search)
        )
    
    # Handle sorting
    sort = request.GET.get('sort', 'name')
    if sort:
        categories = categories.order_by(sort)
    
    # Pagination with default values for web (9 items per page)
    page = request.GET.get('page', 1)
    page_size = int(request.GET.get('page_size', 9))  # Default 9 items per page for web
    paginator = Paginator(categories, page_size)
    
    try:
        categories_page = paginator.page(page)
    except:
        categories_page = paginator.page(1)
    
    # Get total products for each category
    for category in categories_page.object_list:
        category.total_products = category.product_set.filter(is_active=True).count()
    
    data = [{
        'id': cat.id,
        'name': cat.name,
        'slug': cat.slug,
        'description': cat.description,
        'image': cat.image.url if cat.image else None,  # Use .url for ImageField
        'parent': {
            'id': cat.parent.id,
            'name': cat.parent.name,
            'slug': cat.parent.slug
        } if cat.parent else None,
        'total_products': cat.total_products,
        'created_at': cat.created_at.isoformat(),
        'updated_at': cat.updated_at.isoformat()
    } for cat in categories_page]
    
    return JsonResponse({
        'categories': data,
        'total': paginator.count,
        'pages': paginator.num_pages,
        'current_page': categories_page.number,
        'page_size': page_size,
        'has_next': categories_page.has_next(),
        'has_previous': categories_page.has_previous(),
        'next_page': categories_page.next_page_number() if categories_page.has_next() else None,
        'previous_page': categories_page.previous_page_number() if categories_page.has_previous() else None
    })

@csrf_exempt
@require_http_methods(["GET"])
def api_products(request):
    products = Product.objects.select_related('category').all()
    # Handle filtering
    category = request.GET.get('category')
    if category:
        products = products.filter(category__slug=category)
    
    # Handle search
    search = request.GET.get('search')
    if search:
        products = products.filter(
            Q(name__icontains=search) | 
            Q(description__icontains=search)
        )
    
    # Handle sorting
    sort = request.GET.get('sort', '-created_at')
    if sort:
        products = products.order_by(sort)
    
    # Pagination with default values for web (6 items per page)
    page = request.GET.get('page', 1)
    page_size = int(request.GET.get('page_size', 6))  # Default 6 items per page for web
    paginator = Paginator(products, page_size)
    
    try:
        products_page = paginator.page(page)
    except:
        products_page = paginator.page(1)
    
    data = [{
        'id': p.id,
        'name': p.name,
        'slug': p.slug,
        'description': p.description,
        'price': float(p.price),
        'discounted_price': float(p.discounted_price),
        'category': {
            'id': p.category.id,
            'name': p.category.name,
            'slug': p.category.slug
        } if p.category else None,
        'image': p.image,  # Directly use the URL string
        'is_active': p.is_active,
        'is_featured': p.featured,
        'stock': p.stock,
        'created_at': p.created_at.isoformat()
    } for p in products_page]
    
    return JsonResponse({
        'products': data,
        'total': paginator.count,
        'pages': paginator.num_pages,
        'current_page': products_page.number,
        'page_size': page_size,
        'has_next': products_page.has_next(),
        'has_previous': products_page.has_previous(),
        'next_page': products_page.next_page_number() if products_page.has_next() else None,
        'previous_page': products_page.previous_page_number() if products_page.has_previous() else None
    })

@csrf_exempt
@login_required
@require_http_methods(["GET", "POST"])
def api_cart(request):
    if request.method == 'GET':
        cart, created = Cart.objects.get_or_create(user=request.user)
        items = CartItem.objects.filter(cart=cart).select_related('product').all()
        data = [{
            'id': item.id,
            'product': {
                'id': item.product.id,
                'name': item.product.name,
                'price': float(item.product.price),
                'discounted_price': float(item.product.discounted_price),
                'image': item.product.image  # Directly use the URL string
            },
            'quantity': item.quantity,
            'total': float(item.total)
        } for item in items]
        return JsonResponse({
            'cart': data,
            'total': float(cart.total)
        })
    
    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            product_id = data.get('product_id')
            quantity = int(data.get('quantity', 1))
            
            if not product_id:
                return JsonResponse({
                    'success': False,
                    'message': 'Product ID is required'
                }, status=400)
                
            product = get_object_or_404(Product, id=product_id)
            cart, created = Cart.objects.get_or_create(user=request.user)
            
            # Update or create cart item
            cart_item, created = CartItem.objects.get_or_create(
                cart=cart,
                product=product,
                defaults={'quantity': quantity}
            )
            
            if not created:
                cart_item.quantity += quantity
                cart_item.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Product added to cart',
                'cart_item': {
                    'id': cart_item.id,
                    'product_id': product.id,
                    'quantity': cart_item.quantity,
                    'total': float(cart_item.total)
                }
            })
            
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'message': 'Invalid JSON data'
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            }, status=400)

@csrf_exempt
@login_required
@require_http_methods(["GET", "POST"])
def api_orders(request):
    if request.method == 'GET':
        orders = Order.objects.filter(user=request.user).order_by('-created_at')
        
        # Pagination with default values for admin (10 items per page)
        page = request.GET.get('page', 1)
        page_size = int(request.GET.get('page_size', 10))  # Default 10 items per page for admin
        paginator = Paginator(orders, page_size)
        
        try:
            orders_page = paginator.page(page)
        except:
            orders_page = paginator.page(1)
        
        data = [{
            'id': order.id,
            'total_amount': float(order.total_amount),
            'status': order.status,
            'payment_status': order.payment_status,
            'created_at': order.created_at.isoformat(),
            'items': [{
                'product': {
                    'id': item.product.id,
                    'name': item.product.name,
                    'price': float(item.product.price),
                    'discounted_price': float(item.product.discounted_price),
                    'image': item.product.image  # Directly use the URL string
                },
                'quantity': item.quantity,
                'price': float(item.price),
                'total': float(item.total)
            } for item in order.orderitem_set.select_related('product').all()]
        } for order in orders_page]
        
        return JsonResponse({
            'orders': data,
            'total': paginator.count,
            'pages': paginator.num_pages,
            'current_page': orders_page.number,
            'page_size': page_size,
            'has_next': orders_page.has_next(),
            'has_previous': orders_page.has_previous(),
            'next_page': orders_page.next_page_number() if orders_page.has_next() else None,
            'previous_page': orders_page.previous_page_number() if orders_page.has_previous() else None
        })
    
    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            cart = Cart.objects.get(user=request.user)
            
            if not cart.items.exists():
                return JsonResponse({
                    'success': False,
                    'message': 'Cart is empty'
                }, status=400)
            
            # Create order
            order = Order.objects.create(
                user=request.user,
                total_amount=cart.total,
                shipping_address=data.get('shipping_address', ''),
                payment_method=data.get('payment_method', 'COD')
            )
            
            # Create order items
            for item in cart.items.all():
                OrderItem.objects.create(
                    order=order,
                    product=item.product,
                    quantity=item.quantity,
                    price=item.product.price,
                    total_price=item.total
                )
            
            # Clear cart
            cart.items.all().delete()
            
            return JsonResponse({
                'success': True,
                'message': 'Order created successfully',
                'order': {
                    'id': order.id,
                    'total_amount': float(order.total_amount),
                    'status': order.status,
                    'created_at': order.created_at.isoformat()
                }
            })
            
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'message': 'Invalid JSON data'
            }, status=400)
        except Cart.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Cart not found'
            }, status=404)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            }, status=400)

@csrf_exempt
@login_required
@require_http_methods(["GET", "PUT"])
def api_user_profile(request):
    if request.method == 'GET':
        profile = UserProfile.objects.get_or_create(user=request.user)[0]
        return JsonResponse({
            'user': {
                'id': request.user.id,
                'username': request.user.username,
                'email': request.user.email,
                'first_name': request.user.first_name,
                'last_name': request.user.last_name,
                'date_joined': request.user.date_joined.isoformat()
            },
            'profile': {
                'phone_number': profile.phone_number,
                'address': profile.address,
                'avatar': profile.avatar  # Directly use the URL string
            }
        })
    
    elif request.method == 'PUT':
        try:
            data = json.loads(request.body)
            user = request.user
            profile = UserProfile.objects.get_or_create(user=user)[0]
            
            # Update user fields
            if 'email' in data:
                user.email = data['email']
            if 'first_name' in data:
                user.first_name = data['first_name']
            if 'last_name' in data:
                user.last_name = data['last_name']
            user.save()
            
            # Update profile fields
            if 'phone_number' in data:
                profile.phone_number = data['phone_number']
            if 'address' in data:
                profile.address = data['address']
            profile.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Profile updated successfully'
            })
            
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'message': 'Invalid JSON data'
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            }, status=400)

@require_http_methods(["GET", "POST"])
def admin_login(request):
    if request.method == "POST":
        if request.headers.get('Accept') == 'application/json':
            try:
                data = json.loads(request.body)
                username = data.get('username')
                password = data.get('password')
            except json.JSONDecodeError:
                return JsonResponse({
                    'success': False,
                    'message': 'Invalid JSON data'
                }, status=400)
        else:
            username = request.POST.get('username')
            password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)
        if user is not None and user.is_staff:
            login(request, user)
            if request.headers.get('Accept') == 'application/json':
                return JsonResponse({
                    'success': True,
                    'message': 'Login successful',
                    'user': {
                        'id': user.id,
                        'username': user.username,
                        'email': user.email,
                        'is_staff': user.is_staff
                    }
                })
            return redirect('admin_dashboard')
        else:
            if request.headers.get('Accept') == 'application/json':
                return JsonResponse({
                    'success': False,
                    'message': 'Invalid credentials or insufficient permissions'
                }, status=401)
            messages.error(request, 'Invalid credentials or insufficient permissions')
            return render(request, 'admin/login.html')

    return render(request, 'admin/login.html')

@login_required
@user_passes_test(lambda u: u.is_staff)
def admin_dashboard(request):
    if request.headers.get('Accept') == 'application/json':
        # Get statistics
        total_products = Product.objects.count()
        total_orders = Order.objects.count()
        total_users = User.objects.count()
        total_categories = Category.objects.count()
        
        # Get recent orders
        recent_orders = Order.objects.order_by('-created_at')[:5]
        orders_data = [{
            'id': order.id,
            'user': {
                'id': order.user.id,
                'username': order.user.username
            },
            'total_amount': float(order.total_amount),
            'status': order.status,
            'created_at': order.created_at.isoformat()
        } for order in recent_orders]
        
        return JsonResponse({
            'success': True,
            'data': {
                'statistics': {
                    'total_products': total_products,
                    'total_orders': total_orders,
                    'total_users': total_users,
                    'total_categories': total_categories
                },
                'recent_orders': orders_data
            }
        })
    
    return render(request, 'admin/dashboard.html')

@login_required
@user_passes_test(lambda u: u.is_staff)
def admin_categories(request):
    if request.headers.get('Accept') == 'application/json':
        categories = Category.objects.all()
        
        # Search
        search = request.GET.get('search', '')
        if search:
            categories = categories.filter(
                Q(name__icontains=search) |
                Q(description__icontains=search)
            )
        
        # Sort
        sort = request.GET.get('sort', '-created_at')
        if sort:
            categories = categories.order_by(sort)
        
        # Pagination
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 10))
        paginator = Paginator(categories, page_size)
        
        try:
            categories_page = paginator.page(page)
        except (PageNotAnInteger, EmptyPage):
            categories_page = paginator.page(1)
        
        categories_data = [{
            'id': category.id,
            'name': category.name,
            'slug': category.slug,
            'description': category.description,
            'image': category.image.url if category.image else None,
            'parent': {
                'id': category.parent.id if category.parent else None,
                'name': category.parent.name if category.parent else None,
                'slug': category.parent.slug if category.parent else None
            },
            'total_products': category.products.count(),
            'created_at': category.created_at.isoformat(),
            'updated_at': category.updated_at.isoformat()
        } for category in categories_page]
        
        return JsonResponse({
            'success': True,
            'data': {
                'categories': categories_data,
                'total': paginator.count,
                'pages': paginator.num_pages,
                'current_page': page,
                'page_size': page_size,
                'has_next': categories_page.has_next(),
                'has_previous': categories_page.has_previous(),
                'next_page': categories_page.next_page_number() if categories_page.has_next() else None,
                'previous_page': categories_page.previous_page_number() if categories_page.has_previous() else None
            }
        })
    
    return render(request, 'admin/categories.html')

@login_required
@user_passes_test(lambda u: u.is_staff)
def admin_category_detail(request, category_id):
    try:
        category = Category.objects.get(id=category_id)
    except Category.DoesNotExist:
        if request.headers.get('Accept') == 'application/json':
            return JsonResponse({
                'success': False,
                'message': 'Category not found'
            }, status=404)
        messages.error(request, 'Category not found')
        return redirect('admin_categories')
    
    if request.headers.get('Accept') == 'application/json':
        if request.method == 'GET':
            return JsonResponse({
                'success': True,
                'data': {
                    'id': category.id,
                    'name': category.name,
                    'slug': category.slug,
                    'description': category.description,
                    'image': category.image.url if category.image else None,
                    'parent': {
                        'id': category.parent.id if category.parent else None,
                        'name': category.parent.name if category.parent else None,
                        'slug': category.parent.slug if category.parent else None
                    },
                    'total_products': category.products.count(),
                    'created_at': category.created_at.isoformat(),
                    'updated_at': category.updated_at.isoformat()
                }
            })
        elif request.method == 'PUT':
            try:
                data = json.loads(request.body)
                category.name = data.get('name', category.name)
                category.description = data.get('description', category.description)
                category.save()
                return JsonResponse({
                    'success': True,
                    'message': 'Category updated successfully'
                })
            except json.JSONDecodeError:
                return JsonResponse({
                    'success': False,
                    'message': 'Invalid JSON data'
                }, status=400)
        elif request.method == 'DELETE':
            category.delete()
            return JsonResponse({
                'success': True,
                'message': 'Category deleted successfully'
            })
    
    return render(request, 'admin/category_detail.html', {'category': category})

@login_required
@user_passes_test(lambda u: u.is_staff)
def admin_products(request):
    if request.headers.get('Accept') == 'application/json':
        products = Product.objects.all()
        
        # Filter by category
        category = request.GET.get('category')
        if category:
            products = products.filter(category__slug=category)
        
        # Search
        search = request.GET.get('search', '')
        if search:
            products = products.filter(
                Q(name__icontains=search) |
                Q(description__icontains=search)
            )
        
        # Sort
        sort = request.GET.get('sort', '-created_at')
        if sort:
            products = products.order_by(sort)
        
        # Pagination
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 10))
        paginator = Paginator(products, page_size)
        
        try:
            products_page = paginator.page(page)
        except (PageNotAnInteger, EmptyPage):
            products_page = paginator.page(1)
        
        products_data = [{
            'id': product.id,
            'name': product.name,
            'slug': product.slug,
            'description': product.description,
            'price': float(product.price),
            'discounted_price': float(product.discounted_price) if product.discounted_price else None,
            'category': {
                'id': product.category.id,
                'name': product.category.name,
                'slug': product.category.slug
            },
            'image': product.image,
            'is_active': product.is_active,
            'is_featured': product.is_featured,
            'stock': product.stock,
            'created_at': product.created_at.isoformat()
        } for product in products_page]
        
        return JsonResponse({
            'success': True,
            'data': {
                'products': products_data,
                'total': paginator.count,
                'pages': paginator.num_pages,
                'current_page': page,
                'page_size': page_size,
                'has_next': products_page.has_next(),
                'has_previous': products_page.has_previous(),
                'next_page': products_page.next_page_number() if products_page.has_next() else None,
                'previous_page': products_page.previous_page_number() if products_page.has_previous() else None
            }
        })
    
    return render(request, 'admin/products.html')

@login_required
@user_passes_test(lambda u: u.is_staff)
def admin_product_detail(request, product_id):
    try:
        product = Product.objects.get(id=product_id)
    except Product.DoesNotExist:
        if request.headers.get('Accept') == 'application/json':
            return JsonResponse({
                'success': False,
                'message': 'Product not found'
            }, status=404)
        messages.error(request, 'Product not found')
        return redirect('admin_products')
    
    if request.headers.get('Accept') == 'application/json':
        if request.method == 'GET':
            return JsonResponse({
                'success': True,
                'data': {
                    'id': product.id,
                    'name': product.name,
                    'slug': product.slug,
                    'description': product.description,
                    'price': float(product.price),
                    'discounted_price': float(product.discounted_price) if product.discounted_price else None,
                    'category': {
                        'id': product.category.id,
                        'name': product.category.name,
                        'slug': product.category.slug
                    },
                    'image': product.image,
                    'is_active': product.is_active,
                    'is_featured': product.is_featured,
                    'stock': product.stock,
                    'created_at': product.created_at.isoformat()
                }
            })
        elif request.method == 'PUT':
            try:
                data = json.loads(request.body)
                product.name = data.get('name', product.name)
                product.description = data.get('description', product.description)
                product.price = data.get('price', product.price)
                product.discounted_price = data.get('discounted_price', product.discounted_price)
                product.stock = data.get('stock', product.stock)
                product.is_active = data.get('is_active', product.is_active)
                product.is_featured = data.get('is_featured', product.is_featured)
                product.save()
                return JsonResponse({
                    'success': True,
                    'message': 'Product updated successfully'
                })
            except json.JSONDecodeError:
                return JsonResponse({
                    'success': False,
                    'message': 'Invalid JSON data'
                }, status=400)
        elif request.method == 'DELETE':
            product.delete()
            return JsonResponse({
                'success': True,
                'message': 'Product deleted successfully'
            })
    
    return render(request, 'admin/product_detail.html', {'product': product})

@login_required
@user_passes_test(lambda u: u.is_staff)
def admin_orders(request):
    if request.headers.get('Accept') == 'application/json':
        orders = Order.objects.all()
        
        # Filter by status
        status = request.GET.get('status')
        if status:
            orders = orders.filter(status=status)
        
        # Filter by date range
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        if start_date and end_date:
            orders = orders.filter(created_at__range=[start_date, end_date])
        
        # Sort
        sort = request.GET.get('sort', '-created_at')
        if sort:
            orders = orders.order_by(sort)
        
        # Pagination
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 10))
        paginator = Paginator(orders, page_size)
        
        try:
            orders_page = paginator.page(page)
        except (PageNotAnInteger, EmptyPage):
            orders_page = paginator.page(1)
        
        orders_data = [{
            'id': order.id,
            'user': {
                'id': order.user.id,
                'username': order.user.username,
                'email': order.user.email
            },
            'total_amount': float(order.total_amount),
            'status': order.status,
            'payment_status': order.get_payment_status_display(),
            'shipping_address': order.shipping_address,
            'payment_method': order.payment_method,
            'created_at': order.created_at.isoformat(),
            'items': [{
                'product': {
                    'id': item.product.id,
                    'name': item.product.name,
                    'price': float(item.product.price),
                    'discounted_price': float(item.product.discounted_price) if item.product.discounted_price else None,
                    'image': item.product.image
                },
                'quantity': item.quantity,
                'price': float(item.price),
                'total': float(item.total)
            } for item in order.items.all()]
        } for order in orders_page]
        
        return JsonResponse({
            'success': True,
            'data': {
                'orders': orders_data,
                'total': paginator.count,
                'pages': paginator.num_pages,
                'current_page': page,
                'page_size': page_size,
                'has_next': orders_page.has_next(),
                'has_previous': orders_page.has_previous(),
                'next_page': orders_page.next_page_number() if orders_page.has_next() else None,
                'previous_page': orders_page.previous_page_number() if orders_page.has_previous() else None
            }
        })
    
    return render(request, 'admin/orders.html')

@login_required
@user_passes_test(lambda u: u.is_staff)
def admin_order_detail(request, order_id):
    try:
        order = Order.objects.get(id=order_id)
    except Order.DoesNotExist:
        if request.headers.get('Accept') == 'application/json':
            return JsonResponse({
                'success': False,
                'message': 'Order not found'
            }, status=404)
        messages.error(request, 'Order not found')
        return redirect('admin_orders')
    
    if request.headers.get('Accept') == 'application/json':
        if request.method == 'GET':
            return JsonResponse({
                'success': True,
                'data': {
                    'id': order.id,
                    'user': {
                        'id': order.user.id,
                        'username': order.user.username,
                        'email': order.user.email
                    },
                    'total_amount': float(order.total_amount),
                    'status': order.status,
                    'payment_status': order.get_payment_status_display(),
                    'shipping_address': order.shipping_address,
                    'payment_method': order.payment_method,
                    'created_at': order.created_at.isoformat(),
                    'items': [{
                        'product': {
                            'id': item.product.id,
                            'name': item.product.name,
                            'price': float(item.product.price),
                            'discounted_price': float(item.product.discounted_price) if item.product.discounted_price else None,
                            'image': item.product.image
                        },
                        'quantity': item.quantity,
                        'price': float(item.price),
                        'total': float(item.total)
                    } for item in order.items.all()]
                }
            })
        elif request.method == 'PUT':
            try:
                data = json.loads(request.body)
                order.status = data.get('status', order.status)
                order.payment_status = data.get('payment_status', order.payment_status)
                order.save()
                return JsonResponse({
                    'success': True,
                    'message': 'Order updated successfully'
                })
            except json.JSONDecodeError:
                return JsonResponse({
                    'success': False,
                    'message': 'Invalid JSON data'
                }, status=400)
    
    return render(request, 'admin/order_detail.html', {'order': order})

@login_required
@user_passes_test(lambda u: u.is_staff)
def admin_users(request):
    if request.headers.get('Accept') == 'application/json':
        users = User.objects.all()
        
        # Search
        search = request.GET.get('search', '')
        if search:
            users = users.filter(
                Q(username__icontains=search) |
                Q(email__icontains=search) |
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search)
            )
        
        # Sort
        sort = request.GET.get('sort', '-date_joined')
        if sort:
            users = users.order_by(sort)
        
        # Pagination
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 10))
        paginator = Paginator(users, page_size)
        
        try:
            users_page = paginator.page(page)
        except (PageNotAnInteger, EmptyPage):
            users_page = paginator.page(1)
        
        users_data = [{
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'is_staff': user.is_staff,
            'is_active': user.is_active,
            'date_joined': user.date_joined.isoformat(),
            'last_login': user.last_login.isoformat() if user.last_login else None,
            'profile': {
                'phone_number': user.profile.phone_number,
                'address': user.profile.address,
                'avatar': user.profile.avatar.url if user.profile.avatar else None
            } if hasattr(user, 'profile') else None
        } for user in users_page]
        
        return JsonResponse({
            'success': True,
            'data': {
                'users': users_data,
                'total': paginator.count,
                'pages': paginator.num_pages,
                'current_page': page,
                'page_size': page_size,
                'has_next': users_page.has_next(),
                'has_previous': users_page.has_previous(),
                'next_page': users_page.next_page_number() if users_page.has_next() else None,
                'previous_page': users_page.previous_page_number() if users_page.has_previous() else None
            }
        })
    
    return render(request, 'admin/users.html')

@login_required
@user_passes_test(lambda u: u.is_staff)
def admin_user_detail(request, user_id):
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        if request.headers.get('Accept') == 'application/json':
            return JsonResponse({
                'success': False,
                'message': 'User not found'
            }, status=404)
        messages.error(request, 'User not found')
        return redirect('admin_users')
    
    if request.headers.get('Accept') == 'application/json':
        if request.method == 'GET':
            return JsonResponse({
                'success': True,
                'data': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'is_staff': user.is_staff,
                    'is_active': user.is_active,
                    'date_joined': user.date_joined.isoformat(),
                    'last_login': user.last_login.isoformat() if user.last_login else None,
                    'profile': {
                        'phone_number': user.profile.phone_number,
                        'address': user.profile.address,
                        'avatar': user.profile.avatar.url if user.profile.avatar else None
                    } if hasattr(user, 'profile') else None
                }
            })
        elif request.method == 'PUT':
            try:
                data = json.loads(request.body)
                user.email = data.get('email', user.email)
                user.first_name = data.get('first_name', user.first_name)
                user.last_name = data.get('last_name', user.last_name)
                user.is_active = data.get('is_active', user.is_active)
                user.save()
                
                if hasattr(user, 'profile'):
                    user.profile.phone_number = data.get('phone_number', user.profile.phone_number)
                    user.profile.address = data.get('address', user.profile.address)
                    user.profile.save()
                
                return JsonResponse({
                    'success': True,
                    'message': 'User updated successfully'
                })
            except json.JSONDecodeError:
                return JsonResponse({
                    'success': False,
                    'message': 'Invalid JSON data'
                }, status=400)
        elif request.method == 'DELETE':
            user.delete()
            return JsonResponse({
                'success': True,
                'message': 'User deleted successfully'
            })
    
    return render(request, 'admin/user_detail.html', {'user': user})
