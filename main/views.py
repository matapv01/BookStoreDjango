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
    # Lấy tất cả danh mục cha
    base_categories = Category.objects.filter(parent=None).order_by('name')
    
    # Tạo paginator với số lượng category trên mỗi trang
    paginator = Paginator(base_categories, 9) ## 9 danh mục mỗi trang
    
    # Lấy số trang từ request, mặc định là 1
    page_number = request.GET.get('page', 1)
    
    try:
        # Lấy trang hiện tại
        page_obj = paginator.get_page(page_number)
    except (PageNotAnInteger, EmptyPage, ValueError):
        # Nếu có lỗi, lấy trang đầu tiên
        page_obj = paginator.get_page(1)
    
    # Xử lý products cho các category trong trang hiện tại
    for category in page_obj.object_list:
        category.total_products = category.product_set.filter(is_active=True).count()

    # Truyền page_obj vào template thay vì categories
    context = {
        'page_obj': page_obj,  # Đổi tên biến để rõ ràng hơn
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

    # Phân trang
    paginator = Paginator(products, 6)  # 6 sản phẩm mỗi trang
    page = request.GET.get('page')
    products = paginator.get_page(page)

    context = {
        'products': products,
        'search_query': search_query,
        'category_slug': category_slug,
        'sort_by': sort_by,
    }
    context.update(get_base_context())
    return render(request, 'main/product_list.html', context)

def product_detail(request, product_slug):
    product = get_object_or_404(Product, slug=product_slug)
    related_products = Product.objects.filter(category=product.category).exclude(id=product.id)[:4]
    context = {
        'product': product,
        'related_products': related_products,
    }
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
    return render(request, 'main/order_history.html', {'orders': orders})

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
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Mật khẩu đã được thay đổi thành công!')
            return redirect('main:profile')
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'main/change_password.html', {'form': form})

def login_view(request):
    if request.user.is_authenticated:
        return redirect('main:home')
        
    if request.method == 'POST':
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
        form = AuthenticationForm()
    return render(request, 'registration/login.html', {'form': form})

def logout_view(request):
    logout(request)
    messages.success(request, 'Đăng xuất thành công!')
    return redirect('main:home')

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
    return render(request, 'main/register.html', {'form': form})
