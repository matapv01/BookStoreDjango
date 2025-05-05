# GIẢI THÍCH CHI TIẾT DỰ ÁN BOOKSTORE

## 1. TỔNG QUAN DỰ ÁN

Đây là một hệ thống bán sách online với các chức năng chính:
- Quản lý người dùng (Users)
- Quản lý sách (Books)
- Giỏ hàng (Cart)
- Đơn hàng (Orders)

### Phân quyền người dùng:
1. Regular users: Người dùng bình thường
   - Đăng ký/đăng nhập
   - Xem và mua sách
   - Quản lý giỏ hàng của mình

2. Staff users: Nhân viên quản lý
   - Quản lý sách và danh mục
   - Quản lý người dùng cơ bản
   - Không thể sửa thông tin staff khác

3. Superusers: Admin tổng
   - Toàn quyền quản lý hệ thống
   - Có thể quản lý staff users

## 2. CẤU TRÚC PROJECT

### 2.1 Cấu trúc thư mục:
```
bookstore_project/
├── store/                  # App chính chứa logic
│   ├── models.py          # Định nghĩa database
│   ├── views.py           # Xử lý request
│   ├── admin.py           # Giao diện admin
│   ├── forms.py           # Form xử lý dữ liệu
│   ├── urls.py            # Định tuyến URL
│   └── tests.py           # Unit test
├── templates/             # Giao diện HTML
└── static/               # CSS, JS, images
```

### 2.2 Database Models (models.py):

1. Users: Model người dùng
```python
class Users(AbstractBaseUser):
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=100)
    type = models.CharField(choices=['user', 'admin'])
    status = models.CharField(choices=['active', 'inactive'])
    is_staff = models.BooleanField()
```

2. Category: Danh mục sách
```python
class Category(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
```

3. Books: Thông tin sách
```python
class Books(models.Model):
    title = models.CharField(max_length=200)
    category = models.ForeignKey(Category)
    price = models.DecimalField()
    stock = models.IntegerField()
    sold = models.IntegerField()
```

4. Cart & Order: Giỏ hàng và đơn hàng
```python
class Cart(models.Model):
    user = models.ForeignKey(Users)
    books = models.ManyToManyField(Books, through='CartBooks')

class Order(models.Model):
    user = models.ForeignKey(Users)
    total = models.DecimalField()
    status = models.CharField()
```

## 3. LUỒNG XỬ LÝ CHÍNH

### 3.1 Đăng ký/Đăng nhập:
1. User điền form đăng ký
2. Hệ thống kiểm tra email unique
3. Mã hóa password
4. Tạo tài khoản, chuyển đến trang login

Code mẫu (views.py):
```python
def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()
            return redirect('login')
    return JsonResponse({'error': 'Invalid data'})
```

### 3.2 Quản lý giỏ hàng:
1. Thêm sách vào giỏ
2. Kiểm tra số lượng tồn
3. Tính tổng tiền
4. Lưu vào database

Code mẫu:
```python
@login_required
def add_to_cart(request, book_id):
    book = Books.objects.get(id=book_id)
    if book.stock <= 0:
        return JsonResponse({'error': 'Out of stock'})
        
    cart, _ = Cart.objects.get_or_create(user=request.user)
    cart_item, created = CartBooks.objects.get_or_create(
        cart=cart, book=book
    )
```

### 3.3 Xử lý đơn hàng:
1. Chuyển giỏ hàng thành đơn hàng
2. Cập nhật số lượng sách
3. Xử lý thanh toán
4. Gửi xác nhận

### 3.4 Admin actions:
1. Reset password user:
```python
@staff_member_required
def admin_reset_user_password(request):
    user = Users.objects.get(id=request.GET['user_id'])
    user.set_password('default123')
    user.save()
    return redirect('admin:store_users_changelist')
```

2. Phân quyền user:
```python
@staff_member_required 
def admin_change_user_role(request):
    user = Users.objects.get(id=request.GET['user_id'])
    if request.POST['role'] == 'admin':
        user.is_staff = True
        user.type = 'admin'
    user.save()
```

## 4. TESTING

### 4.1 Test Cases Chính:
1. User Management Tests:
- Đăng ký/đăng nhập
- Reset password
- Phân quyền

2. Cart Tests:
- Thêm/xóa sách
- Tính tổng tiền
- Kiểm tra tồn kho

3. Order Tests:
- Tạo đơn hàng
- Cập nhật trạng thái
- Xử lý thanh toán

### 4.2 Mẫu Test:
```python
def test_add_to_cart(self):
    book = Books.objects.create(
        title="Test Book",
        price=100,
        stock=10
    )
    response = self.client.post(
        reverse('store:add_to_cart'),
        {'book_id': book.id}
    )
    self.assertEqual(response.status_code, 200)
    self.assertTrue(CartBooks.objects.filter(
        book=book
    ).exists())
```

## 5. API ENDPOINTS

### 5.1 Public APIs:
```
GET /books/ - Danh sách sách
GET /books/<id>/ - Chi tiết sách
POST /register/ - Đăng ký
POST /login/ - Đăng nhập
```

### 5.2 Protected APIs:
```
POST /cart/add/ - Thêm vào giỏ
POST /cart/update/ - Cập nhật giỏ
POST /checkout/ - Thanh toán
```

### 5.3 Admin APIs:
```
POST /admin/user/reset-password/ 
POST /admin/user/change-role/
```

## 6. SECURITY

1. Authentication:
- Session based auth
- Login required decorator
- Staff member required

2. Permission checks:
- User role validation
- Object level permissions
- CSRF protection

3. Password security:
- Password hashing
- Password validation
- Reset password flow

## 7. DEPLOYMENT

1. Prerequisites:
- Python 3.8+
- Django 3.2+
- Database (SQLite/PostgreSQL)

2. Setup:
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
```

3. Run server:
```bash
python manage.py runserver
```

## 8. TESTING GUIDE

1. Run all tests:
```bash
python manage.py test
```

2. Run specific tests:
```bash
python manage.py test store.tests.UserAdminTest
```

3. Test with coverage:
```bash
coverage run manage.py test
coverage report
