# BookStore Admin API Documentation

## Base URL
```
http://127.0.0.1:8000/admin/api
```

## Authentication
All admin endpoints require a valid session ID and admin privileges. The session ID is automatically set after successful login.

## Endpoints

### Authentication

#### Admin Login
```http
POST /admin/login/
```
**Headers:**
- Accept: application/json
- Content-Type: application/json

**Request Body:**
```json
{
    "username": "string",
    "password": "string"
}
```

**Response:**
```json
{
    "success": true,
    "message": "Login successful",
    "token": "session_key",
    "user": {
        "id": "integer",
        "username": "string",
        "email": "string",
        "first_name": "string",
        "last_name": "string",
        "is_staff": true,
        "is_superuser": true
    }
}
```

### Categories Management

#### Get All Categories
```http
GET /admin/categories/
```
**Headers:**
- Accept: application/json
- Cookie: sessionid=session_key

**Query Parameters:**
- `search`: Search term for category name/description
- `sort`: Sort field (name, -name, created_at, -created_at)
- `page`: Page number (default: 1)
- `page_size`: Items per page (default: 20)

**Response:**
```json
{
    "categories": [
        {
            "id": 1,
            "name": "Category Name",
            "slug": "category-slug",
            "description": "Category description",
            "image": "image_url",
            "parent": {
                "id": 1,
                "name": "Parent Category",
                "slug": "parent-slug"
            },
            "total_products": 10,
            "created_at": "2024-03-20T10:00:00Z",
            "updated_at": "2024-03-20T10:00:00Z"
        }
    ],
    "total": 100,
    "pages": 5,
    "current_page": 1,
    "page_size": 20
}
```

#### Create Category
```http
POST /admin/categories/
```
**Headers:**
- Accept: application/json
- Content-Type: application/json
- Cookie: sessionid=session_key

**Request Body:**
```json
{
    "name": "New Category",
    "description": "Category description",
    "parent": 1,
    "image": "image_url"
}
```

**Response:**
```json
{
    "success": true,
    "message": "Category created successfully",
    "category": {
        "id": 1,
        "name": "New Category",
        "slug": "new-category",
        "description": "Category description",
        "image": "image_url",
        "parent": {
            "id": 1,
            "name": "Parent Category",
            "slug": "parent-slug"
        }
    }
}
```

#### Update Category
```http
PUT /admin/categories/{id}/
```
**Headers:**
- Accept: application/json
- Content-Type: application/json
- Cookie: sessionid=session_key

**Request Body:**
```json
{
    "name": "Updated Category",
    "description": "Updated description",
    "parent": 2,
    "image": "new_image_url"
}
```

**Response:**
```json
{
    "success": true,
    "message": "Category updated successfully",
    "category": {
        "id": 1,
        "name": "Updated Category",
        "slug": "updated-category",
        "description": "Updated description",
        "image": "new_image_url",
        "parent": {
            "id": 2,
            "name": "New Parent",
            "slug": "new-parent"
        }
    }
}
```

#### Delete Category
```http
DELETE /admin/categories/{id}/
```
**Headers:**
- Accept: application/json
- Cookie: sessionid=session_key

**Response:**
```json
{
    "success": true,
    "message": "Category deleted successfully"
}
```

### Products Management

#### Get All Products
```http
GET /admin/products/
```
**Headers:**
- Accept: application/json
- Cookie: sessionid=session_key

**Query Parameters:**
- `category`: Category ID to filter by
- `search`: Search term for product name/description
- `sort`: Sort field (-created_at, price, -price, name)
- `page`: Page number (default: 1)
- `page_size`: Items per page (default: 20)

**Response:**
```json
{
    "products": [
        {
            "id": 1,
            "name": "Product Name",
            "slug": "product-slug",
            "description": "Product description",
            "price": 100000.00,
            "discounted_price": 90000.00,
            "category": {
                "id": 1,
                "name": "Category Name",
                "slug": "category-slug"
            },
            "image": "image_url",
            "is_active": true,
            "is_featured": false,
            "stock": 100,
            "created_at": "2024-03-20T10:00:00Z"
        }
    ],
    "total": 100,
    "pages": 5,
    "current_page": 1,
    "page_size": 20
}
```

#### Create Product
```http
POST /admin/products/
```
**Headers:**
- Accept: application/json
- Content-Type: application/json
- Cookie: sessionid=session_key

**Request Body:**
```json
{
    "name": "New Product",
    "description": "Product description",
    "price": 100000.00,
    "discounted_price": 90000.00,
    "category": 1,
    "image": "image_url",
    "is_active": true,
    "is_featured": false,
    "stock": 100
}
```

**Response:**
```json
{
    "success": true,
    "message": "Product created successfully",
    "product": {
        "id": 1,
        "name": "New Product",
        "slug": "new-product",
        "description": "Product description",
        "price": 100000.00,
        "discounted_price": 90000.00,
        "category": {
            "id": 1,
            "name": "Category Name",
            "slug": "category-slug"
        },
        "image": "image_url",
        "is_active": true,
        "is_featured": false,
        "stock": 100
    }
}
```

#### Update Product
```http
PUT /admin/products/{id}/
```
**Headers:**
- Accept: application/json
- Content-Type: application/json
- Cookie: sessionid=session_key

**Request Body:**
```json
{
    "name": "Updated Product",
    "description": "Updated description",
    "price": 120000.00,
    "discounted_price": 100000.00,
    "category": 2,
    "image": "new_image_url",
    "is_active": true,
    "is_featured": true,
    "stock": 150
}
```

**Response:**
```json
{
    "success": true,
    "message": "Product updated successfully",
    "product": {
        "id": 1,
        "name": "Updated Product",
        "slug": "updated-product",
        "description": "Updated description",
        "price": 120000.00,
        "discounted_price": 100000.00,
        "category": {
            "id": 2,
            "name": "New Category",
            "slug": "new-category"
        },
        "image": "new_image_url",
        "is_active": true,
        "is_featured": true,
        "stock": 150
    }
}
```

#### Delete Product
```http
DELETE /admin/products/{id}/
```
**Headers:**
- Accept: application/json
- Cookie: sessionid=session_key

**Response:**
```json
{
    "success": true,
    "message": "Product deleted successfully"
}
```

### Orders Management

#### Get All Orders
```http
GET /admin/orders/
```
**Headers:**
- Accept: application/json
- Cookie: sessionid=session_key

**Query Parameters:**
- `status`: Order status filter
- `payment_status`: Payment status filter
- `date_from`: Start date (YYYY-MM-DD)
- `date_to`: End date (YYYY-MM-DD)
- `page`: Page number (default: 1)
- `page_size`: Items per page (default: 20)

**Response:**
```json
{
    "orders": [
        {
            "id": 1,
            "user": {
                "id": 1,
                "username": "username",
                "email": "user@example.com"
            },
            "total_amount": 180000.00,
            "status": "PENDING",
            "payment_status": "Đang chờ thanh toán",
            "shipping_address": "123 Test Street",
            "payment_method": "COD",
            "created_at": "2024-03-20T10:00:00Z",
            "items": [
                {
                    "product": {
                        "id": 1,
                        "name": "Product Name",
                        "price": 100000.00,
                        "discounted_price": 90000.00
                    },
                    "quantity": 2,
                    "price": 90000.00,
                    "total": 180000.00
                }
            ]
        }
    ],
    "total": 100,
    "pages": 5,
    "current_page": 1,
    "page_size": 20
}
```

#### Update Order Status
```http
PUT /admin/orders/{id}/status/
```
**Headers:**
- Accept: application/json
- Content-Type: application/json
- Cookie: sessionid=session_key

**Request Body:**
```json
{
    "status": "PROCESSING",
    "payment_status": "Đã thanh toán"
}
```

**Response:**
```json
{
    "success": true,
    "message": "Order status updated successfully",
    "order": {
        "id": 1,
        "status": "PROCESSING",
        "payment_status": "Đã thanh toán",
        "updated_at": "2024-03-20T11:00:00Z"
    }
}
```

### Users Management

#### Get All Users
```http
GET /admin/users/
```
**Headers:**
- Accept: application/json
- Cookie: sessionid=session_key

**Query Parameters:**
- `search`: Search term for username/email
- `sort`: Sort field (username, -username, date_joined, -date_joined)
- `page`: Page number (default: 1)
- `page_size`: Items per page (default: 20)

**Response:**
```json
{
    "users": [
        {
            "id": 1,
            "username": "username",
            "email": "user@example.com",
            "first_name": "First",
            "last_name": "Last",
            "is_active": true,
            "is_staff": false,
            "date_joined": "2024-03-20T10:00:00Z",
            "profile": {
                "phone_number": "1234567890",
                "address": "123 Test Street",
                "avatar": "avatar_url"
            }
        }
    ],
    "total": 100,
    "pages": 5,
    "current_page": 1,
    "page_size": 20
}
```

#### Update User
```http
PUT /admin/users/{id}/
```
**Headers:**
- Accept: application/json
- Content-Type: application/json
- Cookie: sessionid=session_key

**Request Body:**
```json
{
    "email": "updated@example.com",
    "first_name": "Updated",
    "last_name": "User",
    "is_active": true,
    "is_staff": false,
    "profile": {
        "phone_number": "1234567890",
        "address": "456 New Street"
    }
}
```

**Response:**
```json
{
    "success": true,
    "message": "User updated successfully",
    "user": {
        "id": 1,
        "username": "username",
        "email": "updated@example.com",
        "first_name": "Updated",
        "last_name": "User",
        "is_active": true,
        "is_staff": false,
        "profile": {
            "phone_number": "1234567890",
            "address": "456 New Street",
            "avatar": "avatar_url"
        }
    }
}
```

#### Delete User
```http
DELETE /admin/users/{id}/
```
**Headers:**
- Accept: application/json
- Cookie: sessionid=session_key

**Response:**
```json
{
    "success": true,
    "message": "User deleted successfully"
}
```

## Error Responses

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
- All admin endpoints require a valid session ID and admin privileges
- Image URLs are relative to the base URL 