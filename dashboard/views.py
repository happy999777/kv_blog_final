from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.decorators import method_decorator
from django.views import View
from django.contrib import messages
from django.db.models import Count, Q
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.utils import timezone
from datetime import timedelta
from accounts.models import User
from blogs.models import Blog, Category, Bookmark
from comments.models import Comment
from contact.models import ContactMessage
from notifications.models import Notification
from notifications.utils import create_notification
from analytics.models import ActivityLog, SiteStatistic
import json


def moderator_required(view_func):
    from functools import wraps
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_moderator:
            messages.error(request, 'Access denied.')
            return redirect('core:home')
        return view_func(request, *args, **kwargs)
    return wrapper


@method_decorator(login_required, name='dispatch')
class UserDashboardView(View):
    template_name = 'dashboard/user_dashboard.html'

    def get(self, request):
        user = request.user
        my_blogs = Blog.objects.filter(author=user)
        stats = {
            'total': my_blogs.count(),
            'published': my_blogs.filter(status='published').count(),
            'pending': my_blogs.filter(status='pending').count(),
            'rejected': my_blogs.filter(status='rejected').count(),
            'draft': my_blogs.filter(status='draft').count(),
            'total_views': sum(my_blogs.values_list('views_count', flat=True)),
            'total_likes': sum(my_blogs.values_list('likes_count', flat=True)),
        }
        recent_blogs = my_blogs.select_related('category').order_by('-created_at')[:5]
        recent_notifications = Notification.objects.filter(
            recipient=user
        ).order_by('-created_at')[:5]

        return render(request, self.template_name, {
            'stats': stats,
            'recent_blogs': recent_blogs,
            'notifications': recent_notifications,
            'pending_count': my_blogs.filter(status='pending').count(),
            'active_page': 'home',
        })


@method_decorator(login_required, name='dispatch')
class MyBlogsView(View):
    template_name = 'dashboard/my_blogs.html'

    def get(self, request):
        status_filter = request.GET.get('status', 'all')
        sort_by = request.GET.get('sort', 'date')  # date, views, likes
        blogs = Blog.objects.filter(author=request.user).select_related('category')
        
        if status_filter != 'all':
            blogs = blogs.filter(status=status_filter)
        
        # Apply sorting based on the sort parameter
        if sort_by == 'views':
            blogs = blogs.order_by('-views_count')
        elif sort_by == 'likes':
            blogs = blogs.order_by('-likes_count')
        else:  # default to date
            blogs = blogs.order_by('-created_at')
        
        paginator = Paginator(blogs, 10)
        page = paginator.get_page(request.GET.get('page', 1))
        return render(request, self.template_name, {
            'blogs': page,
            'status_filter': status_filter,
            'sort_by': sort_by,
            'status_choices': [
                ('all', 'All', Blog.objects.filter(author=request.user).count()),
                ('draft', 'Draft', Blog.objects.filter(author=request.user, status='draft').count()),
                ('pending', 'Pending', Blog.objects.filter(author=request.user, status='pending').count()),
                ('published', 'Published', Blog.objects.filter(author=request.user, status='published').count()),
                ('rejected', 'Rejected', Blog.objects.filter(author=request.user, status='rejected').count()),
            ],
        })


@method_decorator(login_required, name='dispatch')
class BookmarksView(View):
    template_name = 'dashboard/bookmarks.html'

    def get(self, request):
        bookmarks = Bookmark.objects.filter(
            user=request.user
        ).select_related('blog', 'blog__author', 'blog__category').order_by('-created_at')
        paginator = Paginator(bookmarks, 9)
        page = paginator.get_page(request.GET.get('page', 1))
        return render(request, self.template_name, {'bookmarks': page})


# ---- ADMIN DASHBOARD ----

@method_decorator([login_required, moderator_required], name='dispatch')
class AdminDashboardView(View):
    template_name = 'dashboard/home.html'

    def get(self, request):
        # Stats
        stats = {
            'total_users': User.objects.count(),
            'total_blogs': Blog.objects.count(),
            'pending_blogs': Blog.objects.filter(status='pending').count(),
            'approved_blogs': Blog.objects.filter(status='published').count(),
            'rejected_blogs': Blog.objects.filter(status='rejected').count(),
            'total_comments': Comment.objects.count(),
            'new_messages': ContactMessage.objects.filter(status='new').count(),
        }

        print(f"DEBUG Admin Dashboard: Pending blogs count from query: {stats['pending_blogs']}")
        # Let's also check what actual pending blogs we're getting
        pending_blog_list = Blog.objects.filter(status='pending').select_related(
            'author', 'author__profile', 'category'
        ).order_by('-created_at')[:8]
        print(f"DEBUG Admin Dashboard: Number of pending blogs in list: {len(pending_blog_list)}")
        for i, blog in enumerate(pending_blog_list):
            print(f"DEBUG Admin Dashboard: Pending blog {i}: {blog.title} (status: {blog.status})")

        # Chart data - last 7 days
        days = []
        blog_data = []
        user_data = []
        for i in range(6, -1, -1):
            day = timezone.now().date() - timedelta(days=i)
            days.append(day.strftime('%b %d'))
            blog_data.append(Blog.objects.filter(created_at__date=day).count())
            user_data.append(User.objects.filter(date_joined__date=day).count())

        chart_data = {
            'labels': days,
            'blogs': blog_data,
            'users': user_data,
        }

        # Recent pending blogs
        pending_blogs = Blog.objects.filter(status='pending').select_related(
            'author', 'author__profile', 'category'
        ).order_by('-created_at')[:8]

        # Recent users
        recent_users = User.objects.order_by('-date_joined')[:5]

        # Activity logs
        logs = ActivityLog.objects.select_related('user').order_by('-created_at')[:10]

        # Also build blog-per-month chart for our template
        months_labels, months_values = [], []
        for i in range(6, -1, -1):
            d = (timezone.now().replace(day=1) - timedelta(days=i*28)).replace(day=1)
            months_labels.append(d.strftime('%b'))
            months_values.append(Blog.objects.filter(
                created_at__year=d.year, created_at__month=d.month
            ).count())

        all_stats = {
            **stats,
            'total_views': Blog.objects.aggregate(v=__import__('django.db.models', fromlist=['Sum']).Sum('views_count'))['v'] or 0,
            'total_likes': Blog.objects.count(),
            'blogs_this_month': Blog.objects.filter(created_at__month=timezone.now().month).count(),
        }

        return render(request, self.template_name, {
            'stats': all_stats,
            'chart_data': json.dumps(chart_data),
            'chart_labels': json.dumps(months_labels),
            'chart_values': json.dumps(months_values),
            'views_labels': json.dumps(days[-7:]),
            'views_values': json.dumps(blog_data[-7:]),
            'pending_blogs': pending_blogs,
            'recent_blogs': pending_blogs,
            'recent_users': recent_users,
            'activity_logs': logs,
            'active_page': 'admin_home',
            'admin_pending': stats['pending_blogs'],
        })


@method_decorator([login_required, moderator_required], name='dispatch')
class AdminBlogsView(View):
    template_name = 'dashboard/admin_blogs.html'

    def get(self, request):
        status_filter = request.GET.get('status', 'pending')
        search = request.GET.get('q', '')
        blogs = Blog.objects.select_related('author', 'author__profile', 'category')
        if status_filter != 'all':
            blogs = blogs.filter(status=status_filter)
        if search:
            blogs = blogs.filter(Q(title__icontains=search) | Q(author__username__icontains=search))
        blogs = blogs.order_by('-created_at')
        paginator = Paginator(blogs, 15)
        page = paginator.get_page(request.GET.get('page', 1))
        return render(request, self.template_name, {
            'blogs': page,
            'status_filter': status_filter,
            'search': search,
        })


@method_decorator([login_required, moderator_required], name='dispatch')
class ApproveBlogView(View):
    def post(self, request, slug):
        blog = get_object_or_404(Blog, slug=slug)
        print(f"DEBUG Approve: Blog status before approve: {blog.status}")
        blog.status = 'published'
        blog.reviewed_by = request.user
        blog.reviewed_at = timezone.now()
        blog.save()
        print(f"DEBUG Approve: Blog status after approve: {blog.status}")
        create_notification(
            recipient=blog.author,
            sender=request.user,
            notification_type='blog_approved',
            title='Your blog has been approved!',
            message=f'"{blog.title}" is now live on BlogPlatform.',
            link=blog.get_absolute_url()
        )
        ActivityLog.objects.create(
            user=request.user, action='blog_approve',
            description=f'Approved blog: {blog.title}'
        )
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'status': 'published'})
        messages.success(request, f'Blog "{blog.title}" approved successfully.')
        return redirect('dashboard:admin_blogs')


@method_decorator([login_required, moderator_required], name='dispatch')
class RejectBlogView(View):
    def post(self, request, slug):
        blog = get_object_or_404(Blog, slug=slug)
        print(f"DEBUG Reject: Blog status before reject: {blog.status}")
        reason = request.POST.get('reason', 'Does not meet our guidelines.')
        blog.status = 'rejected'
        blog.rejection_reason = reason
        blog.reviewed_by = request.user
        blog.reviewed_at = timezone.now()
        blog.save()
        print(f"DEBUG Reject: Blog status after reject: {blog.status}")
        create_notification(
            recipient=blog.author,
            sender=request.user,
            notification_type='blog_rejected',
            title='Your blog was not approved',
            message=f'"{blog.title}" was rejected. Reason: {reason}',
            link='/dashboard/'
        )
        ActivityLog.objects.create(
            user=request.user, action='blog_reject',
            description=f'Rejected blog: {blog.title}'
        )
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'status': 'rejected'})
        messages.warning(request, f'Blog "{blog.title}" rejected.')
        return redirect('dashboard:admin_blogs')


@method_decorator([login_required, moderator_required], name='dispatch')
class AdminUsersView(View):
    template_name = 'dashboard/admin_users.html'

    def get(self, request):
        search = request.GET.get('q', '')
        role = request.GET.get('role', '')
        users = User.objects.annotate(post_count=Count('blogs')).select_related('profile')
        if search:
            users = users.filter(Q(username__icontains=search) | Q(email__icontains=search))
        if role:
            users = users.filter(role=role)
        users = users.order_by('-date_joined')
        paginator = Paginator(users, 20)
        page = paginator.get_page(request.GET.get('page', 1))
        return render(request, self.template_name, {
            'users': page, 'search': search, 'role': role
        })


@method_decorator([login_required, moderator_required], name='dispatch')
class AdminMessagesView(View):
    template_name = 'dashboard/admin_messages.html'

    def get(self, request):
        messages_list = ContactMessage.objects.order_by('-created_at')
        paginator = Paginator(messages_list, 15)
        page = paginator.get_page(request.GET.get('page', 1))
        return render(request, self.template_name, {'messages_list': page})


@method_decorator([login_required, moderator_required], name='dispatch')
class AdminCategoriesView(View):
    template_name = 'dashboard/admin_categories.html'

    def get(self, request):
        categories = Category.objects.annotate(
            blog_count=Count('blogs', filter=Q(blogs__status='published'))
        ).order_by('order', 'name')
        return render(request, self.template_name, {'categories': categories})


@method_decorator([login_required, moderator_required], name='dispatch')
class AdminCommentsView(View):
    template_name = 'dashboard/admin_comments.html'

    def get(self, request):
        is_spam = request.GET.get('spam', '')
        comments = Comment.objects.select_related('author', 'blog').order_by('-created_at')
        if is_spam == '1':
            comments = comments.filter(is_spam=True)
        paginator = Paginator(comments, 20)
        page = paginator.get_page(request.GET.get('page', 1))
        return render(request, self.template_name, {'comments': page})


# ---- AJAX ACTIONS ----

@login_required
def ajax_approve_blog(request, pk):
    if not request.method == 'POST':
        return JsonResponse({'success': False})
    if not request.user.is_moderator:
        return JsonResponse({'success': False, 'error': 'Permission denied'})
    try:
        blog = Blog.objects.get(pk=pk)
        print(f"DEBUG AJAX Approve: Blog status before approve: {blog.status}")
        blog.status = 'published'
        blog.approved_by = request.user
        if not blog.published_at:
            from django.utils import timezone
            blog.published_at = timezone.now()
        blog.save()
        print(f"DEBUG AJAX Approve: Blog status after approve: {blog.status}")
        create_notification(blog.author, request.user, 'blog_approved', blog)
        return JsonResponse({'success': True, 'message': f'"{blog.title}" approved successfully!'})
    except Blog.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Blog not found'})


@login_required
def ajax_reject_blog(request, pk):
    if not request.method == 'POST':
        return JsonResponse({'success': False})
    if not request.user.is_moderator:
        return JsonResponse({'success': False, 'error': 'Permission denied'})
    try:
        blog = Blog.objects.get(pk=pk)
        print(f"DEBUG AJAX Reject: Blog status before reject: {blog.status}")
        blog.status = 'rejected'
        blog.save()
        print(f"DEBUG AJAX Reject: Blog status after reject: {blog.status}")
        create_notification(blog.author, request.user, 'blog_rejected', blog)
        return JsonResponse({'success': True, 'message': f'"{blog.title}" rejected.'})
    except Blog.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Blog not found'})


@login_required
def ajax_delete_blog(request, pk):
    if not request.method == 'POST':
        return JsonResponse({'success': False})
    try:
        blog = Blog.objects.get(pk=pk)
        if blog.author != request.user and not request.user.is_staff:
            return JsonResponse({'success': False, 'error': 'Permission denied'})
        title = blog.title
        blog.delete()
        return JsonResponse({'success': True, 'message': f'"{title}" deleted.'})
    except Blog.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Blog not found'})


@method_decorator(login_required, name='dispatch')
class DashboardSettingsView(View):
    template_name = 'dashboard/settings.html'

    def get(self, request):
        return render(request, self.template_name, {'active_page': 'settings'})

    def post(self, request):
        user = request.user
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.email = request.POST.get('email', user.email)
        user.save()
        if hasattr(user, 'profile'):
            profile = user.profile
            profile.bio = request.POST.get('bio', profile.bio)
            profile.title = request.POST.get('title', profile.title)
            if 'avatar' in request.FILES:
                profile.avatar = request.FILES['avatar']
            profile.save()
        messages.success(request, 'Profile updated successfully!')
        return redirect('dashboard:settings')


@method_decorator([login_required, moderator_required], name='dispatch')
class SiteSettingsView(View):
    template_name = 'dashboard/site_settings.html'

    def get(self, request):
        return render(request, self.template_name, {'active_page': 'site_settings'})

    def post(self, request):
        messages.success(request, 'Settings saved successfully!')
        return redirect('dashboard:site_settings')
