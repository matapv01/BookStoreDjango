"""
URL configuration for bookstore project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls.i18n import i18n_patterns
from django.utils.translation import gettext_lazy as _
import debug_toolbar
from main.views import (
    api_categories, api_products, api_cart,
    api_orders, api_user_profile
)

# URLs that should not be translated
urlpatterns = [
    path('i18n/', include('django.conf.urls.i18n')),  # Add URL patterns for language selection
    path('__debug__/', include(debug_toolbar.urls)),  # Debug Toolbar
    
    # API URLs
    path('api/categories/', api_categories, name='api_categories'),
    path('api/products/', api_products, name='api_products'),
    path('api/cart/', api_cart, name='api_cart'),
    path('api/orders/', api_orders, name='api_orders'),
    path('api/profile/', api_user_profile, name='api_user_profile'),
]

# URLs that should be translated
urlpatterns += i18n_patterns(
    path(_('admin/'), admin.site.urls),
    path(_('accounts/'), include('django.contrib.auth.urls')),  # Include Django auth urls
    path('', include('main.urls')),  # Keep your custom main urls
    path(_('admin-panel/'), include('admin_panel.urls')),
    prefix_default_language=False,  # Don't include default language code in URL
)

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
