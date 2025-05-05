from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.urls import reverse
from .models import Category, Books, Users, Order, OrderItem
from .forms import UserRegistrationForm, LoginForm
from django.http import HttpResponse, JsonResponse

def register(request):
    if request.method == 'POST':
        user_form = UserRegistrationForm(request.POST)
        if not user_form.is_valid():
            return JsonResponse({'error': 'Invalid form data'}, status=400)

        new_user = user_form.save(commit=False)
        new_user.set_password(user_form.cleaned_data['password'])
        try:
            new_user.save()
            login(request, new_user)
            return redirect('store:home')
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    else:
        form = UserRegistrationForm()
        return JsonResponse({
            'fields': {
                'name': 'text',
                'email': 'email',
                'password': 'password',
                'password2': 'password'
            }
        }, status=200)

def user_login(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if not form.is_valid():
            return JsonResponse({'error': 'Invalid form data'}, status=400)
            
        cd = form.cleaned_data
        
        try:
            user = Users.objects.get(email=cd['email'])
            if not user.is_active():
                return JsonResponse({'error': 'Account disabled'}, status=403)
        except Users.DoesNotExist:
            return JsonResponse({'error': 'Invalid credentials'}, status=400)
            
        user = authenticate(request, username=cd['email'], password=cd['password'])
        if not user:
            return JsonResponse({'error': 'Invalid credentials'}, status=400)
            
        login(request, user)
        return redirect('store:home')
    else:
        return JsonResponse({
            'fields': {
                'email': 'email',
                'password': 'password'
            }
        }, status=200)

@login_required
def user_logout(request):
    logout(request)
    return redirect('store:home')

def home(request):
    """Home page view showing featured books and categories"""
    data = {
        'categories': list(Category.objects.values()),
        'books': list(Books.objects.order_by('-id')[:6].values())
    }
    return JsonResponse(data, safe=False)

def book_list(request, category_slug=None):
    """View to show all books, optionally filtered by category"""
    books_query = Books.objects.all()
    
    if category_slug:
        category = Category.objects.get(name=category_slug)
        books_query = books_query.filter(category=category)
    
    data = {
        'books': list(books_query.values())
    }
    return JsonResponse(data, safe=False)

def book_detail(request, pk):
    """Detailed view of a single book"""
    try:
        book = Books.objects.get(pk=pk)
        data = {
            'id': book.id,
            'title': book.title,
            'description': book.description,
            'price': str(book.price),
            'category': book.category.name,
            'stock': book.stock,
            'sold': book.sold
        }
        return JsonResponse(data)
    except Books.DoesNotExist:
        return HttpResponse('Book not found', status=404)

@login_required
def add_to_cart(request, book_id):
    """Add a book to the shopping cart"""
    try:
        book = Books.objects.get(id=book_id)
        if book.stock <= 0:
            return JsonResponse(
                {'error': 'This book is out of stock'}, 
                status=400
            )
        
        current_user = request.user
        order, created = Order.objects.get_or_create(
            user=current_user,
            status='pending',
            defaults={
                'number': f'TEMP-{current_user.id}',
                'total': 0,
                'payment_status': 'unpaid'
            }
        )

        order_item, created = OrderItem.objects.get_or_create(
            order=order,
            book=book,
            defaults={'quantity': 1}
        )

        if not created:
            if order_item.quantity >= book.stock:
                return JsonResponse(
                    {'error': f'Only {book.stock} copies available'}, 
                    status=400
                )
            order_item.quantity += 1
            order_item.save()

        order.total = sum(item.book.price * item.quantity for item in order.items.all())
        order.save()

        return JsonResponse({
            'status': 'success',
            'message': f'{book.title} added to cart',
            'total': '{:.2f}'.format(order.total)
        })
    except Books.DoesNotExist:
        return JsonResponse({'error': 'Book not found'}, status=404)

@login_required
def update_cart(request):
    """Update quantity of an item in cart"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        book_id = request.POST.get('book_id')
        quantity = int(request.POST.get('quantity', 0))
        
        if quantity < 0:
            return JsonResponse({'error': 'Invalid quantity'}, status=400)

        book = Books.objects.get(id=book_id)
        if quantity > book.stock:
            return JsonResponse(
                {'error': f'Only {book.stock} copies available'},
                status=400
            )

        order = Order.objects.get(user=request.user, status='pending')
        order_item = order.items.get(book=book)
        
        if quantity == 0:
            order_item.delete()
        else:
            order_item.quantity = quantity
            order_item.save()

        order.total = sum(item.book.price * item.quantity for item in order.items.all())
        order.save()

        return JsonResponse({
            'status': 'success',
            'message': 'Cart updated',
            'total': '{:.2f}'.format(order.total)
        })
    except (Books.DoesNotExist, Order.DoesNotExist, OrderItem.DoesNotExist):
        return JsonResponse({'error': 'Item not found'}, status=404)
    except ValueError:
        return JsonResponse({'error': 'Invalid quantity'}, status=400)

@login_required
def remove_from_cart(request, book_id):
    """Remove an item from cart"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    try:
        book = Books.objects.get(id=book_id)
        order = Order.objects.get(user=request.user, status='pending')
        order_item = order.items.get(book=book)
        order_item.delete()

        order.total = sum(item.book.price * item.quantity for item in order.items.all())
        order.save()

        return JsonResponse({
            'status': 'success',
            'message': f'{book.title} removed from cart',
            'total': '{:.2f}'.format(order.total)
        })
    except (Books.DoesNotExist, Order.DoesNotExist, OrderItem.DoesNotExist):
        return JsonResponse({'error': 'Item not found'}, status=404)

@login_required
def clear_cart(request):
    """Remove all items from cart"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    try:
        order = Order.objects.get(user=request.user, status='pending')
        order.items.all().delete()
        order.total = 0
        order.save()

        return JsonResponse({
            'status': 'success',
            'message': 'Cart cleared',
            'total': '{:.2f}'.format(order.total)
        })
    except Order.DoesNotExist:
        return JsonResponse({'error': 'Cart not found'}, status=404)

@login_required
def cart(request):
    """Shopping cart view"""
    try:
        order = Order.objects.get(user=request.user, status='pending')
        items = list(order.items.all().values('book__title', 'quantity', 'book__price'))
        total = sum(item['book__price'] * item['quantity'] for item in items)
        
        data = {
            'items': items,
            'total': '{:.2f}'.format(total)
        }
        return JsonResponse(data)
    except Order.DoesNotExist:
        return JsonResponse({'items': [], 'total': '0.00'})

@login_required
def checkout(request):
    """Checkout process view"""
    try:
        order = Order.objects.get(user=request.user, status='pending')
    except Order.DoesNotExist:
        return HttpResponse('No pending order found', status=404)

    if request.method == 'POST':
        shipping_address = request.POST.get('shipping_address')
        if shipping_address:
            order.address = shipping_address
            order.status = 'processing'
            order.payment_status = 'paid'
            order.save()
            return redirect('store:order_confirmation', order_id=order.id)
        else:
            return HttpResponse('Shipping address required', status=400)

    data = {
        'order': {
            'id': order.id,
            'total': '{:.2f}'.format(order.total),
            'items': list(order.items.all().values('book__title', 'quantity', 'book__price'))
        }
    }
    return JsonResponse(data)

@login_required
def order_confirmation(request, order_id):
    """Order confirmation view"""
    try:
        order = Order.objects.get(id=order_id, user=request.user)
        data = {
            'order_number': order.number,
            'total': '{:.2f}'.format(order.total),
            'status': order.status,
            'payment_status': order.payment_status
        }
        return JsonResponse(data)
    except Order.DoesNotExist:
        return HttpResponse('Order not found', status=404)

@staff_member_required
def admin_reset_user_password(request):
    """Admin view to reset user password"""
    user_id = request.GET.get('user_id')
    if not user_id:
        return JsonResponse({'error': 'User ID required'}, status=400)
    
    try:
        user = Users.objects.get(id=user_id)
        # Don't allow non-superusers to reset staff passwords
        if user.is_staff and not request.user.is_superuser:
            return JsonResponse({'error': 'Permission denied'}, status=403)
        
        user.set_password('default123')
        user.save()
        messages.success(request, f'Password reset for user {user.email}')
        return redirect('admin:store_users_changelist')
    except Users.DoesNotExist:
        return JsonResponse({'error': 'User not found'}, status=404)

@staff_member_required
def admin_change_user_role(request):
    """Admin view to change user role"""
    user_id = request.GET.get('user_id')
    new_role = request.POST.get('role')
    
    if not user_id or not new_role:
        return JsonResponse({'error': 'User ID and role required'}, status=400)
    
    if new_role not in ['user', 'admin']:
        return JsonResponse({'error': 'Invalid role'}, status=400)
        
    try:
        user = Users.objects.get(id=user_id)
        # Only superusers can modify staff status
        if (user.is_staff or new_role == 'admin') and not request.user.is_superuser:
            return JsonResponse({'error': 'Permission denied'}, status=403)
            
        user.type = new_role
        user.is_staff = (new_role == 'admin')
        user.save()
        
        messages.success(request, f'Role updated for user {user.email}')
        return redirect('admin:store_users_changelist')
    except Users.DoesNotExist:
        return JsonResponse({'error': 'User not found'}, status=404)
