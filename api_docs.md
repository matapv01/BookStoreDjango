# BookStore API Documentation

## Base URL
```
http://127.0.0.1:8000
```

## Authentication
All authenticated endpoints require a valid session ID. The session ID is automatically set after successful login.

## Endpoints

### Authentication

#### Register
```http
POST /register/
```
Register a new user account.

**Request Body:**
```json
{
    "username": "testuser",
    "email": "test@example.com",
    "password1": "Test@123",
    "password2": "Test@123",
    "first_name": "Test",
    "last_name": "User"
}
```

**Response:**
```json
{
    "success": true,
    "message": "Registration successful"
}
```

#### Login
```http
POST /login/
Content-Type: application/json

{
    "username": "your_username",
    "password": "your_password"
}
```

**Response:**
```json
{
    "success": true,
    "message": "Login successful",
    "token": "session_id",
    "user": {
        "id": 1,
        "username": "your_username",
        "email": "your_email@example.com",
        "first_name": "Your",
        "last_name": "Name"
    }
}
```

#### Logout
```http
POST /logout/
Accept: application/json
Cookie: sessionid=your_session_id
```

**Response:**
```json
{
    "success": true,
    "message": "Logout successful"
}
```

#### Change Password
```http
POST /change-password/
Content-Type: application/json
Cookie: sessionid=your_session_id

{
    "old_password": "current_password",
    "new_password1": "new_password",
    "new_password2": "new_password"
}
```

**Response:**
```json
{
    "success": true,
    "message": "Mật khẩu đã được thay đổi thành công!"
}
```

### Categories

#### Get Categories
```http
GET /api/categories/
Accept: application/json
```

Query Parameters:
- `search`: Search by name or description
- `sort`: Sort field (name, -name, created_at, -created_at)
- `page`: Page number (default: 1)
- `page_size`: Items per page (default: 9)

Response:
```json
{
    "categories": [
        {
            "id": 1,
            "name": "Category Name",
            "slug": "category-slug",
            "description": "Category Description",
            "image": "image_url",
            "parent": {
                "id": null,
                "name": null,
                "slug": null
            },
            "total_products": 10,
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z"
        }
    ],
    "total": 100,
    "pages": 10,
    "current_page": 1,
    "page_size": 9,
    "has_next": true,
    "has_previous": false,
    "next_page": 2,
    "previous_page": null
}
```

### Products

#### Get Products
```http
GET /api/products/
Accept: application/json
```

Query Parameters:
- `category`: Filter by category slug
- `search`: Search by name or description
- `sort`: Sort field (-created_at, price, -price, name, -name)
- `page`: Page number (default: 1)
- `page_size`: Items per page (default: 6)

Response:
```json
{
    "products": [
        {
            "id": 1,
            "name": "Product Name",
            "slug": "product-slug",
            "description": "Product Description",
            "price": 100000.0,
            "discounted_price": 90000.0,
            "category": {
                "id": 1,
                "name": "Category Name",
                "slug": "category-slug"
            },
            "image": "image_url",
            "is_active": true,
            "is_featured": true,
            "stock": 100,
            "created_at": "2024-01-01T00:00:00Z"
        }
    ],
    "total": 100,
    "pages": 10,
    "current_page": 1,
    "page_size": 6,
    "has_next": true,
    "has_previous": false,
    "next_page": 2,
    "previous_page": null
}
```

### Cart

#### Get Cart
```http
GET /api/cart/
Accept: application/json
Cookie: sessionid=your_session_id
```

**Response:**
```json
{
    "cart": [
        {
            "id": 1,
            "product": {
                "id": 1,
                "name": "Product Name",
                "price": 100000.0,
                "discounted_price": 90000.0,
                "image": "image_url"
            },
            "quantity": 2,
            "total": 180000.0
        }
    ],
    "total": 180000.0
}
```

#### Add to Cart
```http
POST /api/cart/
Content-Type: application/json
Cookie: sessionid=your_session_id

{
    "product_id": 1,
    "quantity": 2
}
```

**Response:**
```json
{
    "success": true,
    "message": "Product added to cart",
    "cart_item": {
        "id": 1,
        "product_id": 1,
        "quantity": 2,
        "total": 180000.0
    }
}
```

#### Remove from Cart
```http
DELETE /api/cart/{item_id}/
Accept: application/json
Cookie: sessionid=your_session_id
```

**Response:**
```json
{
    "success": true,
    "message": "Item removed from cart"
}
```

### Orders

#### Get Orders
```http
GET /api/orders/
Accept: application/json
Cookie: sessionid=your_session_id
```

Query Parameters:
- `page`: Page number (default: 1)
- `page_size`: Items per page (default: 10)

**Response:**
```json
{
    "orders": [
        {
            "id": 1,
            "total_amount": 180000.0,
            "status": "PENDING",
            "payment_status": "Đang chờ thanh toán",
            "created_at": "2024-01-01T00:00:00Z",
            "items": [
                {
                    "product": {
                        "id": 1,
                        "name": "Product Name",
                        "price": 100000.0,
                        "discounted_price": 90000.0,
                        "image": "image_url"
                    },
                    "quantity": 2,
                    "price": 90000.0,
                    "total": 180000.0
                }
            ]
        }
    ],
    "total": 10,
    "pages": 1,
    "current_page": 1,
    "page_size": 10,
    "has_next": false,
    "has_previous": false,
    "next_page": null,
    "previous_page": null
}
```

#### Create Order
```http
POST /api/orders/
Content-Type: application/json
Cookie: sessionid=your_session_id

{
    "shipping_address": "Your Address",
    "payment_method": "COD"
}
```

**Response:**
```json
{
    "success": true,
    "message": "Order created successfully",
    "order": {
        "id": 1,
        "total_amount": 180000.0,
        "status": "PENDING",
        "created_at": "2024-01-01T00:00:00Z"
    }
}
```

### User Profile

#### Get Profile
```http
GET /api/user/profile/
Accept: application/json
Cookie: sessionid=your_session_id
```

**Response:**
```json
{
    "user": {
        "id": 1,
        "username": "your_username",
        "email": "your_email@example.com",
        "first_name": "Your",
        "last_name": "Name",
        "date_joined": "2024-01-01T00:00:00Z"
    },
    "profile": {
        "phone_number": "0123456789",
        "address": "Your Address",
        "avatar": "avatar_url"
    }
}
```

#### Update Profile
```http
PUT /api/user/profile/
Content-Type: application/json
Cookie: sessionid=your_session_id

{
    "email": "new_email@example.com",
    "first_name": "New",
    "last_name": "Name",
    "phone_number": "0987654321",
    "address": "New Address"
}
```

**Response:**
```json
{
    "success": true,
    "message": "Profile updated successfully"
}
```

## Error Responses

All endpoints may return the following error responses:

### 400 Bad Request
```json
{
    "success": false,
    "message": "Error message",
    "errors": {
        "field_name": ["Error message"]
    }
}
```

### 401 Unauthorized
```json
{
    "success": false,
    "message": "User is not authenticated"
}
```

### 403 Forbidden
```json
{
    "success": false,
    "message": "Permission denied"
}
```

### 404 Not Found
```json
{
    "success": false,
    "message": "Resource not found"
}
```

### 405 Method Not Allowed
```json
{
    "success": false,
    "message": "Method not allowed"
}
```

### 500 Internal Server Error
```json
{
    "success": false,
    "message": "Internal server error"
}
```

## Notes
- All monetary values are in VND (Vietnamese Dong)
- Dates are in ISO 8601 format
- Pagination is zero-based
- All authenticated endpoints require a valid session ID
- Session ID should be included in the Cookie header as `sessionid=your_session_id`
- Image URLs are relative to the base URL 