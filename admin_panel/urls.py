from django.urls import path
from . import views

app_name = 'admin_panel'

urlpatterns = [
    path('', views.admin_panel_index, name='index'), # Add this line for the root path
    path('dashboard/', views.dashboard, name='dashboard'),
    path('login/', views.admin_login, name='login'),
    path('logout/', views.admin_logout, name='logout'),
    path('products/', views.product_list, name='products'),
    path('products/add/', views.add_product, name='add_product'),
    path('products/<int:pk>/edit/', views.edit_product, name='edit_product'),
    path('products/<int:pk>/delete/', views.delete_product, name='delete_product'),
    path('products/<int:pk>/toggle-status/', views.update_product_status, name='update_product_status'),
    path('products/<int:pk>/toggle-featured/', views.update_product_featured, name='update_product_featured'),
    path('categories/', views.category_list, name='categories'),
    path('categories/add/', views.add_category, name='add_category'),
    path('categories/<int:pk>/edit/', views.edit_category, name='edit_category'),
    path('categories/<int:pk>/delete/', views.delete_category, name='delete_category'),
    path('orders/', views.order_list, name='orders'),
    path('orders/<int:pk>/', views.order_detail, name='order_detail'),
    path('orders/<int:pk>/update-status/', views.update_order_status, name='update_order_status'),
    path('orders/<int:pk>/update-payment-status/', views.update_payment_status, name='update_payment_status'),
    path('users/', views.user_list, name='users'),
    path('users/add/', views.add_user, name='add_user'),
    path('users/<int:pk>/', views.user_detail, name='user_detail'),
    path('users/<int:pk>/edit/', views.edit_user, name='edit_user'),
    path('users/<int:pk>/delete/', views.delete_user, name='delete_user'),
    path('users/<int:pk>/toggle-status/', views.toggle_user_status, name='toggle_user_status'),
    path('users/<int:pk>/reset-password/', views.reset_user_password, name='reset_user_password'),
    path('settings/', views.system_settings, name='settings'),
    path('profile/', views.user_profile, name='profile'),
    path('profile/password/', views.admin_password_change, name='password_change'),
    path('notifications/', views.get_notifications, name='get_notifications'),
    path('notifications/<int:notification_id>/mark-read/', views.mark_notification_read, name='mark_notification_read'),
    path('notifications/<int:notification_id>/delete/', views.delete_notification, name='delete_notification'),
    path('notifications/mark-all-read/', views.mark_all_notifications_read, name='mark_all_notifications_read'),
]
