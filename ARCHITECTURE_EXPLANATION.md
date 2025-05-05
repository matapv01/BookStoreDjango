# KIẾN TRÚC XỬ LÝ REQUEST TRONG DỰ ÁN

## 1. Hybrid Architecture

Dự án sử dụng kiến trúc hybrid, kết hợp cả:

### 1.1 API Endpoints (JSON Responses)
```python
# views.py
def book_list(request):
    books = Books.objects.all()
    data = {
        'books': list(books.values())
    }
    return JsonResponse(data, safe=False)

def add_to_cart(request, book_id):
    # ... xử lý logic
    return JsonResponse({
        'status': 'success',
        'message': f'{book.title} added to cart',
        'total': '{:.2f}'.format(order.total)
    })
```

Các endpoint này trả về JSON để:
- Frontend có thể xử lý dynamic
- Mobile apps có thể sử dụng
- AJAX calls từ templates

### 1.2 Traditional Views (Template Rendering)
```python 
def checkout(request):
    try:
        order = Order.objects.get(user=request.user, status='pending')
    except Order.DoesNotExist:
        return HttpResponse('No pending order found', status=404)

    if request.method == 'POST':
        # Xử lý checkout
        return redirect('store:order_confirmation', order_id=order.id)
    
    return render(request, 'store/checkout.html', {'order': order})
```

Các view này render template trực tiếp cho:
- Admin interface
- Form phức tạp
- Trang tĩnh

## 2. Luồng Xử Lý Request

### 2.1 API Request
```
Client -> URL -> View -> Model -> JsonResponse -> Client
```

Ví dụ add to cart:
1. Client gửi POST request tới /cart/add/
2. View function xử lý logic
3. Trả về JSON response
4. Frontend update UI

### 2.2 Template Request  
```
Client -> URL -> View -> Model -> Template -> Client
```

Ví dụ checkout:
1. Client truy cập /checkout/
2. View get order data
3. Render checkout template
4. Return HTML response

## 3. Response Format

### 3.1 API Responses
```python
# Success Response
{
    'status': 'success',
    'data': {...},
    'message': '...'
}

# Error Response  
{
    'error': 'Error message'
}
```

### 3.2 Template Responses
```python
return render(request, 'template.html', context)
# hoặc
return redirect('view_name')
```

## 4. Form Handling

### 4.1 API Forms
```python
def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if not form.is_valid():
            return JsonResponse({'error': 'Invalid data'})
        # Create user...
        return JsonResponse({'success': True})
    else:
        # Return form fields for frontend
        return JsonResponse({
            'fields': {
                'email': 'email',
                'password': 'password' 
            }
        })
```

### 4.2 Template Forms
```python
def checkout(request):
    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid():
            # Process order
            return redirect('confirmation')
    else:
        form = CheckoutForm()
    return render(request, 'checkout.html', {'form': form})
```

## 5. Authentication/Authorization

### 5.1 API Auth
```python
@login_required
def cart_api(request):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Login required'}, status=401)
    # Process cart...
```

### 5.2 Template Auth
```python  
@login_required
def profile(request):
    if not request.user.is_authenticated:
        return redirect('login')
    return render(request, 'profile.html')
```

## 6. Error Handling

### 6.1 API Errors
```python
try:
    book = Books.objects.get(id=book_id)
except Books.DoesNotExist:
    return JsonResponse(
        {'error': 'Book not found'},
        status=404
    )
```

### 6.2 Template Errors
```python
try:
    order = Order.objects.get(id=order_id)
except Order.DoesNotExist:
    messages.error(request, 'Order not found')
    return redirect('orders')
```

## 7. Lợi ích của Kiến trúc Hybrid

1. Flexibility:
- API cho frontend dynamic
- Templates cho pages phức tạp
- Dễ chuyển đổi giữa 2 loại

2. Reusability:
- API có thể dùng cho web/mobile
- Templates tái sử dụng components

3. Performance:
- API nhẹ, nhanh cho AJAX
- Templates tối ưu cho SEO

4. Development:
- Chia nhỏ logic dễ maintain
- Dễ test riêng từng phần
