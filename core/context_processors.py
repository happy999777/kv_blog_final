from blogs.models import Category, Tag, Blog
from django.conf import settings
from django.db.models import Count, Q


def global_context(request):
    nav_categories = Category.objects.filter(is_active=True).order_by('name')[:8]
    footer_categories = Category.objects.filter(is_active=True).order_by('name')[:12]

    unread_notification_count = 0
    if request.user.is_authenticated:
        try:
            unread_notification_count = request.user.notifications.filter(is_read=False).count()
        except Exception:
            pass

    return {
        'site_name': getattr(settings, 'SITE_NAME', 'KV Blog'),
        'site_tagline': getattr(settings, 'SITE_TAGLINE', 'Where Great Ideas Take Flight'),
        'nav_categories': nav_categories,
        'footer_categories': footer_categories,
        'unread_notification_count': unread_notification_count,
    }
