from .models import Notification

def notifications(request):
    """
    Context processor to return notifications for the current user.
    """
    if request.user.is_authenticated and (request.user.is_staff or request.user.is_superuser):
        notifications = Notification.objects.filter(is_read=False).order_by('-created_at')[:5]
        unread_count = Notification.objects.filter(is_read=False).count()
        return {
            'notifications': notifications,
            'unread_notifications_count': unread_count
        }
    return {
        'notifications': [],
        'unread_notifications_count': 0
    } 