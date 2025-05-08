# store/urls.py

from django.urls import path
from . import views

app_name = 'store' # Namespace for URLs

urlpatterns = [
    # Core Browsing/Viewing URLs
    path('books/best-selling/', views.best_selling_books_list, name='best_selling_books_list'),
    path('books/', views.book_list, name='book_list'), # GET: List all books
    path('books/search/', views.search_books, name='book_search'),
    path('category/<str:category_slug>/', views.book_list, name='book_list_by_category'), # GET: List books filtered by category name/slug
    path('categories/', views.category_list, name='category_list'), # GET: List categories

    path('book/<int:pk>/', views.book_detail, name='book_detail'), # GET: Details for a single book


    # Cart Management URLs
     path('cart/add/<int:book_id>/', views.add_to_cart, name='add_to_cart'),
     path('cart/', views.cart, name='cart'),
     path('cart/update/', views.update_cart, name='update_cart'),
     path('cart/remove/<int:book_id>/', views.remove_from_cart, name='remove_from_cart'),
     path('cart/clear/', views.clear_cart, name='clear_cart'),
     path('order/place/', views.place_order_from_cart, name='place_order_from_cart'),

    
    # user
    path('users/me/', views.user_profile, name='user_profile'),
    path('users/change-password/', views.change_password, name='change_password'),
    path('orders/history/', views.order_history, name='order_history'), # GET: List all orders for the user
    path('orders/<int:order_id>/', views.order_detail, name='order_detail'), # <<< (TÙY CHỌN) URL xem chi tiết đơn hàng

    path('register/', views.register, name='register'), # GET: Show required fields; POST: Register a new user
    path('login/', views.user_login, name='user_login'), # GET: Show required fields; POST: Log in a user
    path('logout/', views.user_logout, name='user_logout'), # POST: Log out the current user

    # Admin Action URLs 
    path('store/admin/login/', views.admin_login, name='admin_login'),
    path('store/admin/logout/', views.admin_logout, name='admin_logout'),

    path('store/admin/orders/pending/', views.admin_list_pending_orders, name='admin_list_pending_orders'),
    path('store/admin/orders/<int:order_id>/update-status/', views.admin_update_order_status, name='admin_update_order_status'),
    path('store/admin/orders/<int:order_id>/detail/', views.admin_order_detail, name='admin_order_detail'),

    path('store/admin/users/', views.admin_list_users, name='admin_list_users'),
    path('store/admin/users/<int:user_id>/update/', views.admin_update_user, name='admin_update_user'),
    path('store/admin/users/<int:user_id>/reset-password/', views.admin_reset_user_password_to_default, name='admin_reset_user_password_to_default'),

    # Admin Book Management
    path('store/admin/books/create/', views.admin_book_create, name='admin_book_create_post'), # POST để create
    # Hoặc có thể gộp list và create vào một URL /store/admin/books/ nếu phân biệt bằng method GET/POST
    # path('store/admin/books/', views.admin_book_combined_list_create, name='admin_book_list_create'),

    path('store/admin/books/<int:pk>/update/', views.admin_book_update, name='admin_book_update_put_patch'), # PUT/PATCH để update (toàn bộ/1 phần)
    path('store/admin/books/<int:pk>/delete/', views.admin_book_delete, name='admin_book_delete_delete'), # DELETE để xóa
    
    # Admin Category Management
    path('store/admin/categories/', views.admin_category_list_create, name='admin_category_list_create'), # GET list, POST create
    path('store/admin/categories/<int:pk>/', views.admin_category_resource, name='admin_category_resource'), # GET detail, PUT/PATCH update, DELETE delete
]    