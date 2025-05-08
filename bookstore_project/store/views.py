from django.shortcuts import redirect # Keep for potential admin redirects if needed, but API views won't use it
from .decorators import token_required, staff_token_required # <<< ĐẢM BẢO DÒNG NÀY TỒN TẠI VÀ ĐÚNG
from django.contrib.auth import authenticate, login, logout
# from django.contrib import messages # messages are generally for template rendering, not APIs
from django.urls import reverse # Might not be needed if not generating URLs within responses
from .models import Category, Books, Users, Order, OrderItem
from .forms import UserRegistrationForm, LoginForm
from django.http import JsonResponse, HttpResponseNotAllowed, HttpResponse # <<< THÊM DÒNG NÀY
from django.views.decorators.csrf import csrf_exempt # Import csrf_exempt
from django.core.exceptions import ObjectDoesNotExist # More specific exception handling
from decimal import Decimal # To handle potential Decimal serialization
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
import random
from django.shortcuts import render, get_object_or_404
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from django.db import transaction, models 
from django.db import transaction, models, IntegrityError 
from django.contrib.auth.forms import PasswordChangeForm
from django.db.models import Q, F, Sum 
import traceback
from django.conf import settings
import string, json
from .models import (
    Users, USER_TYPE_CHOICES, STATUS_CHOICES,
    Category,
    Books,
    Cart,         # <<< THÊM CART VÀO ĐÂY
    CartBooks,    # <<< THÊM CARTBOOKS VÀO ĐÂY
    Order,        # Import cả Order và OrderItem nếu các view checkout dùng đến
    OrderItem
)

# Helper to format Decimal to string for JSON
def format_decimal(d):
    return "{:.2f}".format(d) if isinstance(d, Decimal) else d

def format_book_data(book_instance):
    """
    Hàm helper để định dạng dữ liệu của một đối tượng Books thành dictionary,
    bao gồm cả URL hình ảnh từ Cloudinary.
    """
    if not book_instance:
        return None

    return {
        'id': book_instance.id,
        'title': book_instance.title,
        'description': getattr(book_instance, 'description', None),
        'price': format_decimal(book_instance.price),
        'stock': book_instance.stock,
        'category_id': book_instance.category_id, # Giả sử category là ForeignKey trực tiếp
        'category_name': book_instance.category.name if book_instance.category else None,
        'sold': getattr(book_instance, 'sold', 0),
        'image_url': book_instance.image_public_url # <<< SỬ DỤNG PROPERTY TỪ MODEL BOOKS
    }

# --- Public Browsing Views ---

@csrf_exempt # Thường không cần cho GET
def best_selling_books_list(request):
    """
    API: Lấy danh sách các sách bán chạy nhất, có phân trang.
    Sắp xếp theo số lượng đã bán (trường 'sold') giảm dần.
    Query parameters:
        - page: Số trang muốn lấy (mặc định: 1)
        - page_size: Số lượng sách mỗi trang (mặc định: 10, max: 50)
    """
    if request.method == 'GET':
        try:
            # --- Lấy tham số phân trang ---
            try:
                page = int(request.GET.get('page', 1))
            except ValueError:
                page = 1 # Mặc định về trang 1 nếu 'page' không hợp lệ

            try:
                page_size = min(int(request.GET.get('page_size', 10)), 50) # Mặc định 10, max 50
                if page_size <= 0:
                    page_size = 10 # Đảm bảo page_size dương
            except ValueError:
                page_size = 10 # Mặc định về 10 nếu 'page_size' không hợp lệ

            # --- Query sách bán chạy nhất ---
            # Đảm bảo model Books có trường 'sold'
            if not hasattr(Books, 'sold'):
                return JsonResponse({
                    'error': "Feature not available: Book model does not have a 'sold' field."
                }, status=501) # 501 Not Implemented

            # Chỉ lấy sách còn hàng và có số lượng bán > 0 (tùy chọn)
            # Sắp xếp theo 'sold' giảm dần, sau đó theo 'id' để đảm bảo thứ tự ổn định nếu 'sold' bằng nhau
            books_query = Books.objects.select_related('category').filter(
                stock__gt=0,
                # sold__gt=0 # Bỏ comment nếu chỉ muốn hiển thị sách đã bán được ít nhất 1 cuốn
            ).order_by('-sold', '-id')


            # --- Áp dụng phân trang ---
            paginator = Paginator(books_query, page_size)
            try:
                books_page = paginator.page(page)
            except PageNotAnInteger:
                books_page = paginator.page(1)
                page = 1
            except EmptyPage:
                books_page = paginator.page(paginator.num_pages)
                page = paginator.num_pages

            # --- Chuẩn bị dữ liệu sách cho trang hiện tại ---
            books_data = [format_book_data(book) for book in books_page.object_list]

            # --- Tạo response JSON với thông tin phân trang ---
            data = {
                'count': paginator.count,
                'num_pages': paginator.num_pages,
                'current_page': page,
                'page_size': page_size,
                'next_page': books_page.next_page_number() if books_page.has_next() else None,
                'previous_page': books_page.previous_page_number() if books_page.has_previous() else None,
                'results': books_data
            }
            return JsonResponse(data)

        except Exception as e:
            print(f"Best Selling Books API Error: {e}")
            import traceback
            traceback.print_exc()
            return JsonResponse({'error': 'Could not retrieve best selling books list.'}, status=500)
    else:
        return JsonResponse({'error': 'Method not allowed, please use GET'}, status=405)


@csrf_exempt
def book_list(request, category_slug=None):
    """
    API danh sách sách: hỗ trợ lọc theo category và phân trang.
    Query parameters:
        - page: Số trang muốn lấy (mặc định: 1)
        - page_size: Số lượng sách mỗi trang (mặc định: 10)
    """
    if request.method == 'GET':
        try:
            # --- Lấy tham số phân trang ---
            try:
                page = int(request.GET.get('page', 1))
            except ValueError:
                page = 1
            try:
                # Cho phép client tùy chỉnh page_size, nhưng giới hạn max để tránh quá tải
                page_size = min(int(request.GET.get('page_size', 10)), 50) # Giới hạn max 50 item/trang
                if page_size <= 0:
                     page_size = 10
            except ValueError:
                page_size = 10

            # --- Query sách ---
            books_query = Books.objects.select_related('category').filter(stock__gt=0).order_by('-id') # Sắp xếp mặc định

            current_category = None
            if category_slug:
                category = get_object_or_404(Category, name=category_slug)
                books_query = books_query.filter(category=category)
                current_category = {'id': category.id, 'name': category.name}

            # --- Áp dụng phân trang ---
            paginator = Paginator(books_query, page_size)
            try:
                books_page = paginator.page(page)
            except PageNotAnInteger:
                # Nếu page không phải số nguyên, trả về trang đầu tiên.
                books_page = paginator.page(1)
                page = 1 # Cập nhật lại số trang hiện tại
            except EmptyPage:
                # Nếu page vượt quá tổng số trang, trả về trang cuối cùng.
                books_page = paginator.page(paginator.num_pages)
                page = paginator.num_pages # Cập nhật lại số trang hiện tại

            # --- Chuẩn bị dữ liệu sách cho trang hiện tại ---
            books_data = [format_book_data(book) for book in books_page.object_list]

            # --- Tạo response JSON với thông tin phân trang ---
            data = {
                'count': paginator.count, # Tổng số sách
                'num_pages': paginator.num_pages, # Tổng số trang
                'current_page': page, # Trang hiện tại
                'page_size': page_size, # Số lượng item mỗi trang
                'next_page': books_page.next_page_number() if books_page.has_next() else None,
                'previous_page': books_page.previous_page_number() if books_page.has_previous() else None,
                'category_filter': current_category, # Thông tin category đang lọc (nếu có)
                'results': books_data # Danh sách sách của trang hiện tại
            }
            return JsonResponse(data)

        except Category.DoesNotExist:
             return JsonResponse({'error': f'Category "{category_slug}" not found'}, status=404)
        except Exception as e:
            print(f"Book List API Error: {e}")
            return JsonResponse({'error': 'Could not retrieve book list.'}, status=500)
    else:
        return JsonResponse({'error': 'Method not allowed, please use GET'}, status=405)

@csrf_exempt
def book_detail(request, pk):
    if request.method == 'GET':
        try:
            book = get_object_or_404(Books.objects.select_related('category'), pk=pk)

            # Lấy sách liên quan và format
            related_books_query = Books.objects.select_related('category') \
                                 .filter(category=book.category, stock__gt=0) \
                                 .exclude(pk=pk).order_by('?')[:4] # Lấy ngẫu nhiên
            related_books_data = [format_book_data(rb) for rb in related_books_query]

            # Format sách chính
            main_book_data = format_book_data(book) # <<< SỬ DỤNG HELPER
            if not main_book_data:
                return JsonResponse({'error': 'Book data could not be formatted.'}, status=500)

            main_book_data['related_books'] = related_books_data # Thêm sách liên quan vào dict của sách chính

            # Trả về trực tiếp dictionary của sách chính (đã bao gồm related_books)
            return JsonResponse(main_book_data)
        except Exception as e:
            print(f"Book Detail API Error: {e}")
            import traceback; traceback.print_exc()
            return JsonResponse({'error': 'Could not retrieve book details.'}, status=500)
    else:
        return JsonResponse({'error': 'Method not allowed, please use GET'}, status=405)

@csrf_exempt
def search_books(request):
    """
    API: Tìm kiếm sách theo tên (q) VÀ/HOẶC lọc theo category (category_id).
    Không yêu cầu token. Hỗ trợ phân trang.
    Query parameters:
        - q: Chuỗi tìm kiếm tên sách (tùy chọn nếu có category).
        - category: ID của category để lọc (tùy chọn).
        - page: Số trang (mặc định 1).
        - page_size: Số lượng kết quả mỗi trang (mặc định 10, max 50).
    """
    if request.method == 'GET':
        # 1. Lấy tham số từ query string
        search_query_term = request.GET.get('q', '').strip()
        category_id_str = request.GET.get('category', None) # Lấy category ID (là chuỗi)

        # --- Kiểm tra xem có ít nhất một tiêu chí lọc/tìm kiếm không ---
        if not search_query_term and not category_id_str:
            return JsonResponse({'error': 'At least one filter parameter (q or category) is required.'}, status=400)

        # 2. Lấy tham số phân trang
        try: page = int(request.GET.get('page', 1))
        except ValueError: page = 1
        try:
            page_size = min(int(request.GET.get('page_size', 10)), 50)
            if page_size <= 0: page_size = 10
        except ValueError: page_size = 10

        try:
            # 3. Xây dựng query tìm kiếm/lọc
            # Bắt đầu với tất cả sách còn hàng
            books_query = Books.objects.select_related('category').filter(stock__gt=0)
            category_filter_applied = None
            if category_id_str:
                try:
                    category_id = int(category_id_str)
                    category_filter_applied = get_object_or_404(Category, id=category_id)
                    books_query = books_query.filter(category_id=category_id)
                except ValueError: return JsonResponse({'error': 'Invalid category ID format.'}, status=400)
                except Category.DoesNotExist: return JsonResponse({'error': f'Category with ID {category_id_str} not found.'}, status=404)
            if search_query_term:
                books_query = books_query.filter(title__icontains=search_query_term)
            books_query = books_query.order_by('-id')

            # Sắp xếp kết quả
            books_query = books_query.order_by('-id') # Hoặc tiêu chí khác

            # 4. Áp dụng phân trang
            paginator = Paginator(books_query, page_size)
            try: books_page = paginator.page(page)
            except PageNotAnInteger: books_page = paginator.page(1); page = 1
            except EmptyPage:
                if paginator.num_pages > 0: books_page = paginator.page(paginator.num_pages); page = paginator.num_pages
                else: books_page = paginator.page(1); page = 1

            # 5. Chuẩn bị dữ liệu kết quả
            books_data = [format_book_data(book) for book in books_page.object_list]


            # 6. Tạo response JSON
            data = {
                'search_query': search_query_term if search_query_term else None,
                'category_filter': { # Thông tin category đã lọc (nếu có)
                     'id': category_filter_applied.id,
                     'name': category_filter_applied.name
                } if category_filter_applied else None,
                'count': paginator.count,
                'num_pages': paginator.num_pages,
                'current_page': page,
                'page_size': page_size,
                'next_page': books_page.next_page_number() if books_page.has_next() else None,
                'previous_page': books_page.previous_page_number() if books_page.has_previous() else None,
                'results': books_data
            }
            return JsonResponse(data)

        # Xử lý lỗi chung (trừ lỗi Category.DoesNotExist đã xử lý ở trên)
        except Exception as e:
            print(f"Search Books API Error: {e}")
            import traceback; traceback.print_exc()
            return JsonResponse({'error': 'Could not perform book search.'}, status=500)
    else:
        return JsonResponse({'error': 'Method not allowed, please use GET'}, status=405)

@csrf_exempt # Thường không cần cho GET
def category_list(request):
    """
    API danh sách categories: trả về tất cả các category, có hỗ trợ phân trang.
    Không yêu cầu token.
    Query parameters:
        - page: Số trang muốn lấy (mặc định: 1)
        - page_size: Số lượng category mỗi trang (mặc định: 10, max: 50)
    """
    if request.method == 'GET':
        try:
            # --- Lấy tham số phân trang ---
            try:
                page = int(request.GET.get('page', 1))
            except ValueError:
                page = 1 # Mặc định về trang 1 nếu 'page' không hợp lệ

            try:
                # Cho phép client tùy chỉnh page_size, nhưng giới hạn max
                page_size = min(int(request.GET.get('page_size', 10)), 50) # Mặc định 10, max 50
                if page_size <= 0:
                    page_size = 10 # Đảm bảo page_size dương
            except ValueError:
                page_size = 10 # Mặc định về 10 nếu 'page_size' không hợp lệ

            # --- Query categories ---
            # .order_by('name') để sắp xếp theo tên (tùy chọn, nhưng tốt cho phân trang ổn định)
            categories_query = Category.objects.all().order_by('name')

            # --- Áp dụng phân trang ---
            paginator = Paginator(categories_query, page_size)
            try:
                categories_page = paginator.page(page)
            except PageNotAnInteger:
                # Nếu page không phải số nguyên, trả về trang đầu tiên.
                categories_page = paginator.page(1)
                page = 1 # Cập nhật lại số trang hiện tại
            except EmptyPage:
                # Nếu page vượt quá tổng số trang, trả về trang cuối cùng.
                categories_page = paginator.page(paginator.num_pages)
                page = paginator.num_pages # Cập nhật lại số trang hiện tại

            # --- Chuẩn bị dữ liệu category cho trang hiện tại ---
            # Lấy các trường cần thiết, ví dụ: 'id', 'name'
            # Nếu model Category có các trường khác bạn muốn hiển thị (ví dụ: description, total_books),
            # hãy thêm chúng vào .values()
            categories_data = list(categories_page.object_list.values(
                'id',
                'name',
                # 'description', # Bỏ comment nếu bạn có và muốn hiển thị trường này
                # 'total_books'  # Bỏ comment nếu bạn có và muốn hiển thị trường này
            ))

            # --- Tạo response JSON với thông tin phân trang ---
            data = {
                'count': paginator.count, # Tổng số categories
                'num_pages': paginator.num_pages, # Tổng số trang
                'current_page': page, # Trang hiện tại
                'page_size': page_size, # Số lượng item mỗi trang
                'next_page': categories_page.next_page_number() if categories_page.has_next() else None,
                'previous_page': categories_page.previous_page_number() if categories_page.has_previous() else None,
                'results': categories_data # Danh sách categories của trang hiện tại
            }
            return JsonResponse(data)

        except Exception as e:
            print(f"Category List API Error: {e}")
            import traceback
            traceback.print_exc() # In traceback đầy đủ để debug
            return JsonResponse({'error': 'Could not retrieve categories.'}, status=500)
    else:
        # Chỉ cho phép phương thức GET
        return JsonResponse({'error': 'Method not allowed, please use GET'}, status=405)


@csrf_exempt # Exempt from CSRF
def register(request):
    if request.method == 'POST':
        user_form = UserRegistrationForm(request.POST)
        if not user_form.is_valid():
            # Provide more specific validation errors if possible
            return JsonResponse({'error': 'Invalid form data', 'details': user_form.errors}, status=400)

        new_user = user_form.save(commit=False)
        new_user.set_password(user_form.cleaned_data['password'])
        try:
            new_user.save()
            # Automatically log in the user after registration
            login(request, new_user, backend='django.contrib.auth.backends.ModelBackend') # Specify backend if needed
            return JsonResponse({
                'status': 'success',
                'message': 'User registered and logged in successfully.',
                'user': {
                    'id': new_user.id,
                    'email': new_user.email,
                    'name': new_user.name # Assuming 'name' field exists
                }
            }, status=201) # 201 Created is more appropriate
        except Exception as e:
            # Log the exception e for debugging
            print(f"Registration Error: {e}")
            return JsonResponse({'error': 'An internal error occurred during registration.'}, status=500)
    else:
        # Describe the expected input format for GET requests
        return JsonResponse({
            'message': 'Send POST request with registration data.',
            'required_fields': {
                'name': 'text',
                'email': 'email',
                'password': 'password',
                'password2': 'password (confirmation)'
            }
        }, status=200)

# --- User Browsing Views ---

@csrf_exempt
def user_login(request):
    # No token needed to log in
    if request.method == 'POST':
        form = LoginForm(request.POST) # Using form for validation
        if not form.is_valid():
            return JsonResponse({'error': 'Invalid form data', 'details': form.errors}, status=400)

        cd = form.cleaned_data
        email = cd.get('email')
        password = cd.get('password')

        # Use Django's authenticate to verify credentials
        user = authenticate(request, username=email, password=password)

        if user is not None:
            if user.is_active:
                # --- TẠO TOKENS KHI ĐĂNG NHẬP THÀNH CÔNG ---
                try:
                    refresh = RefreshToken.for_user(user)
                    access_token = str(refresh.access_token)
                    refresh_token = str(refresh)
                except Exception as e:
                    # Xử lý lỗi nếu không tạo được token (hiếm khi xảy ra nếu user hợp lệ)
                    print(f"Token Generation Error: {e}")
                    return JsonResponse({'error': 'Could not generate authentication tokens.'}, status=500)
                # --- KẾT THÚC TẠO TOKENS ---

                # --- TRẢ VỀ JSON BAO GỒM CẢ TOKENS ---
                return JsonResponse({
                    'status': 'success',
                    'message': 'Login successful.',
                    'user': { # Thông tin user (tùy chọn nhưng hữu ích)
                        'id': user.id,
                        'email': user.email,
                        'name': getattr(user, 'name', user.get_username())
                    },
                    # --- Tokens quan trọng ---
                    'access': access_token,  # Access token để dùng ngay
                    'refresh': refresh_token, # Refresh token để lưu và dùng làm mới
                    # --- Kết thúc Tokens ---
                }, status=200)
                # --- KẾT THÚC TRẢ VỀ JSON ---
            else:
                # User bị vô hiệu hóa
                return JsonResponse({'error': 'Account disabled'}, status=403)
        else:
            # Sai email hoặc mật khẩu
            # (Logic kiểm tra user tồn tại nhưng sai pass vẫn giữ nguyên)
            try:
                 Users.objects.get(email=email)
                 return JsonResponse({'error': 'Invalid credentials (password)'}, status=401)
            except Users.DoesNotExist:
                 return JsonResponse({'error': 'Invalid credentials (email)'}, status=401)
            except Exception as e:
                 print(f"Login User Lookup Error: {e}")
                 return JsonResponse({'error': 'An error occurred during login.'}, status=500)
    else:
        # GET request
        return JsonResponse({
            'message': 'Send POST request with login credentials.',
            'required_fields': { 'email': 'email', 'password': 'password' }
        }, status=200)

@csrf_exempt # Exempt from CSRF (usually logout is POST)
@token_required # Still require login to logout
def user_logout(request):
    # Ensure it's a POST request for logout to prevent CSRF via GET if exemption wasn't used
    if request.method != 'POST':
         return JsonResponse({'error': 'Method not allowed, please use POST'}, status=405)
    logout(request)
    return JsonResponse({'status': 'success', 'message': 'Logout successful.'}, status=200)


# ---------------------------------------------------
# API Views cho Cart
# ---------------------------------------------------

def _calculate_cart_totals(user_cart_instance): # Nhận vào instance của Cart
    """Tính tổng số lượng item và tổng giá trị cho một Cart instance."""
    if not user_cart_instance:
        return 0, Decimal('0.00')

    # Query các CartBooks liên quan đến user_cart_instance
    # Sử dụng related_name 'cartbooks_set' (mặc định nếu không đặt related_name trong CartBooks.cart)
    # Hoặc related_name bạn đã đặt (ví dụ: 'items_in_cart')
    totals = user_cart_instance.cartbooks_set.aggregate( # Hoặc user_cart_instance.items_in_cart.aggregate(...)
        total_items=models.Sum('quantity'),
        total_value=models.Sum(models.F('quantity') * models.F('book__price'), output_field=models.DecimalField())
    )

    total_items_count = totals['total_items'] or 0
    total_cart_value = totals['total_value'] or Decimal('0.00')

    return total_items_count, total_cart_value

@csrf_exempt
@token_required
def add_to_cart(request, book_id):
    """API: Thêm sách vào giỏ hàng (POST) - Dùng mô hình Cart/CartBooks."""
    current_user = request.user
    if request.method != 'POST': return JsonResponse({'error': 'Method not allowed, use POST'}, status=405)

    try:
        book_to_add = get_object_or_404(Books, id=book_id)
        if book_to_add.stock <= 0: return JsonResponse({'error': 'This book is out of stock'}, status=400)

        with transaction.atomic():
            user_cart, cart_created = Cart.objects.get_or_create(user=current_user)
            cart_item, item_created = CartBooks.objects.get_or_create(
                cart=user_cart, book=book_to_add, defaults={'quantity': 1}
            )
            if not item_created:
                current_quantity = cart_item.quantity
                if current_quantity + 1 > book_to_add.stock:
                    return JsonResponse({'error': f'Cannot add more "{book_to_add.title}". Only {book_to_add.stock - current_quantity} more copies available'}, status=400)
                cart_item.quantity = models.F('quantity') + 1
                cart_item.save(update_fields=['quantity'])
                cart_item.refresh_from_db()

        total_items, total_value = _calculate_cart_totals(user_cart)

        return JsonResponse({
            'status': 'success',
            'message': f'"{book_to_add.title}" {"added to" if item_created else "quantity updated in"} cart.',
            'item_quantity': cart_item.quantity,
            'total_cart_items': total_items,
            'total_cart_value': format_decimal(total_value),
        }, status=200)
    except Books.DoesNotExist: return JsonResponse({'error': 'Book not found'}, status=404)
    except Exception as e:
        print(f"Add Cart API Error (Cart/CartBooks): {e}")
        import traceback; traceback.print_exc()
        return JsonResponse({'error': 'Could not add item to cart.'}, status=500)

@csrf_exempt
@token_required
def update_cart(request):
    """
    API: Cập nhật số lượng sách trong giỏ hàng (POST) - Dùng mô hình Cart/CartBooks.
    Yêu cầu: Token header.
    Body params: book_id, quantity (>= 0).
    """
    current_user = request.user
    if request.method != 'POST': return JsonResponse({'error': 'Method not allowed, use POST'}, status=405)

    try:
        book_id_str = request.POST.get('book_id')
        quantity_str = request.POST.get('quantity')
        if book_id_str is None or quantity_str is None: return JsonResponse({'error': 'Missing fields: book_id, quantity'}, status=400)
        try:
            book_id = int(book_id_str); quantity = int(quantity_str)
            if quantity < 0: return JsonResponse({'error': 'Quantity must be >= 0'}, status=400)
        except ValueError: return JsonResponse({'error': 'Invalid format for book_id or quantity'}, status=400)

        with transaction.atomic():
            # Lấy cart của user, nếu không có cart thì không có gì để update
            user_cart = Cart.objects.filter(user=current_user).first()
            if not user_cart:
                return JsonResponse({'error': 'Cart not found for this user.'}, status=404)

            # Lấy cart item cần update
            cart_item = get_object_or_404(CartBooks.objects.select_related('book'), # Lấy cả sách để check stock/lấy tên
                                             cart=user_cart, book_id=book_id)
            book = cart_item.book

            message = ""
            if quantity == 0:
                # Xóa item
                message = f'"{book.title}" removed from cart.'
                cart_item.delete()
            else:
                # Cập nhật quantity, kiểm tra stock
                if quantity > book.stock:
                    return JsonResponse({'error': f'Only {book.stock} copies available for "{book.title}", requested {quantity}'}, status=400)
                cart_item.quantity = quantity
                cart_item.save(update_fields=['quantity'])
                message = f'Quantity for "{book.title}" updated to {quantity}.'

        total_items, total_value = _calculate_cart_totals(user_cart) # Tính lại tổng sau khi thay đổi

        return JsonResponse({
            'status': 'success',
            'message': message,
            'total_cart_items': total_items,
            'total_cart_value': format_decimal(total_value),
        }, status=200)
    except CartBooks.DoesNotExist: return JsonResponse({'error': 'Item with specified book_id not found in your cart.'}, status=404)
    except Exception as e:
        print(f"Update Cart API Error (Cart/CartBooks): {e}")
        import traceback; traceback.print_exc()
        return JsonResponse({'error': 'Could not update cart item.'}, status=500)

@csrf_exempt
@token_required
def remove_from_cart(request, book_id):
    """
    API: Xóa một item sách khỏi giỏ hàng (POST) - Dùng mô hình Cart/CartBooks.
    Yêu cầu: Token header.
    Path param: book_id.
    """
    current_user = request.user
    if request.method != 'POST': return JsonResponse({'error': 'Method not allowed, use POST'}, status=405)

    try:
        # Validate book_id
        try: b_id = int(book_id)
        except (ValueError, TypeError): return JsonResponse({'error': 'Invalid book_id format.'}, status=400)

        with transaction.atomic():
            user_cart = Cart.objects.filter(user=current_user).first()
            if not user_cart: return JsonResponse({'error': 'Cart not found.'}, status=404)

            cart_item = get_object_or_404(CartBooks.objects.select_related('book'),
                                             cart=user_cart, book_id=b_id)
            item_title = cart_item.book.title
            cart_item.delete()

        total_items, total_value = _calculate_cart_totals(user_cart) # Tính lại tổng

        return JsonResponse({
            'status': 'success',
            'message': f'"{item_title}" removed from cart.',
            'total_cart_items': total_items,
            'total_cart_value': format_decimal(total_value),
        }, status=200)
    except CartBooks.DoesNotExist: return JsonResponse({'error': 'Item with specified book_id not found in your cart.'}, status=404)
    except Exception as e:
        print(f"Remove Cart API Error (Cart/CartBooks): {e}")
        import traceback; traceback.print_exc()
        return JsonResponse({'error': 'Could not remove item from cart.'}, status=500)

@csrf_exempt
@token_required
def clear_cart(request):
    """
    API: Xóa tất cả các item khỏi giỏ hàng (POST) - Dùng mô hình Cart/CartBooks.
    Yêu cầu: Token header.
    """
    current_user = request.user
    if request.method != 'POST': return JsonResponse({'error': 'Method not allowed, use POST'}, status=405)

    try:
        with transaction.atomic():
            user_cart = Cart.objects.filter(user=current_user).first()
            if user_cart:
                # Xóa tất cả CartBooks liên quan đến cart này
                CartBooks.objects.filter(cart=user_cart).delete()
                message = 'Cart cleared successfully.'
            else:
                message = 'Cart is already empty.'

        # Sau khi xóa hết item, tổng là 0
        total_items = 0
        total_value = Decimal('0.00')

        return JsonResponse({
            'status': 'success',
            'message': message,
            'total_cart_items': total_items,
            'total_cart_value': format_decimal(total_value),
        }, status=200)
    except Exception as e:
        print(f"Clear Cart API Error (Cart/CartBooks): {e}")
        import traceback; traceback.print_exc()
        return JsonResponse({'error': 'Could not clear cart.'}, status=500)

@csrf_exempt
@token_required
def cart(request):
    """
    API: Xem nội dung giỏ hàng hiện tại (GET) - Dùng mô hình Cart/CartBooks.
    Yêu cầu: Token header.
    """
    current_user = request.user
    if request.method != 'GET': return JsonResponse({'error': 'Method not allowed, use GET'}, status=405)

    try:
        # Lấy cart của user
        user_cart = Cart.objects.filter(user=current_user).first()

        items_data = []
        cart_id = None
        total_items_count = 0
        total_cart_value = Decimal('0.00')

        if user_cart:
            cart_id = user_cart.id
            # Lấy tất cả items trong cart, prefetch sách để tối ưu
            cart_items_query = CartBooks.objects.filter(cart=user_cart).select_related('book')
            
            for item in cart_items_query:
                formatted_book = None # Khởi tạo formatted_book
                item_total_value = Decimal('0.00') # Khởi tạo item_total

                if item.book: # Chỉ xử lý nếu item.book tồn tại
                    formatted_book = format_book_data(item.book)
                    item_total_value = item.book.price * item.quantity

                items_data.append({
                    'quantity': item.quantity,
                    'book': formatted_book,
                    'item_total': format_decimal(item_total_value)
                })
            # Tính tổng dùng helper function
            total_items_count, total_cart_value = _calculate_cart_totals(user_cart)

        # Tạo response
        data = {
            'cart_id': cart_id, # ID của cart (có thể null nếu cart chưa tồn tại)
            'items': items_data,
            'total_items': total_items_count, # Tổng số lượng các cuốn sách
            'total_value': format_decimal(total_cart_value) # Tổng giá trị giỏ hàng
        }
        return JsonResponse(data)

    except Exception as e:
        print(f"View Cart API Error (Cart/CartBooks): {e}")
        import traceback; traceback.print_exc()
        return JsonResponse({'error': 'Could not retrieve cart details.'}, status=500)


@csrf_exempt
@token_required
def place_order_from_cart(request):
    current_user = request.user
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed, please use POST'}, status=405)

    shipping_address = request.POST.get('shipping_address')
    if not shipping_address:
        return JsonResponse({'error': 'Shipping address is required.'}, status=400)

    try:
        with transaction.atomic():
            try:
                user_cart = Cart.objects.select_related('user').prefetch_related(
                    models.Prefetch('cartbooks_set', queryset=CartBooks.objects.select_related('book'))
                ).get(user=current_user)
            except Cart.DoesNotExist:
                return JsonResponse({'error': 'Your cart is empty or does not exist.'}, status=400)

            cart_items_to_process = user_cart.cartbooks_set.all()
            if not cart_items_to_process.exists():
                return JsonResponse({'error': 'Your cart is empty. Cannot place an order.'}, status=400)

            # Kiểm tra tồn kho
            insufficient_stock_items = []
            for item in cart_items_to_process:
                if item.quantity > item.book.stock:
                    insufficient_stock_items.append(
                        f'"{item.book.title}" (Requested: {item.quantity}, Available: {item.book.stock})'
                    )
            if insufficient_stock_items:
                return JsonResponse({
                    'error': 'Insufficient stock for some items. Please review your cart.',
                    'details': insufficient_stock_items
                }, status=400)

            # --- BỎ QUA GIẢ ĐỊNH THANH TOÁN THÀNH CÔNG NGAY LẬP TỨC ---
            # payment_successful = True # <<< XÓA HOẶC COMMENT DÒNG NÀY

            # Tính tổng giá trị giỏ hàng
            _, final_order_total = _calculate_cart_totals(user_cart)

            # Tạo bản ghi Order mới với trạng thái mặc định
            new_order = Order.objects.create(
                user=current_user,
                shipping_address=shipping_address,
                total_amount=final_order_total
                # status và payment_status sẽ lấy default
            )
            # new_order.save() # Không cần nếu number tự tạo trong save()

            order_items_created_data = []
            for cart_book_item in cart_items_to_process:
                book_instance = cart_book_item.book
                order_item = OrderItem.objects.create(
                    order=new_order,
                    book=book_instance,
                    quantity=cart_book_item.quantity
                )
                # --- SỬ DỤNG format_book_data CHO SÁCH TRONG ORDER ITEM ---
                formatted_book_for_order = format_book_data(book_instance) if book_instance else None
                # ----------------------------------------------------------
                order_items_created_data.append({
                    # 'order_item_id': order_item.id, # Tùy chọn
                    'quantity': order_item.quantity,
                    'price_at_purchase': format_decimal(order_item.price_at_purchase),
                    'book': formatted_book_for_order # <<< Thông tin sách đầy đủ (bao gồm image_url)
                })

                # --- LOGIC GIẢM TỒN KHO VÀ TĂNG SOLD CHỈ NÊN XẢY RA KHI THANH TOÁN THÀNH CÔNG VÀ ĐƠN HÀNG HOÀN TẤT ---
                # TẠM THỜI CHÚNG TA SẼ KHÔNG GIẢM STOCK NGAY TẠI ĐÂY
                # Việc giảm stock sẽ được thực hiện ở một bước sau (ví dụ: khi admin xác nhận đơn hàng/thanh toán)
                #
                # if new_order.status == Order._COMPLETED and new_order.payment_status == Order.PAID:
                #     book_instance.stock = models.F('stock') - cart_book_item.quantity
                #     if hasattr(book_instance, 'sold'):
                #         book_instance.sold = models.F('sold') + cart_book_item.quantity
                #         book_instance.save(update_fields=['stock', 'sold'])
                #     else:
                #         book_instance.save(update_fields=['stock'])
                # --- KẾT THÚC TẠM DỪNG GIẢM STOCK ---


            # Xóa các item khỏi giỏ hàng
            CartBooks.objects.filter(cart=user_cart).delete()

            return JsonResponse({
                'status': 'success',
                'message': 'Order placed successfully and is awaiting confirmation/payment.', # Thông báo rõ hơn
                'order': {
                    'order_id': new_order.id,
                    'order_number': new_order.number,
                    'total_amount': format_decimal(new_order.total_amount),
                    'status': new_order.get_status_display(),
                    'payment_status': new_order.get_payment_status_display(),
                    'shipping_address': new_order.shipping_address,
                    'created_at': new_order.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                    'items': order_items_created_data # <<< Đã chứa sách đã format
                }
            }, status=201)

    except Cart.DoesNotExist:
        return JsonResponse({'error': 'Your cart is empty or does not exist.'}, status=400)
    except Exception as e:
        print(f"Place Order API Error: {e}")
        import traceback; traceback.print_exc()
        return JsonResponse({'error': f'Could not place order. An unexpected error occurred: {str(e)}'}, status=500)

@csrf_exempt # GET thường an toàn
@token_required # <<< Bắt buộc: Chỉ người dùng đã đăng nhập mới xem được profile của mình
def user_profile(request):
    """
    API: Lấy thông tin cá nhân của người dùng đang đăng nhập.
    Yêu cầu: Token trong header Authorization.
    Phương thức: GET
    """
    # Decorator @token_required đã xác thực token và gán user vào request.user
    current_user = request.user

    if request.method == 'GET':
        try:
            # Chuẩn bị dữ liệu trả về
            # Chỉ trả về những thông tin cần thiết và an toàn để hiển thị
            user_data = {
                'id': current_user.id,
                'email': current_user.email,
                'name': getattr(current_user, 'name', current_user.get_username()), # Lấy tên nếu có
                'type': getattr(current_user, 'type', 'user'), # Loại tài khoản (nếu có)
                'is_staff': current_user.is_staff, # Trạng thái staff
                # Thêm các trường khác bạn muốn hiển thị từ model Users của bạn
                # Ví dụ:
                # 'phone_number': getattr(current_user, 'phone_number', None),
                # 'date_joined': current_user.date_joined.strftime("%Y-%m-%d %H:%M:%S") if current_user.date_joined else None,
                'last_login': current_user.last_login.strftime("%Y-%m-%d %H:%M:%S") if current_user.last_login else None,
            }

            # Không bao giờ trả về password hash hoặc thông tin nhạy cảm khác!

            return JsonResponse({'status': 'success', 'user': user_data})

        except AttributeError as e:
            # Bắt lỗi nếu cố truy cập thuộc tính không tồn tại trên user model
            print(f"User Profile API Error - AttributeError: {e}")
            return JsonResponse({'error': f'Attribute error accessing user data: {e}'}, status=500)
        except Exception as e:
            print(f"User Profile API Error: {e}")
            import traceback
            traceback.print_exc()
            return JsonResponse({'error': 'Could not retrieve user profile.'}, status=500)
    else:
        return JsonResponse({'error': 'Method not allowed, please use GET'}, status=405)

@csrf_exempt
@token_required # <<< Bắt buộc: Chỉ user đăng nhập mới đổi được pass của mình
def change_password(request):
    """
    API: Cho phép người dùng đang đăng nhập thay đổi mật khẩu của họ.
    Yêu cầu: Token trong header Authorization.
    Phương thức: POST
    Body params (form-data/x-www-form-urlencoded): old_password, new_password1, new_password2
    """
    current_user = request.user # User lấy từ token

    if request.method == 'POST':
        # Tạo form đổi mật khẩu, truyền vào user hiện tại và dữ liệu từ POST
        form = PasswordChangeForm(user=current_user, data=request.POST)

        if form.is_valid():
            # Nếu form hợp lệ (mật khẩu cũ đúng, mật khẩu mới khớp và đạt yêu cầu)
            try:
                # Lưu mật khẩu mới vào database
                # form.save() sẽ tự động hash mật khẩu mới và cập nhật cho user
                user_saved = form.save()

                # QUAN TRỌNG cho API Token-based:
                # Mặc dù form.save() hoạt động, việc thay đổi mật khẩu có thể làm vô hiệu hóa
                # một số cơ chế liên quan đến session (nếu có).
                # Với API JWT thuần túy, việc này thường không ảnh hưởng trực tiếp đến
                # các token JWT hiện có (trừ khi logic token của bạn dựa vào password hash,
                # điều này không phổ biến với simplejwt).
                # Dòng update_session_auth_hash thường dùng cho web truyền thống dùng session.
                # Bạn có thể bỏ qua nó trong API JWT, nhưng để đó cũng không gây hại.
                # update_session_auth_hash(request, user_saved)

                # (Tùy chọn) Vô hiệu hóa các Refresh Token cũ sau khi đổi mật khẩu
                # Điều này tăng cường bảo mật, yêu cầu user đăng nhập lại trên các thiết bị khác
                # bằng mật khẩu mới để lấy token mới.
                # Yêu cầu cài đặt `rest_framework_simplejwt.token_blacklist`
                # try:
                #     from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken
                #     # Tìm tất cả các token chưa hết hạn của user này
                #     tokens = OutstandingToken.objects.filter(user=user_saved)
                #     for token_instance in tokens:
                #         # Blacklist các refresh token
                #         if hasattr(token_instance, 'token') and token_instance.token and token_instance.token_type == 'refresh':
                #             # Kiểm tra xem đã blacklist chưa để tránh lỗi
                #             if not BlacklistedToken.objects.filter(token=token_instance).exists():
                #                 BlacklistedToken.objects.create(token=token_instance)
                #     print(f"Blacklisted existing refresh tokens for user {user_saved.id}")
                # except ImportError:
                #     print("Skipping token blacklist: token_blacklist app not found or configured.")
                # except Exception as e_blacklist:
                #     print(f"Error blacklisting tokens after password change: {e_blacklist}")

                return JsonResponse({
                    'status': 'success',
                    'message': 'Password changed successfully.'
                    # Không cần trả về token mới ở đây, user có thể tiếp tục dùng token cũ
                    # cho đến khi nó hết hạn, hoặc bạn có thể yêu cầu họ đăng nhập lại.
                }, status=200)

            except Exception as e:
                # Bắt lỗi không mong muốn khi lưu form
                print(f"Change Password Save Error: {e}")
                import traceback
                traceback.print_exc()
                return JsonResponse({'error': 'Could not save new password due to a server error.'}, status=500)
        else:
            # Nếu form không hợp lệ (sai mật khẩu cũ, mật khẩu mới không khớp,...)
            # Trả về lỗi validation từ form
            # Cần định dạng lại lỗi của form cho JSON
            error_dict = {}
            for field, errors in form.errors.items():
                # Lấy lỗi đầu tiên cho mỗi trường (hoặc nối tất cả nếu muốn)
                error_dict[field] = errors[0] if errors else 'Unknown error'

            return JsonResponse({
                'error': 'Password change failed. Please check the details.',
                'details': error_dict
            }, status=400) # 400 Bad Request cho lỗi validation
    else:
        # Chỉ cho phép POST
        return JsonResponse({'error': 'Method not allowed, please use POST'}, status=405)
@csrf_exempt # GET thường an toàn
@token_required # <<< Bắt buộc: User phải đăng nhập để xem lịch sử của mình
def order_history(request):
    """
    API: Lấy danh sách lịch sử đơn hàng của người dùng đang đăng nhập.
    Yêu cầu: Token trong header Authorization.
    Phương thức: GET
    Query parameters:
        - page: Số trang (mặc định 1)
        - page_size: Số lượng đơn hàng mỗi trang (mặc định 10, max 50)
    """
    current_user = request.user

    if request.method == 'GET':
        try:
            # --- Lấy tham số phân trang ---
            try:
                page = int(request.GET.get('page', 1))
            except ValueError:
                page = 1
            try:
                page_size = min(int(request.GET.get('page_size', 10)), 50)
                if page_size <= 0: page_size = 10
            except ValueError:
                page_size = 10

            # --- Query các đơn hàng của user ---
            # Lấy các đơn hàng đã được đặt bởi user hiện tại
            # Lọc bỏ các trạng thái không mong muốn nếu cần (ví dụ: loại bỏ 'pending' nếu có)
            # Sắp xếp theo ngày tạo giảm dần (mới nhất trước)
            orders_query = Order.objects.filter(
                user=current_user
            ).order_by('-created_at')

            # --- Áp dụng phân trang ---
            paginator = Paginator(orders_query, page_size)
            try:
                orders_page = paginator.page(page)
            except PageNotAnInteger:
                orders_page = paginator.page(1)
                page = 1
            except EmptyPage:
                orders_page = paginator.page(paginator.num_pages)
                page = paginator.num_pages

            # --- Chuẩn bị dữ liệu đơn hàng cho trang hiện tại ---
            # Chỉ lấy thông tin tóm tắt cho danh sách
            orders_data = []
            for order in orders_page.object_list:
                orders_data.append({
                    'order_id': order.id,
                    'order_number': order.number,
                    'created_at': order.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                    'total_amount': format_decimal(order.total_amount),
                    'status': order.get_status_display(), # Lấy tên hiển thị
                    'payment_status': order.get_payment_status_display(), # Lấy tên hiển thị
                    # Thêm link tới chi tiết đơn hàng nếu có API chi tiết
                    # 'detail_url': reverse('store:order_detail', kwargs={'order_id': order.id}) # Cần có API order_detail
                })

            # --- Tạo response JSON với thông tin phân trang ---
            data = {
                'count': paginator.count, # Tổng số đơn hàng khớp điều kiện
                'num_pages': paginator.num_pages,
                'current_page': page,
                'page_size': page_size,
                'next_page': orders_page.next_page_number() if orders_page.has_next() else None,
                'previous_page': orders_page.previous_page_number() if orders_page.has_previous() else None,
                'results': orders_data # Danh sách đơn hàng tóm tắt của trang hiện tại
            }
            return JsonResponse(data)

        except Exception as e:
            print(f"Order History API Error: {e}")
            import traceback
            traceback.print_exc()
            return JsonResponse({'error': 'Could not retrieve order history.'}, status=500)
    else:
        return JsonResponse({'error': 'Method not allowed, please use GET'}, status=405)


# --- (TÙY CHỌN) API Chi tiết đơn hàng ---
@csrf_exempt
@token_required
def order_detail(request, order_id):
    """
    API: Lấy thông tin chi tiết của một đơn hàng cụ thể của người dùng.
    Yêu cầu: Token header.
    Phương thức: GET
    Path param: order_id - ID của đơn hàng cần xem.
    """
    current_user = request.user
    if request.method == 'GET':
        try:
            order = get_object_or_404(
                Order.objects.prefetch_related(
                    models.Prefetch('items', queryset=OrderItem.objects.select_related('book__category')) # Prefetch book và category
                ),
                id=order_id,
                user=current_user
            )

            items_data = []
            for item in order.items.all():
                # --- SỬ DỤNG format_book_data CHO SÁCH TRONG ORDER ITEM ---
                formatted_book = format_book_data(item.book) if item.book else None
                # ----------------------------------------------------------
                items_data.append({
                    # 'order_item_id': item.id, # Tùy chọn
                    'quantity': item.quantity,
                    'price_at_purchase': format_decimal(item.price_at_purchase),
                    'item_total': format_decimal(item.item_total),
                    'book': formatted_book # <<< Thông tin sách đầy đủ (bao gồm image_url)
                })

            # Chuẩn bị dữ liệu đơn hàng chi tiết
            order_data = {
                'order_id': order.id,
                'order_number': order.number,
                'created_at': order.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                'updated_at': order.updated_at.strftime("%Y-%m-%d %H:%M:%S"),
                'total_amount': format_decimal(order.total_amount),
                'status': order.get_status_display(),
                'payment_status': order.get_payment_status_display(),
                'shipping_address': order.shipping_address,
                'items': items_data # Bao gồm cả danh sách item chi tiết
            }
            return JsonResponse({'status': 'success', 'order': order_data})

        except Order.DoesNotExist: # Xảy ra nếu get_object_or_404 không tìm thấy hoặc không thuộc user
             return JsonResponse({'error': 'Order not found or you do not have permission to view it.'}, status=404)
        except Exception as e:
            print(f"Order Detail API Error: {e}")
            import traceback; traceback.print_exc()
            return JsonResponse({'error': 'Could not retrieve order details.'}, status=500)
    else:
        return JsonResponse({'error': 'Method not allowed, please use GET'}, status=405)

# -- ADMIN API--

@csrf_exempt
def admin_login(request):
    """API đăng nhập dành riêng cho người dùng có quyền Staff."""
    if request.method == 'POST':
        form = LoginForm(request.POST) # Vẫn dùng LoginForm để validate
        if not form.is_valid():
            return JsonResponse({'error': 'Invalid form data', 'details': form.errors}, status=400)

        cd = form.cleaned_data
        email = cd.get('email')
        password = cd.get('password')

        user = authenticate(request, username=email, password=password)

        if user is not None:
            # --- KIỂM TRA is_active VÀ is_staff ---
            if user.is_active and user.is_staff: # <<< BẮT BUỘC PHẢI LÀ STAFF
                try:
                    refresh = RefreshToken.for_user(user)
                    access_token = str(refresh.access_token)
                    refresh_token = str(refresh)
                except Exception as e:
                    print(f"Admin Token Generation Error: {e}")
                    return JsonResponse({'error': 'Could not generate authentication tokens.'}, status=500)

                return JsonResponse({
                    'status': 'success',
                    'message': 'Admin login successful.',
                    'user': {
                        'id': user.id,
                        'email': user.email,
                        'name': getattr(user, 'name', user.get_username()),
                        'is_staff': True # Luôn là true ở đây
                    },
                    'access': access_token,
                    'refresh': refresh_token,
                }, status=200)
            elif not user.is_staff:
                # Nếu đăng nhập thành công nhưng không phải staff
                return JsonResponse({'error': 'Access denied. Staff account required.'}, status=403)
            else: # Trường hợp is_staff=True nhưng is_active=False
                return JsonResponse({'error': 'Admin account disabled'}, status=403)
        else:
            # Xử lý sai credentials
            # Kiểm tra xem có phải staff account sai pass không
            try:
                maybe_staff = Users.objects.get(email=email, is_staff=True)
                # Nếu tìm thấy staff account -> sai pass
                return JsonResponse({'error': 'Invalid credentials (password) for staff account.'}, status=401)
            except Users.DoesNotExist:
                # Nếu không tìm thấy staff account với email đó
                 return JsonResponse({'error': 'Invalid credentials or not a staff account.'}, status=401)
            except Exception as e:
                 print(f"Admin Login User Lookup Error: {e}")
                 return JsonResponse({'error': 'An error occurred during admin login.'}, status=500)
    else:
         return JsonResponse({ 'message': 'Send POST request...', 'required_fields': ... }, status=200)

try:
    # Import các model blacklist nếu tồn tại
    from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken
    HAS_BLACKLIST_APP = True
except ImportError:
    # Nếu không cài app blacklist, đặt cờ thành False
    HAS_BLACKLIST_APP = False

@csrf_exempt # Vẫn giữ csrf_exempt để nhất quán
@staff_token_required # <<< BẮT BUỘC: Chỉ staff mới logout qua API này được
def admin_logout(request):
    """
    API: Đăng xuất cho người dùng có quyền Staff.
    Yêu cầu: Token hợp lệ của Staff trong header Authorization.
    Phương thức: POST
    Body params (tùy chọn): refresh - Refresh token để blacklist.
    """
    # Decorator @staff_token_required đã xác thực token và kiểm tra is_staff.
    # request.user là đối tượng staff user.
    staff_user = request.user

    if request.method == 'POST':
        try:
            message = f'Admin logout successful for {staff_user.email}. Client should discard tokens.'

            # --- Tùy chọn: Blacklist Refresh Token ---
            if HAS_BLACKLIST_APP: # Chỉ thực hiện nếu app blacklist được cài đặt
                refresh_token = request.POST.get('refresh')
                if refresh_token:
                    try:
                        token = RefreshToken(refresh_token)
                        # Kiểm tra xem token này có thực sự thuộc về user đang logout không
                        # Mặc dù không bắt buộc chặt chẽ, nhưng tăng thêm lớp kiểm tra
                        if token.payload.get('user_id') == staff_user.id:
                             # Tìm outstanding token tương ứng
                            outstanding_token = OutstandingToken.objects.filter(
                                token=str(token), user=staff_user
                            ).first()
                            if outstanding_token:
                                 # Kiểm tra xem đã blacklist chưa
                                if not BlacklistedToken.objects.filter(token=outstanding_token).exists():
                                    BlacklistedToken.objects.create(token=outstanding_token)
                                    message = f'Admin logout successful for {staff_user.email}. Refresh token blacklisted.'
                                else:
                                    message += ' (Refresh token was already blacklisted).'
                            else:
                                message += ' (Could not find outstanding refresh token to blacklist).'
                        else:
                            # Token không khớp user, không blacklist nhưng vẫn cho logout thành công phía client
                            message += ' (Provided refresh token does not belong to this user, not blacklisted).'
                    except TokenError as e_token:
                        # Nếu refresh token gửi lên không hợp lệ/hết hạn, vẫn coi là logout thành công
                        message += f' (Could not blacklist invalid/expired refresh token: {str(e_token)}).'
                    except Exception as e_blacklist_detail:
                        # Lỗi khác trong quá trình blacklist
                        print(f"Error blacklisting admin refresh token: {e_blacklist_detail}")
                        message += ' (Server error during token blacklisting).'
                else:
                    message += ' (No refresh token provided for blacklisting).'
            else:
                 message += ' (Token blacklisting not available).'
            # --- Kết thúc Blacklist ---

            # Luôn trả về thành công để client xóa token
            return JsonResponse({'status': 'success', 'message': message}, status=200)

        except Exception as e:
            # Lỗi không mong muốn xảy ra trong quá trình xử lý (rất hiếm ở đây)
            print(f"Admin Logout Error: {e}")
            import traceback; traceback.print_exc()
            # Vẫn nên trả về thành công để client có thể xóa token
            return JsonResponse({'status': 'success', 'message': 'Logout processed, but an unexpected server error occurred.'}, status=200)
    else:
        # Chỉ cho phép POST
        return JsonResponse({'error': 'Method not allowed, please use POST'}, status=405)
@csrf_exempt # GET thường an toàn
@staff_token_required # <<< Bắt buộc: Chỉ staff mới xem được danh sách này
def admin_list_pending_orders(request):
    """
    API (Admin): Liệt kê các đơn hàng đang chờ duyệt (ví dụ: status='processing').
    Yêu cầu: Token của Staff trong header Authorization.
    Phương thức: GET
    Query parameters:
        - page: Số trang (mặc định 1)
        - page_size: Số lượng đơn hàng mỗi trang (mặc định 10, max 50)
        - sort_by: Tiêu chí sắp xếp (ví dụ: 'created_at', '-total_amount'. Mặc định: '-created_at')
        - search_user: Email hoặc tên người dùng để tìm đơn hàng (tùy chọn)
        - search_order: Mã đơn hàng để tìm (tùy chọn)
    """
    # Decorator @staff_token_required đã xác thực token và kiểm tra is_staff.
    # request.user là đối tượng staff user.

    if request.method == 'GET':
        try:
            # --- Lấy tham số phân trang và sắp xếp ---
            try: page = int(request.GET.get('page', 1))
            except ValueError: page = 1

            try:
                page_size = min(int(request.GET.get('page_size', 10)), 50)
                if page_size <= 0: page_size = 10
            except ValueError: page_size = 10

            sort_by = request.GET.get('sort_by', '-created_at') # Mặc định sắp xếp theo ngày tạo mới nhất
            valid_sort_fields = ['created_at', '-created_at', 'total_amount', '-total_amount', 'user__email', '-user__email', 'number', '-number']
            if sort_by not in valid_sort_fields:
                sort_by = '-created_at' # Reset về default nếu sort_by không hợp lệ

            # --- Lấy tham số tìm kiếm (tùy chọn) ---
            search_user_query = request.GET.get('search_user', '').strip()
            search_order_query = request.GET.get('search_order', '').strip()


           # --- Query các đơn hàng đang chờ duyệt ---
            orders_query = Order.objects.select_related('user') # Bắt đầu query

            # --- Áp dụng tìm kiếm trước (nếu có) ---
            if search_user_query:
                orders_query = orders_query.filter(
                    models.Q(user__email__icontains=search_user_query) |
                    models.Q(user__name__icontains=search_user_query)
                )
            if search_order_query:
                orders_query = orders_query.filter(number__icontains=search_order_query)

            # --- LỌC BỎ ĐƠN HÀNG ĐÃ HOÀN THÀNH ---
            # Sử dụng exclude với tên trường 'status' và giá trị hằng số
            orders_query = orders_query.exclude(status__in=[Order.COMPLETED, Order.CANCELLED])
            # ------------------------------------

            # Áp dụng sắp xếp
            orders_query = orders_query.order_by(sort_by)


            # --- Áp dụng phân trang ---
            paginator = Paginator(orders_query, page_size)
            try: orders_page = paginator.page(page)
            except PageNotAnInteger: orders_page = paginator.page(1); page = 1
            except EmptyPage:
                if paginator.num_pages > 0: orders_page = paginator.page(paginator.num_pages); page = paginator.num_pages
                else: orders_page = paginator.page(1); page = 1


            # --- Chuẩn bị dữ liệu đơn hàng cho trang hiện tại ---
            orders_data = []
            if orders_page.object_list:
                for order in orders_page.object_list:
                    orders_data.append({
                        'order_id': order.id,
                        'order_number': order.number,
                        'user_email': order.user.email if order.user else "N/A",
                        'user_name': getattr(order.user, 'name', None) if order.user else "N/A",
                        'created_at': order.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                        'total_amount': format_decimal(order.total_amount),
                        'status': order.get_status_display(),
                        'payment_status': order.get_payment_status_display(),
                        'shipping_address': order.shipping_address,
                        # Thêm link tới API admin duyệt/thay đổi trạng thái đơn hàng nếu có
                        # 'actions': {
                        #     'approve_url': reverse('store:admin_approve_order', kwargs={'order_id': order.id}),
                        #     'reject_url': reverse('store:admin_reject_order', kwargs={'order_id': order.id}),
                        # }
                    })

            # --- Tạo response JSON với thông tin phân trang ---
            data = {
                'count': paginator.count,
                'num_pages': paginator.num_pages,
                'current_page': page,
                'page_size': page_size,
                'sort_by': sort_by,
                'search_user_query': search_user_query if search_user_query else None,
                'search_order_query': search_order_query if search_order_query else None,
                'next_page': orders_page.next_page_number() if orders_page.has_next() else None,
                'previous_page': orders_page.previous_page_number() if orders_page.has_previous() else None,
                'results': orders_data
            }
            return JsonResponse(data)

        except Exception as e:
            print(f"Admin List Pending Orders API Error: {e}")
            import traceback; traceback.print_exc()
            return JsonResponse({'error': 'Could not retrieve pending orders list.'}, status=500)
    else:
        return JsonResponse({'error': 'Method not allowed, please use GET'}, status=405)

@csrf_exempt
@staff_token_required # <<< Chỉ staff mới được cập nhật trạng thái đơn hàng
@transaction.atomic # <<< Bọc trong transaction vì có thể cập nhật nhiều thứ (status, payment, stock)
def admin_update_order_status(request, order_id):
    """
    API (Admin): Cập nhật trạng thái và/hoặc trạng thái thanh toán của đơn hàng.
    Yêu cầu: Token của Staff.
    Phương thức: POST (hoặc PUT/PATCH)
    Path param: order_id - ID của đơn hàng cần cập nhật.
    Body params:
        - status (tùy chọn): Trạng thái đơn hàng mới (vd: 'completed', 'cancelled').
        - payment_status (tùy chọn): Trạng thái thanh toán mới (vd: 'paid', 'refunded').
    """
    # request.user là staff user đã được xác thực

    if request.method != 'POST': # Hoặc kiểm tra PUT/PATCH nếu dùng phương thức đó
        return JsonResponse({'error': 'Method not allowed, please use POST'}, status=405)

    try:
        # Lấy đơn hàng cần cập nhật
        order_to_update = get_object_or_404(Order.objects.select_related('user'), id=order_id)

        # Lấy trạng thái mới từ request body
        new_status = request.POST.get('status', None)
        new_payment_status = request.POST.get('payment_status', None)

        # Kiểm tra xem có ít nhất một trạng thái được cung cấp không
        if new_status is None and new_payment_status is None:
            return JsonResponse({'error': 'At least one status (status or payment_status) must be provided.'}, status=400)

        updated_fields = [] # Theo dõi các trường đã thay đổi
        status_changed_to_completed = False
        payment_changed_to_paid = False

        # --- Validate và cập nhật Order Status ---
        if new_status is not None:
            # Lấy danh sách các key trạng thái hợp lệ từ choices
            valid_statuses = [s[0] for s in Order.ORDER_STATUS_CHOICES]
            if new_status not in valid_statuses:
                return JsonResponse({
                    'error': f"Invalid order status '{new_status}'. Valid options are: {', '.join(valid_statuses)}"
                }, status=400)
            # Chỉ cập nhật nếu trạng thái thực sự thay đổi
            if order_to_update.status != new_status:
                order_to_update.status = new_status
                updated_fields.append('status')
                if new_status == Order.COMPLETED: # <<< Ghi nhận nếu chuyển sang completed
                     status_changed_to_completed = True
            # Lưu ý: Có thể thêm logic kiểm tra chuyển đổi trạng thái hợp lệ ở đây
            # Ví dụ: không cho phép chuyển từ COMPLETED về PROCESSING

        # --- Validate và cập nhật Payment Status ---
        if new_payment_status is not None:
            valid_payment_statuses = [p[0] for p in Order.PAYMENT_STATUS_CHOICES]
            if new_payment_status not in valid_payment_statuses:
                 return JsonResponse({
                    'error': f"Invalid payment status '{new_payment_status}'. Valid options are: {', '.join(valid_payment_statuses)}"
                }, status=400)
            # Chỉ cập nhật nếu trạng thái thực sự thay đổi
            if order_to_update.payment_status != new_payment_status:
                order_to_update.payment_status = new_payment_status
                updated_fields.append('payment_status')
                if new_payment_status == Order.PAID: # <<< Ghi nhận nếu chuyển sang paid
                    payment_changed_to_paid = True
            # Lưu ý: Có thể thêm logic kiểm tra chuyển đổi trạng thái thanh toán hợp lệ
            # Ví dụ: không cho phép chuyển từ PAID về UNPAID (trừ khi là REFUNDED)

        # Nếu có thay đổi, lưu lại Order
        if updated_fields:
            order_to_update.save(update_fields=updated_fields)
            print(f"Order {order_to_update.id} updated fields: {updated_fields}") # Ghi log nếu cần
        else:
            # Không có gì thay đổi
             return JsonResponse({
                 'status': 'no_change',
                 'message': 'No changes detected in status or payment_status.',
                 'order': _get_order_detail_data(order_to_update) # Trả về trạng thái hiện tại
             }, status=200)


        # --- Xử lý giảm tồn kho và tăng số lượng bán ---
        # Chỉ thực hiện khi đơn hàng chuyển sang HOÀN THÀNH (COMPLETED)
        # VÀ trạng thái thanh toán là ĐÃ THANH TOÁN (PAID)
        # Chúng ta cần kiểm tra trạng thái *sau khi* đã lưu thay đổi
        order_after_update = Order.objects.get(pk=order_to_update.pk) # Lấy lại trạng thái mới nhất

        # Biến để kiểm tra xem logic stock đã được chạy cho đơn này chưa
        # (Phòng trường hợp API bị gọi lại cho đơn đã completed/paid)
        # Cách tốt hơn là dùng một trường riêng trên Order model: stock_adjusted = models.BooleanField(default=False)
        stock_already_adjusted = False # Giả định là chưa (cần cơ chế kiểm tra tốt hơn)

        if order_after_update.status == Order.COMPLETED and order_after_update.payment_status == Order.PAID and not stock_already_adjusted:
            print(f"Order {order_after_update.id} is COMPLETED and PAID. Adjusting stock...")
            order_items = OrderItem.objects.filter(order=order_after_update).select_related('book')
            adjustment_errors = []
            for item in order_items:
                if item.book: # Kiểm tra sách còn tồn tại không
                    try:
                        # Dùng update với F() để giảm stock an toàn
                        updated_count = Books.objects.filter(pk=item.book.pk, stock__gte=item.quantity).update(
                            stock=models.F('stock') - item.quantity,
                            sold=models.F('sold') + item.quantity # Giả sử có trường sold
                        )
                        if updated_count == 0:
                            # Lỗi: Không đủ hàng tồn kho khi cố gắng cập nhật
                            adjustment_errors.append(f"Insufficient stock for book ID {item.book.pk} ('{item.book.title}') when trying to complete order.")
                            # QUAN TRỌNG: Ở đây transaction sẽ rollback nếu có lỗi này xảy ra,
                            # tức là trạng thái đơn hàng sẽ không được cập nhật thành completed/paid.
                            # Bạn cần quyết định logic xử lý:
                            # 1. Chấp nhận rollback (an toàn cho kho).
                            # 2. Hoặc bắt lỗi này, không rollback nhưng ghi log/thông báo lỗi.
                            # 3. Hoặc không kiểm tra stock__gte trong filter và cho phép stock âm (không khuyến khích).
                            raise IntegrityError(f"Stock adjustment failed for order {order_after_update.id}, book {item.book.pk}") # Ném lỗi để rollback transaction

                    except Exception as stock_e:
                         # Lỗi không mong muốn khác khi cập nhật stock
                        error_msg = f"Error adjusting stock for book ID {item.book.pk}: {stock_e}"
                        print(error_msg)
                        adjustment_errors.append(error_msg)
                        raise IntegrityError(f"Stock adjustment error for order {order_after_update.id}") # Rollback

            if not adjustment_errors:
                 print(f"Stock adjusted successfully for order {order_after_update.id}")
                 # Đánh dấu là đã cập nhật stock (nếu có trường stock_adjusted)
                 # order_after_update.stock_adjusted = True
                 # order_after_update.save(update_fields=['stock_adjusted'])

            # Nếu có lỗi trong quá trình cập nhật stock, transaction đã rollback rồi

        # --- Trả về thông tin đơn hàng đã cập nhật ---
        # Lấy lại dữ liệu đầy đủ để trả về (bao gồm cả items nếu muốn)
        final_order_data = _get_order_detail_data(order_after_update)

        return JsonResponse({
            'status': 'success',
            'message': f'Order {order_after_update.number} status updated successfully.',
            'order': final_order_data
        }, status=200)

    except Order.DoesNotExist: # Xảy ra nếu get_object_or_404 không tìm thấy
        return JsonResponse({'error': 'Order not found.'}, status=404)
    except IntegrityError as ie: # Bắt lỗi từ việc raise trong khối cập nhật stock
         return JsonResponse({'error': f'Failed to update order due to data inconsistency: {ie}. Status changes may have been rolled back.'}, status=409) # 409 Conflict
    except Exception as e:
        print(f"Admin Update Order Status API Error: {e}")
        import traceback; traceback.print_exc()
        return JsonResponse({'error': 'Could not update order status.'}, status=500)


# --- Helper Function để lấy chi tiết đơn hàng (có thể tách ra nếu dùng ở nhiều nơi) ---
def _get_order_detail_data(order_instance):
    """
    Lấy dữ liệu chi tiết của một Order instance, bao gồm cả thông tin sách đầy đủ (với ảnh) cho items.
    """
    # Lấy items với select_related('book__category') để format_book_data có thể lấy category_name
    items_query = OrderItem.objects.filter(order=order_instance).select_related('book__category')
    items_data = []
    for item in items_query:
        # --- SỬ DỤNG format_book_data ĐỂ LẤY THÔNG TIN SÁCH ĐẦY ĐỦ ---
        formatted_book = format_book_data(item.book) if item.book else None
        # -------------------------------------------------------------
        items_data.append({
            'order_item_id': item.id, # ID của OrderItem
            'quantity': item.quantity,
            'price_at_purchase': format_decimal(item.price_at_purchase),
            'item_total': format_decimal(item.item_total),
            'book': formatted_book # <<< Đối tượng sách đã được format (bao gồm image_url)
        })

    order_data = {
        'order_id': order_instance.id,
        'order_number': order_instance.number,
        'user_id': order_instance.user_id if order_instance.user else None, # Thêm user_id
        'user_email': order_instance.user.email if order_instance.user else "N/A (Guest or Deleted)",
        'user_name': getattr(order_instance.user, 'name', None) if order_instance.user else "N/A",
        'created_at': order_instance.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        'updated_at': order_instance.updated_at.strftime("%Y-%m-%d %H:%M:%S"),
        'total_amount': format_decimal(order_instance.total_amount),
        'status_key': order_instance.status,
        'status_display': order_instance.get_status_display(),
        'payment_status_key': order_instance.payment_status,
        'payment_status_display': order_instance.get_payment_status_display(),
        'shipping_address': order_instance.shipping_address,
        'items': items_data # <<< Giờ đây mỗi item trong danh sách này sẽ có thông tin sách đầy đủ
    }
    return order_data
@csrf_exempt # GET thường an toàn
@staff_token_required # <<< Bắt buộc: Chỉ staff mới xem được chi tiết đơn hàng bất kỳ
def admin_order_detail(request, order_id):
    """
    API (Admin): Lấy thông tin chi tiết của một đơn hàng bất kỳ.
    Yêu cầu: Token của Staff.
    Phương thức: GET
    Path param: order_id - ID của đơn hàng cần xem.
    """
    # Decorator @staff_token_required đã xác thực token và kiểm tra is_staff.
    # request.user là đối tượng staff user.

    if request.method == 'GET':
        try:
            # Lấy đơn hàng theo ID, không cần lọc theo user vì đây là admin view
            # Sử dụng select_related('user') để lấy thông tin user hiệu quả
            order = get_object_or_404(
                Order.objects.select_related('user'), # Lấy cả thông tin user
                id=order_id
            )

            # Sử dụng hàm helper để lấy dữ liệu chi tiết
            order_data = _get_order_detail_data(order)

            return JsonResponse({'status': 'success', 'order': order_data})

        except Order.DoesNotExist: # Xảy ra nếu get_object_or_404 không tìm thấy
             return JsonResponse({'error': 'Order not found.'}, status=404)
        except Exception as e:
            print(f"Admin Order Detail API Error: {e}")
            import traceback; traceback.print_exc()
            return JsonResponse({'error': 'Could not retrieve order details.'}, status=500)
    else:
        return JsonResponse({'error': 'Method not allowed, please use GET'}, status=405)

@csrf_exempt
@staff_token_required
def admin_list_users(request):
    """
    API (Admin): Liệt kê tất cả người dùng, có phân trang, tìm kiếm và lọc.
    Query params:
        - page, page_size
        - search: Theo email hoặc name.
        - type: Lọc theo type ('user', 'admin').
        - status: Lọc theo status ('active', 'inactive').
        - is_staff: Lọc theo is_staff ('true', 'false').
        - sort_by: Tiêu chí sắp xếp (mặc định: 'email').
    """
    if request.method == 'GET':
        try:
            # --- Lấy tham số ---
            try: page = int(request.GET.get('page', 1))
            except ValueError: page = 1
            try:
                page_size = min(int(request.GET.get('page_size', 10)), 50)
                if page_size <= 0: page_size = 10
            except ValueError: page_size = 10

            search_query = request.GET.get('search', '').strip()
            user_type_filter = request.GET.get('type', None)
            user_status_filter = request.GET.get('status', None) # <<< Lọc theo trường status
            is_staff_filter_str = request.GET.get('is_staff', None)
            sort_by = request.GET.get('sort_by', 'email')

            # --- Query cơ bản ---
            users_query = Users.objects.all()

            # --- Áp dụng Filter ---
            if search_query:
                users_query = users_query.filter(
                    models.Q(email__icontains=search_query) |
                    models.Q(name__icontains=search_query)
                )
            if user_type_filter:
                valid_types = [choice[0] for choice in USER_TYPE_CHOICES] # <<< Lấy từ Users model
                if user_type_filter in valid_types:
                    users_query = users_query.filter(type=user_type_filter)

            if user_status_filter: # <<< Lọc theo trường status
                valid_statuses = [choice[0] for choice in STATUS_CHOICES] # <<< Lấy từ Users model
                if user_status_filter in valid_statuses:
                    users_query = users_query.filter(status=user_status_filter)

            if is_staff_filter_str is not None:
                if is_staff_filter_str.lower() == 'true':
                    users_query = users_query.filter(is_staff=True)
                elif is_staff_filter_str.lower() == 'false':
                    users_query = users_query.filter(is_staff=False)

            # --- Áp dụng Sắp xếp ---
            valid_sort_fields_user = [
                'email', '-email', 'name', '-name', 'date_joined', '-date_joined',
                'last_login', '-last_login', 'type', '-type', 'status', '-status' # <<< Thêm status
            ]
            if sort_by in valid_sort_fields_user:
                users_query = users_query.order_by(sort_by)
            else:
                users_query = users_query.order_by('email')

            # --- Phân trang ---
            paginator = Paginator(users_query, page_size)
            try: users_page = paginator.page(page)
            except PageNotAnInteger: users_page = paginator.page(1); page = 1
            except EmptyPage:
                users_page = paginator.page(paginator.num_pages if paginator.num_pages > 0 else 1); page = users_page.number

            # --- Chuẩn bị dữ liệu ---
            users_data = []
            if users_page.object_list:
                for user in users_page.object_list:
                    users_data.append({
                        'id': user.id,
                        'email': user.email,
                        'name': user.name,
                        'type': user.type,
                        'get_type_display': user.get_type_display(),
                        'status': user.status, # <<< Hiển thị trường status
                        'get_status_display': user.get_status_display(), # <<< Lấy tên hiển thị
                        'is_active_property': user.is_active(), # <<< Kết quả từ phương thức is_active()
                        'is_staff': user.is_staff,
                        'is_superuser': user.is_superuser,
                        'date_joined': user.date_joined.strftime("%Y-%m-%d %H:%M:%S") if user.date_joined else None,
                        'last_login': user.last_login.strftime("%Y-%m-%d %H:%M:%S") if user.last_login else None,
                    })
            # --- Response ---
            data = {
                'count': paginator.count, 'num_pages': paginator.num_pages, 'current_page': page,
                'page_size': page_size, 'sort_by': sort_by,
                'search_query': search_query if search_query else None,
                'type_filter': user_type_filter,
                'status_filter': user_status_filter, # <<< Thêm vào response
                'is_staff_filter': is_staff_filter_str,
                'next_page': users_page.next_page_number() if users_page.has_next() else None,
                'previous_page': users_page.previous_page_number() if users_page.has_previous() else None,
                'results': users_data
            }
            return JsonResponse(data)
        except Exception as e:
            print(f"Admin List Users API Error: {e}")
            import traceback; traceback.print_exc()
            return JsonResponse({'error': 'Could not retrieve users list.'}, status=500)
    else:
        return JsonResponse({'error': 'Method not allowed, please use GET'}, status=405)

@csrf_exempt
@staff_token_required
@transaction.atomic
def admin_update_user(request, user_id):
    """
    API (Admin): Cập nhật thông tin và quyền của một user (trừ mật khẩu).
    Body params: name, type ('user'/'admin'), status ('active'/'inactive'), is_staff ('true'/'false' - chỉ superuser).
    """
    admin_making_change = request.user
    if request.method != 'POST': return JsonResponse({'error': 'Method not allowed, use POST'}, status=405)

    try:
        user_to_update = get_object_or_404(Users, id=user_id)
        is_self_update = (user_to_update == admin_making_change)

        # --- Kiểm tra quyền ---
        if not admin_making_change.is_superuser:
            if user_to_update.is_superuser:
                return JsonResponse({'error': 'Permission denied: Cannot modify a superuser account.'}, status=403)
            # Staff thường không được thay đổi is_staff, type thành 'admin' hoặc status của staff khác/superuser
            if 'is_staff' in request.POST or \
               (request.POST.get('type') == 'admin' and user_to_update.type != 'admin') or \
               (user_to_update.is_staff and 'status' in request.POST): # Cẩn thận hơn nếu staff sửa status của staff khác
                return JsonResponse({'error': 'Permission denied: Insufficient privileges for this operation.'}, status=403)

        updated_fields_list = []

        # Cập nhật Name
        new_name = request.POST.get('name')
        if new_name is not None and user_to_update.name != new_name:
            user_to_update.name = new_name.strip()
            updated_fields_list.append('name')

        # Cập nhật Type và is_staff (thường đi đôi với nhau)
        new_type = request.POST.get('type')
        if new_type is not None and user_to_update.type != new_type:
            valid_types = [choice[0] for choice in USER_TYPE_CHOICES]
            if new_type not in valid_types:
                return JsonResponse({'error': f"Invalid user type '{new_type}'. Valid: {', '.join(valid_types)}"}, status=400)

            # Chỉ superuser mới được thay đổi type của người khác thành/khỏi 'admin'
            if (new_type == 'admin' or user_to_update.type == 'admin') and not admin_making_change.is_superuser and not is_self_update:
                 return JsonResponse({'error': 'Permission denied: Only superusers can change admin type status.'}, status=403)

            user_to_update.type = new_type
            updated_fields_list.append('type')
            # Đồng bộ is_staff với type
            new_is_staff_from_type = (new_type == 'admin')
            if user_to_update.is_staff != new_is_staff_from_type:
                user_to_update.is_staff = new_is_staff_from_type
                updated_fields_list.append('is_staff')

        # Cập nhật is_staff trực tiếp (ưu tiên hơn nếu được gửi, chỉ superuser)
        is_staff_str = request.POST.get('is_staff')
        if is_staff_str is not None and admin_making_change.is_superuser:
            new_is_staff = is_staff_str.lower() == 'true'
            if user_to_update.is_staff != new_is_staff:
                if is_self_update and user_to_update.is_superuser and not new_is_staff:
                    return JsonResponse({'error': "Permission denied: Superuser cannot revoke their own staff status if they are the one being updated."}, status=403)

                user_to_update.is_staff = new_is_staff
                updated_fields_list.append('is_staff')
                # Đồng bộ type với is_staff
                new_type_from_staff = 'admin' if new_is_staff else 'user'
                if user_to_update.type != new_type_from_staff:
                    user_to_update.type = new_type_from_staff
                    if 'type' not in updated_fields_list: updated_fields_list.append('type')


        # Cập nhật Status (active/inactive)
        new_status_str = request.POST.get('status')
        if new_status_str is not None:
            valid_statuses = [choice[0] for choice in STATUS_CHOICES]
            if new_status_str not in valid_statuses:
                return JsonResponse({'error': f"Invalid status '{new_status_str}'. Valid: {', '.join(valid_statuses)}"}, status=400)

            if user_to_update.status != new_status_str:
                # Kiểm tra quyền khi hủy kích hoạt
                if new_status_str == 'inactive':
                    if is_self_update:
                        return JsonResponse({'error': 'Cannot deactivate your own account via this API.'}, status=403)
                    if user_to_update.is_superuser and not admin_making_change.is_superuser:
                        return JsonResponse({'error': 'Permission denied: Only superusers can deactivate other superusers.'}, status=403)

                user_to_update.status = new_status_str
                updated_fields_list.append('status')

        if updated_fields_list:
            # Loại bỏ các trường trùng lặp trước khi save
            user_to_update.save(update_fields=list(set(updated_fields_list)))
            message = f"User {user_to_update.email} updated. Fields: {', '.join(list(set(updated_fields_list)))}."
        else:
            message = f"No changes detected for user {user_to_update.email}."

        user_data_updated = {
            'id': user_to_update.id, 'email': user_to_update.email, 'name': user_to_update.name,
            'type': user_to_update.type, 'get_type_display': user_to_update.get_type_display(),
            'status': user_to_update.status, 'get_status_display': user_to_update.get_status_display(),
            'is_active_property': user_to_update.is_active(),
            'is_staff': user_to_update.is_staff, 'is_superuser': user_to_update.is_superuser
        }
        return JsonResponse({'status': 'success', 'message': message, 'user': user_data_updated}, status=200)
    except Users.DoesNotExist: return JsonResponse({'error': 'User not found.'}, status=404)
    except Exception as e:
        print(f"Admin Update User API Error: {e}"); import traceback; traceback.print_exc()
        return JsonResponse({'error': 'Could not update user information.'}, status=500)

@csrf_exempt
@staff_token_required
@transaction.atomic
def admin_reset_user_password_to_default(request, user_id):
    admin_making_change = request.user
    if request.method != 'POST': return JsonResponse({'error': 'Method not allowed, use POST'}, status=405)

    try:
        user_to_reset = get_object_or_404(Users, id=user_id)

        if not admin_making_change.is_superuser:
            if user_to_reset.is_staff or user_to_reset.is_superuser:
                return JsonResponse({'error': 'Permission denied: Only superusers can reset staff/admin passwords.'}, status=403)
        if user_to_reset == admin_making_change:
             return JsonResponse({'error': 'Cannot reset your own password via this API.'}, status=403)

        length = 12
        characters = string.ascii_letters + string.digits + string.punctuation.replace("'", "").replace('"', '').replace('\\', '') # Loại bỏ ký tự có thể gây lỗi SQL/JSON
        new_password = ''.join(random.choice(characters) for i in range(length))

        user_to_reset.set_password(new_password)
        user_to_reset.save(update_fields=['password'])

        # Trong PRODUCTION, TUYỆT ĐỐI không trả về new_password.
        # Thông báo này chỉ mang tính demo/dev.
        response_message = (
            f"Password for user {user_to_reset.email} has been reset. "
            "The new password needs to be communicated securely to the user."
        )
        if settings.DEBUG: # Chỉ thêm mật khẩu vào message nếu DEBUG=True
            response_message += f" (DEV ONLY - New Password: {new_password})"

        return JsonResponse({'status': 'success', 'message': response_message}, status=200)
    except Users.DoesNotExist: return JsonResponse({'error': 'User not found.'}, status=404)
    except Exception as e:
        print(f"Admin Reset Password API Error: {e}"); import traceback; traceback.print_exc()
        return JsonResponse({'error': 'Could not reset user password.'}, status=500)

@csrf_exempt
@staff_token_required
@transaction.atomic
def admin_book_create(request):
    """
    API (Admin): Tạo một cuốn sách mới (POST).
    Yêu cầu: Token của Staff.
    Phương thức: POST
    Body params (form-data BẮT BUỘC để tải file 'image'):
        - title, price, stock, category_id (bắt buộc)
        - description, sold (tùy chọn)
        - image (file hình ảnh, tùy chọn)
    """
    if request.method == 'POST':
        # --- Lấy dữ liệu ---
        # Dùng request.POST vì có thể có file đi kèm (form-data)
        title = request.POST.get('title')
        description = request.POST.get('description', '')
        price_str = request.POST.get('price')
        stock_str = request.POST.get('stock')
        category_id_str = request.POST.get('category_id')
        sold_str = request.POST.get('sold', '0')
        image_file = request.FILES.get('image', None)

        # --- Validation ---
        required_fields = {'title': title, 'price': price_str, 'stock': stock_str, 'category_id': category_id_str}
        missing_fields = [k for k, v in required_fields.items() if not v]
        if missing_fields:
            return JsonResponse({'error': f'Missing required fields: {", ".join(missing_fields)}'}, status=400)

        try:
            price = Decimal(price_str); stock = int(stock_str); category_id = int(category_id_str); sold = int(sold_str)
            if price < 0 or stock < 0 or sold < 0 : raise ValueError("Numeric fields cannot be negative.")
        except (ValueError, InvalidOperation):
            return JsonResponse({'error': 'Invalid number format for price, stock, sold or category ID.'}, status=400)

        try:
            category = get_object_or_404(Category, id=category_id)

            # Tạo đối tượng Books (chưa lưu)
            new_book = Books(
                title=title, description=description, price=price,
                stock=stock, category=category, sold=sold
            )
            if image_file:
                new_book.image = image_file # Gán file

            # Lưu (Cloudinary sẽ tải lên nếu image được gán)
            new_book.save()

            # Cập nhật total_books (nếu có)
            if hasattr(category, 'total_books'):
                category.total_books = Books.objects.filter(category=category).count()
                category.save(update_fields=['total_books'])

            return JsonResponse({
                'status': 'success',
                'message': 'Book created successfully.',
                'book': format_book_data(new_book) # <<< Trả về dữ liệu đã format
            }, status=201) # 201 Created

        except Category.DoesNotExist: # Từ get_object_or_404
            return JsonResponse({'error': f'Category with ID "{category_id}" not found.'}, status=400)
        except IntegrityError as e:
            return JsonResponse({'error': f'Book creation failed (e.g., duplicate title): {e}'}, status=400)
        except Exception as e:
            print(f"Admin Book Create API Error: {e}"); import traceback; traceback.print_exc()
            return JsonResponse({'error': 'Could not create book.'}, status=500)

    else: # Chỉ cho phép POST
        return JsonResponse({'error': 'Method not allowed, please use POST'}, status=405)


# --- API Cập nhật Sách (PUT/PATCH) ---
@csrf_exempt
@staff_token_required
@transaction.atomic
def admin_book_update(request, pk):
    """
    API (Admin): Cập nhật thông tin sách (PUT/PATCH).
    Ưu tiên JSON body cho PATCH/PUT không có ảnh.
    Dùng form-data nếu có gửi file ảnh.
    """
    book_to_update = get_object_or_404(Books.objects.select_related('category'), pk=pk) # <<< BIẾN ĐÚNG LÀ book_to_update
    original_category = book_to_update.category

    is_put = request.method == 'PUT'
    is_patch = request.method == 'PATCH'

    if not is_put and not is_patch:
        return HttpResponseNotAllowed(['PUT', 'PATCH'])

    data = {}
    files = request.FILES
    image_file = files.get('image', None)

    # --- Đọc dữ liệu đầu vào ---
    content_type = request.content_type or ''
    if 'application/json' in content_type and request.body:
        try: data = json.loads(request.body)
        except json.JSONDecodeError: return JsonResponse({'error': 'Invalid JSON.'}, status=400)
    elif request.POST or image_file:
        data = request.POST
    if not data and not image_file: return JsonResponse({'error': 'No data provided.'}, status=400)

    updated_fields_book = []
    category_changed = False
    new_category = None

    # --- Validation và Gán giá trị (Đọc từ `data` dictionary) ---

    # Title
    if 'title' in data or is_put: # Kiểm tra key có trong data hoặc là PUT
        new_title = data.get('title', '' if is_put else book_to_update.title).strip() # <<< SỬA: dùng book_to_update
        if is_put and not new_title: return JsonResponse({'error': 'Title is required for PUT.'}, status=400)
        if book_to_update.title != new_title:
            book_to_update.title = new_title; updated_fields_book.append('title')

    # Description
    if 'description' in data or is_put:
        new_description = data.get('description', book_to_update.description if is_patch else '') # <<< SỬA: dùng book_to_update
        if book_to_update.description != new_description:
             book_to_update.description = new_description; updated_fields_book.append('description')

    # Price
    if 'price' in data or is_put:
        price_str = data.get('price')
        if is_put and price_str is None: return JsonResponse({'error': 'Price is required for PUT.'}, status=400)
        if price_str is not None:
            try: price = Decimal(str(price_str)); assert price >= 0
            except (InvalidOperation, AssertionError, ValueError): return JsonResponse({'error': 'Invalid price format or value.'}, status=400)
            if book_to_update.price != price: book_to_update.price = price; updated_fields_book.append('price')

    # Stock
    if 'stock' in data or is_put:
        stock_str = data.get('stock')
        if is_put and stock_str is None: return JsonResponse({'error': 'Stock is required for PUT.'}, status=400)
        if stock_str is not None:
            try: stock = int(str(stock_str)); assert stock >= 0
            except (ValueError, AssertionError): return JsonResponse({'error': 'Invalid stock format or value.'}, status=400)
            if book_to_update.stock != stock: book_to_update.stock = stock; updated_fields_book.append('stock')

    # Sold
    if 'sold' in data or is_put:
        sold_str = data.get('sold')
        if is_put and sold_str is None: sold_str = '0' # Default 0 cho PUT nếu thiếu
        if sold_str is not None:
            try: sold = int(str(sold_str)); assert sold >= 0
            except (ValueError, AssertionError): return JsonResponse({'error': 'Invalid sold format or value.'}, status=400)
            if book_to_update.sold != sold: book_to_update.sold = sold; updated_fields_book.append('sold')

    # Category
    if 'category_id' in data or is_put:
        category_id_str = data.get('category_id')
        if is_put and category_id_str is None: return JsonResponse({'error': 'Category ID is required for PUT.'}, status=400)
        if category_id_str is not None:
            try: category_id = int(str(category_id_str))
            except ValueError: return JsonResponse({'error': 'Invalid category ID format.'}, status=400)
            if book_to_update.category_id != category_id:
                try: new_category = Category.objects.get(id=category_id); book_to_update.category = new_category; updated_fields_book.append('category'); category_changed=True
                except Category.DoesNotExist: return JsonResponse({'error': f'Category ID {category_id} not found.'}, status=400)

    # Image
    remove_image = data.get('remove_image')
    if image_file:
        book_to_update.image = image_file; updated_fields_book.append('image')
    elif remove_image == True or str(remove_image).lower() == 'true':
        if book_to_update.image: book_to_update.image.delete(save=False); book_to_update.image = None; updated_fields_book.append('image')

    # --- Lưu thay đổi ---
    if updated_fields_book:
        try:
            # Loại bỏ trường trùng lặp nếu có (ví dụ 'category' và 'category_id' cùng lúc)
            fields_to_save = list(set(updated_fields_book))
            book_to_update.save(update_fields=fields_to_save)
            # ... (Cập nhật total_books cho category như cũ) ...
            if category_changed:
                if original_category and hasattr(original_category,'total_books'): original_category.total_books=Books.objects.filter(category=original_category).count(); original_category.save(update_fields=['total_books'])
                if new_category and hasattr(new_category,'total_books'): new_category.total_books=Books.objects.filter(category=new_category).count(); new_category.save(update_fields=['total_books'])
        except Exception as e:
            print(f"Admin Book Update Save Error: {e}"); traceback.print_exc()
            return JsonResponse({'error': 'Could not save book updates.'}, status=500)

    return JsonResponse({
        'status': 'success',
        'message': f"Book '{book_to_update.title}' updated. Fields: {list(set(updated_fields_book)) or 'No changes'}.", # Dùng set để tránh trùng
        'book': format_book_data(book_to_update)
    })
# --- API Xóa Sách (DELETE) ---
@csrf_exempt
@staff_token_required
@transaction.atomic
def admin_book_delete(request, pk):
    """API (Admin): Xóa một cuốn sách (DELETE)."""
    book_to_delete = get_object_or_404(Books.objects.select_related('category'), pk=pk)

    if request.method == 'DELETE': # <<< KIỂM TRA PHƯƠNG THỨC DELETE
        # Kiểm tra xem sách có trong OrderItem nào không
        if OrderItem.objects.filter(book=book_to_delete).exists():
            return JsonResponse({
                'error': f"Cannot delete book '{book_to_delete.title}' as it exists in placed orders. "
                         "Consider deactivating the book instead (e.g., set stock to 0)."
            }, status=409) # 409 Conflict

        try:
            book_title = book_to_delete.title
            category_of_deleted_book = book_to_delete.category
            image_to_delete = book_to_delete.image # Lấy đối tượng ảnh trước khi xóa model

            book_to_delete.delete() # Xóa sách khỏi DB

            # Xóa ảnh trên Cloudinary (CloudinaryField thường tự làm, nhưng gọi rõ ràng nếu cần)
            if image_to_delete:
                try:
                    # CloudinaryField không cần save=False khi gọi delete trực tiếp
                    image_to_delete.delete()
                    print(f"Cloudinary image for '{book_title}' deleted.")
                except Exception as e_img_del:
                    # Ghi log lỗi xóa ảnh nhưng không nên dừng việc xóa sách
                    print(f"Warning: Error deleting Cloudinary image for '{book_title}': {e_img_del}")

            # Cập nhật total_books của category
            if category_of_deleted_book and hasattr(category_of_deleted_book, 'total_books'):
                category_of_deleted_book.total_books = Books.objects.filter(category=category_of_deleted_book).count()
                category_of_deleted_book.save(update_fields=['total_books'])

            # Trả về 204 No Content là chuẩn cho DELETE thành công không có nội dung trả về
            return JsonResponse({'status': 'success', 'message': f"Book '{book_title}' deleted successfully."}, status=200)
            # Hoặc trả về 200 OK với message nếu muốn
            # return JsonResponse({'status': 'success', 'message': f"Book '{book_title}' deleted successfully."})

        except Exception as e:
            print(f"Admin Book Delete API Error: {e}"); import traceback; traceback.print_exc()
            return JsonResponse({'error': 'Could not delete book.'}, status=500)
    else:
        return JsonResponse({'error': 'Method not allowed, please use DELETE'}, status=405)

# --- API CRUD cho Category (Admin - RESTful) ---

@csrf_exempt
@staff_token_required
def admin_category_list_create(request):
    """
    API (Admin): GET để list categories (có phân trang), POST để tạo category mới.
    Yêu cầu: Token của Staff.
    """
    # === Xử lý GET: List Categories ===
    if request.method == 'GET':
        # Test GET: GET /admin/categories/?page=1&page_size=5 + Header Auth
        try:
            # Lấy tham số phân trang
            try: page = int(request.GET.get('page', 1)); assert page > 0
            except (ValueError, AssertionError): page = 1
            try: page_size = max(1, min(int(request.GET.get('page_size', 10)), 50))
            except ValueError: page_size = 10

            # Query và sắp xếp (thêm sắp xếp theo tên để ổn định)
            categories_query = Category.objects.all().order_by('name')

            # Phân trang
            paginator = Paginator(categories_query, page_size)
            try: categories_page = paginator.page(page)
            except PageNotAnInteger: categories_page = paginator.page(1); page = 1
            except EmptyPage: categories_page = paginator.page(paginator.num_pages if paginator.num_pages > 0 else 1); page = categories_page.number

            # Chuẩn bị dữ liệu (lấy các trường cần thiết từ model)
            categories_data = []
            for cat in categories_page.object_list:
                 # Tính total_books nếu trường này null hoặc bạn muốn đảm bảo nó đúng
                 # Cách 1: Lấy giá trị lưu trữ (có thể null)
                 # total_b = cat.total_books

                 # Cách 2: Tính toán lại (chính xác hơn nhưng chậm hơn nếu nhiều category)
                 total_b = cat.books.count() # Dùng related_name 'books' từ Books.category

                 categories_data.append({
                    'id': cat.id,
                    'name': cat.name,
                    'description': cat.description,
                    'total_books': total_b # Sử dụng total_b đã tính
                 })

            # Tạo response
            data = {
                'count': paginator.count, 'num_pages': paginator.num_pages, 'current_page': page, 'page_size': page_size,
                'next_page': categories_page.next_page_number() if categories_page.has_next() else None,
                'previous_page': categories_page.previous_page_number() if categories_page.has_previous() else None,
                'results': categories_data
            }
            return JsonResponse(data)
        except Exception as e:
            print(f"Admin Category List Error: {e}"); traceback.print_exc()
            return JsonResponse({'error':'Could not retrieve category list.'}, status=500)

    # === Xử lý POST: Create Category ===
    elif request.method == 'POST':
        # Test POST: POST /admin/categories/ + Header Auth + Body (form-data: name=<tên>, description=<mô tả>?)
        # Hoặc Body (JSON): {"name": "Tên mới", "description": "Mô tả mới"}
        data = {}
        content_type = request.content_type or ''
        if 'application/json' in content_type and request.body:
             try: data = json.loads(request.body)
             except json.JSONDecodeError: return JsonResponse({'error': 'Invalid JSON.'}, status=400)
        elif request.POST: # Fallback về form-data
             data = request.POST
        else: return JsonResponse({'error': 'No data provided.'}, status=400)

        name = data.get('name', '').strip()
        description = data.get('description', '') # Lấy description từ data

        if not name:
            return JsonResponse({'error': 'Category name is required.'}, status=400)

        # Bọc trong transaction
        with transaction.atomic():
            # Kiểm tra tên đã tồn tại chưa (không phân biệt hoa thường)
            # Model Category của bạn không có unique=True, nên về lý thuyết có thể trùng tên
            # Nhưng logic nghiệp vụ thường yêu cầu tên category là duy nhất. Thêm kiểm tra ở đây.
            if Category.objects.filter(name__iexact=name).exists():
                return JsonResponse({'error': f"Category with name '{name}' already exists (case-insensitive)."}, status=400)
            try:
                # total_books không cần gán khi tạo, nên để null hoặc 0 nếu có default
                category = Category(name=name, description=description)
                category.save()

                # Chuẩn bị dữ liệu trả về
                category_data = {
                    'id': category.id,
                    'name': category.name,
                    'description': category.description,
                    'total_books': category.total_books # Lấy giá trị sau khi lưu (có thể là None hoặc default)
                }
                return JsonResponse({'status': 'success', 'message': 'Category created.', 'category': category_data}, status=201)
            except IntegrityError as e:
                 # Dù model không có unique=True, vẫn có thể có lỗi Integrity khác
                 return JsonResponse({'error': f'Could not create category due to integrity constraint: {e}'}, status=400)
            except Exception as e:
                print(f"Admin Category Create Error: {e}"); traceback.print_exc()
                return JsonResponse({'error': 'Server error during category creation.'}, status=500)
    else:
        return HttpResponseNotAllowed(['GET', 'POST'])



@csrf_exempt
@staff_token_required
@transaction.atomic
def admin_category_resource(request, pk):
    """
    API (Admin): GET detail, PATCH/PUT update, DELETE Category.
    Yêu cầu: Token của Staff.
    Path param: pk - ID của category.
    """
    try:
        # Lấy category ngay từ đầu, nếu không có sẽ raise 404
        category = get_object_or_404(Category, pk=pk)
    except Category.DoesNotExist: # Bắt lỗi rõ ràng hơn (dù get_object_or_404 đã xử lý)
        return JsonResponse({'error': f'Category with ID {pk} not found.'}, status=404)
    except Exception as e: # Bắt lỗi khác nếu có khi query
        print(f"Admin Category Resource Get Error: {e}"); traceback.print_exc()
        return JsonResponse({'error': 'Error retrieving category.'}, status=500)


    # === Xử lý GET: Category Detail ===
    if request.method == 'GET':
        # Test GET: GET /admin/categories/<pk>/ + Header Auth
        try:
            total_b = category.books.count() # Tính số sách
            category_data = {
                'id': category.id,
                'name': category.name,
                'description': category.description,
                'total_books': total_b
            }
            return JsonResponse(category_data)
        except Exception as e:
            print(f"Admin Category Detail GET Error: {e}"); traceback.print_exc()
            return JsonResponse({'error': 'Could not format category details.'}, status=500)

    # === Xử lý PATCH/PUT: Update Category ===
    elif request.method == 'PATCH' or request.method == 'PUT':
        # Test PATCH: PATCH /admin/categories/<pk>/ + Header Auth, Content-Type: application/json, Body: {"name": "New"}
        # Test PUT: PUT /admin/categories/<pk>/ + Header Auth, Content-Type: application/json, Body: {"name": "Full", "description": "Replace"}
        is_put = request.method == 'PUT'
        try:
            # ... (Logic đọc data từ JSON hoặc POST như cũ) ...
            if not request.body or 'application/json' not in (request.content_type or ''):
                 if request.POST: data = request.POST
                 else: return JsonResponse({'error':'Request body empty or invalid Content-Type (expected JSON or form-data).'}, status=400)
            else: data = json.loads(request.body)
            if not data: return JsonResponse({'error':'No data provided for update.'}, status=400)

            updated_fields = []
            # ... (Logic validate và gán giá trị cho name, description như cũ) ...
            new_name=data.get('name'); new_desc=data.get('description')
            if is_put and new_name is None: return JsonResponse({'error':'PUT requires name.'}, status=400)
            if new_name is not None:
                new_name=new_name.strip()
                if not new_name: return JsonResponse({'error':'Name cannot be empty.'}, status=400)
                if category.name != new_name:
                    if Category.objects.filter(name__iexact=new_name).exclude(pk=pk).exists(): return JsonResponse({'error':f"Another category with name '{new_name}' exists."}, status=400)
                    category.name = new_name; updated_fields.append('name')
            if is_put and new_desc is None: new_desc = ""
            if new_desc is not None:
                if category.description != new_desc: category.description = new_desc; updated_fields.append('description')

            # Lưu nếu có thay đổi
            if updated_fields:
                category.save(update_fields=updated_fields)

            # Trả về category đã cập nhật
            total_b = category.books.count() # Tính lại
            category_data = {'id':category.id, 'name':category.name, 'description':category.description, 'total_books':total_b}
            return JsonResponse({'status':'success', 'message':f"Updated fields: {updated_fields or 'None'}", 'category':category_data})

        except json.JSONDecodeError: return JsonResponse({'error': 'Invalid JSON.'}, status=400)
        except IntegrityError as e: return JsonResponse({'error': f'Update failed due to integrity constraint: {e}'}, status=400)
        except AssertionError as ae: return JsonResponse({'error': str(ae)}, status=400) # Từ assert name empty
        except Exception as e:
            print(f"Admin Category Update Error: {e}"); traceback.print_exc()
            return JsonResponse({'error':'Update failed.'}, status=500)

    # === Xử lý DELETE: Delete Category ===
    elif request.method == 'DELETE':
        # Test DELETE: DELETE /admin/categories/<pk>/ + Header Auth
        try:
            # Kiểm tra sách liên quan
            if category.books.exists():
                return JsonResponse({
                    'error': f"Cannot delete category '{category.name}' because it contains books. "
                             "Please reassign or delete the associated books first."
                }, status=409) # 409 Conflict

            category_name = category.name # Lưu lại tên để thông báo
            category.delete()

            # --- SỬA Ở ĐÂY: Trả về JSON 200 OK với thông báo ---
            return JsonResponse({
                'status': 'success',
                'message': f"Category '{category_name}' (ID: {pk}) deleted successfully."
            }, status=200)
            # -------------------------------------------------

        except Exception as e:
            print(f"Admin Category Delete Error: {e}"); traceback.print_exc()
            return JsonResponse({'error': 'Could not delete category.'}, status=500)

    else:
        # Phương thức không được hỗ trợ cho URL này
        return HttpResponseNotAllowed(['GET', 'PUT', 'PATCH', 'DELETE'])