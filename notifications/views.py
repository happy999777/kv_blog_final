from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views import View
from django.http import JsonResponse
from django.core.paginator import Paginator
from .models import Notification


@method_decorator(login_required, name='dispatch')
class NotificationListView(View):
    template_name = 'notifications/list.html'

    def get(self, request):
        notifications = Notification.objects.filter(
            recipient=request.user
        ).order_by('-created_at')
        # Mark all as read
        notifications.filter(is_read=False).update(is_read=True)
        paginator = Paginator(notifications, 20)
        page = paginator.get_page(request.GET.get('page', 1))
        return render(request, self.template_name, {'notifications': page})


@login_required
def mark_all_read(request):
    if request.method == 'POST':
        Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True)
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True})
    return redirect('notifications:list')
