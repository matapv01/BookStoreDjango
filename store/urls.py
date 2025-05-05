from django.urls import path
from . import views

app_name = 'store'

urlpatterns = [
    path('', views.home, name='home'),
    path('books/', views.book_list, name='book_list'),
    # Changed category filter from slug to name to match view logic based on ERD model
    path('category/<str:category_slug>/', views.book_list, name='book_list_by_category'),
    # Changed book detail from slug to pk
    path('book/<int:pk>/', views.book_detail, name='book_detail'),
    # Removed author_detail URL as the view was removed
    path('cart/add/<int:book_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/', views.cart, name='cart'),
    path('cart/update/', views.update_cart, name='update_cart'),
    path('cart/remove/<int:book_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('cart/clear/', views.clear_cart, name='clear_cart'),
    path('checkout/', views.checkout, name='checkout'),
    path('order/confirmation/<int:order_id>/', views.order_confirmation, name='order_confirmation'),

    # Authentication URLs
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),

    # Admin actions
    path('store/admin/user/reset-password/', views.admin_reset_user_password, name='admin_reset_user_password'),
    path('store/admin/user/change-role/', views.admin_change_user_role, name='admin_change_user_role'),
]
