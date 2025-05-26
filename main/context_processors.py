from .models import Cart

def cart_items_count(request):
    """
    Context processor to return the number of items in the cart.
    """
    count = 0
    if request.user.is_authenticated:
        cart = Cart.objects.filter(user=request.user).first()
        if cart:
            count = cart.count
    return {
        'cart_items_count': count
    }

def get_settings(request):
    """
    Context processor to return system settings.
    """
    from admin_panel.models import SystemSettings
    return {
        'system_settings': SystemSettings.get_settings()
    }
