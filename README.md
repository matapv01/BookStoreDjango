# BookStore - Hệ thống Quản lý Nhà sách

Hệ thống quản lý nhà sách được xây dựng bằng Django, cho phép quản lý sản phẩm, đơn hàng và người dùng.

## Tính năng

- Quản lý danh mục sách
- Quản lý sản phẩm
- Quản lý đơn hàng
- Quản lý người dùng
- Phân quyền admin
- Giao diện responsive
- Tích hợp thanh toán
- Báo cáo thống kê

## Yêu cầu hệ thống

- Python 3.8+
- Django 5.1.7
- PostgreSQL (cho production)
- Các thư viện trong requirements.txt

## Cài đặt

1. Clone repository:
```bash
git clone https://github.com/your-username/bookstore.git
cd bookstore
```

2. Tạo môi trường ảo:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

3. Cài đặt dependencies:
```bash
pip install -r requirements.txt
```

4. Tạo file .env:
```bash
cp .env.example .env
# Chỉnh sửa các biến môi trường trong file .env
```

5. Chạy migrations:
```bash
python manage.py makemigrations
python manage.py migrate
```

6. Tạo superuser:
```bash
python manage.py createsuperuser
```

7. Chạy server:
```bash
python manage.py runserver
```

## Cấu trúc thư mục

```
bookstore/
├── admin_panel/        # Ứng dụng quản trị
├── main/              # Ứng dụng chính
├── static/            # File tĩnh
├── templates/         # Template HTML
├── media/            # File upload
├── manage.py
└── requirements.txt
```

## Sử dụng

1. Truy cập trang chủ: http://localhost:8000
2. Truy cập admin: http://localhost:8000/admin
3. Truy cập admin panel: http://localhost:8000/admin-panel

## Admin account: admin/123456
## User account: User1/Pass?123
## conda djangomain
## python manage.py runserver