from django.urls import path
from . import views
from rest_framework.routers import DefaultRouter

app_name = 'main'

# Create a router and register our viewsets with it
router = DefaultRouter()

urlpatterns = [
    # Web URLs
    path('', views.home, name='home'),
    path('categories/', views.category_list, name='category_list'),
    path('categories/<slug:slug>/', views.category_detail, name='category_detail'),
    path('products/', views.product_list, name='product_list'),
    path('products/<slug:slug>/', views.product_detail, name='product_detail'),
    path('cart/', views.cart, name='cart'),
    path('cart/add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/remove/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('cart/update/<int:item_id>/', views.update_cart, name='update_cart'),
    path('checkout/', views.checkout, name='checkout'),
    path('orders/', views.order_history, name='order_history'),
    path('orders/<int:order_id>/', views.order_detail, name='order_detail'),
    path('orders/<int:order_id>/cancel/', views.cancel_order, name='cancel_order'),
    path('profile/', views.profile, name='profile'),
    path('profile/edit/', views.profile_edit, name='profile_edit'),
    path('change-password/', views.change_password, name='change_password'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register, name='register'),

    # API URLs
    path('api/categories/', views.api_categories, name='api_categories'),
    path('api/products/', views.api_products, name='api_products'),
    path('api/cart/', views.api_cart, name='api_cart'),
    path('api/orders/', views.api_orders, name='api_orders'),
    path('api/user/profile/', views.api_user_profile, name='api_user_profile'),
]

# Include router URLs
urlpatterns += router.urls
