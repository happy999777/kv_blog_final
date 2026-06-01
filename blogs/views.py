from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views import View
from django.core.paginator import Paginator
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q, F, Count
from django.utils import timezone
from django.conf import settings
from .models import Blog, Category, Tag, Like, Bookmark, BlogView
from notifications.utils import create_notification
from django.contrib.auth import get_user_model
from .forms import BlogForm
from comments.models import Comment

User = get_user_model()


class BlogListView(View):
    template_name = 'blogs/list.html'

    def get(self, request):
        blogs = Blog.objects.filter(status='published').select_related(
            'author', 'author__profile', 'category'
        ).prefetch_related('tags')

        category_slug = request.GET.get('category', '').strip()
        tag_slug = request.GET.get('tag', '').strip()
        search_q = request.GET.get('q', '').strip()
        sort = request.GET.get('sort', '-published_at')

        if category_slug:
            blogs = blogs.filter(category__slug=category_slug)

        if tag_slug:
            blogs = blogs.filter(tags__slug=tag_slug).distinct()

        if search_q:
            exact_category = Category.objects.filter(name__iexact=search_q, is_active=True).first()
            exact_tag = Tag.objects.filter(name__iexact=search_q).first()

            if exact_category and not category_slug and not tag_slug:
                blogs = blogs.filter(category=exact_category).distinct()
            elif exact_tag and not category_slug and not tag_slug:
                blogs = blogs.filter(tags=exact_tag).distinct()
            else:
                blogs = blogs.filter(
                    Q(title__icontains=search_q) |
                    Q(excerpt__icontains=search_q) |
                    Q(content__icontains=search_q) |
                    Q(category__name__icontains=search_q) |
                    Q(tags__name__icontains=search_q) |
                    Q(author__username__icontains=search_q) |
                    Q(author__first_name__icontains=search_q) |
                    Q(author__last_name__icontains=search_q)
                ).distinct()

        sort_options = {
            '-published_at': '-published_at',
            '-views_count': '-views_count',
            '-likes_count': '-likes_count',
        }
        blogs = blogs.order_by(sort_options.get(sort, '-published_at'))

        paginator = Paginator(blogs, settings.BLOGS_PER_PAGE)
        page = paginator.get_page(request.GET.get('page', 1))

        categories = Category.objects.filter(is_active=True, parent=None).annotate(
            blog_count=Count('blogs', filter=Q(blogs__status='published'))
        )

        popular_blogs = Blog.objects.filter(
            status='published'
        ).select_related('author', 'category').order_by('-views_count')[:6]

        popular_tags = Tag.objects.annotate(
            blog_count=Count('blogs', filter=Q(blogs__status='published'))
        ).filter(blog_count__gt=0).order_by('-blog_count')[:20]

        cats = Category.objects.filter(is_active=True).annotate(
            blog_count=Count('blogs', filter=Q(blogs__status='published'))
        )

        query_params = request.GET.copy()
        query_params.pop('page', None)

        return render(request, self.template_name, {
            'page_obj': page,
            'blogs': page.object_list,
            'categories': cats,
            'popular_blogs': popular_blogs,
            'popular_tags': popular_tags,
            'search_q': search_q,
            'current_category': category_slug,
            'current_tag': tag_slug,
            'sort': sort,
            'query_params': query_params.urlencode(),
        })


class BlogDetailView(View):
    template_name = 'blogs/detail.html'

    def get(self, request, slug):
        from django.http import Http404

        try:
            blog = Blog.objects.get(slug=slug, status='published')
        except Blog.DoesNotExist:
            try:
                candidate = Blog.objects.get(slug=slug)
            except Blog.DoesNotExist:
                raise Http404("No Blog matches the given query.")

            can_preview = False
            if request.user.is_authenticated:
                if candidate.author == request.user:
                    can_preview = True
                if request.user.is_staff or request.user.is_superuser:
                    can_preview = True

            if not can_preview:
                raise Http404("No Blog matches the given query.")

            blog = candidate

        ip = get_client_ip(request)
        session_key = request.session.session_key or ''

        if not BlogView.objects.filter(blog=blog, ip_address=ip).filter(
            created_at__date=timezone.now().date()
        ).exists():
            BlogView.objects.create(blog=blog, ip_address=ip, session_key=session_key)
            Blog.objects.filter(pk=blog.pk).update(views_count=F('views_count') + 1)
            blog.views_count += 1

        related = Blog.objects.filter(
            status='published', category=blog.category
        ).exclude(pk=blog.pk).order_by('-views_count')[:4]

        comments = blog.comments.filter(
            is_approved=True, parent=None
        ).select_related(
            'author', 'author__profile'
        ).prefetch_related('replies__author__profile')

        is_liked = False
        is_bookmarked = False

        if request.user.is_authenticated:
            is_liked = Like.objects.filter(user=request.user, blog=blog).exists()
            is_bookmarked = Bookmark.objects.filter(user=request.user, blog=blog).exists()

        popular_blogs = Blog.objects.filter(
            status='published'
        ).exclude(pk=blog.pk).order_by('-views_count')[:5]

        popular_tags = Tag.objects.annotate(
            blog_count=Count('blogs', filter=Q(blogs__status='published'))
        ).order_by('-blog_count')[:20]

        return render(request, self.template_name, {
            'blog': blog,
            'related_blogs': related,
            'comments': comments,
            'user_liked': is_liked,
            'user_bookmarked': is_bookmarked,
            'is_liked': is_liked,
            'is_bookmarked': is_bookmarked,
            'comment_count': blog.comments.filter(is_approved=True).count(),
            'popular_blogs': popular_blogs,
            'popular_tags': popular_tags,
        })


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0]
    return request.META.get('REMOTE_ADDR', '127.0.0.1')


@method_decorator(login_required, name='dispatch')
class BlogCreateView(View):
    template_name = 'blogs/blog_form.html'

    def get(self, request):
        form = BlogForm()
        return render(request, self.template_name, {
            'form': form,
            'title': 'Create New Blog',
            'blog': None
        })

    def post(self, request):
        form = BlogForm(request.POST, request.FILES)

        if form.is_valid():
            blog = form.save(commit=False)
            blog.author = request.user

            action = request.POST.get('action', 'pending_review')

            if action == 'draft':
                blog.status = 'draft'
                msg = 'Blog saved as draft.'
            elif action == 'published' and (
                request.user.is_superuser or getattr(request.user, 'role', '') == 'admin'
            ):
                blog.status = 'published'
                msg = 'Blog published directly.'
            else:
                blog.status = 'pending'
                msg = 'Blog submitted for review. You will be notified once approved.'

            blog.save()
            form.save_m2m()

            if blog.status == 'pending':
                staff_users = User.objects.filter(
                    Q(is_staff=True) |
                    Q(is_superuser=True) |
                    Q(role__in=['admin', 'moderator'])
                )

                for staff in staff_users.distinct():
                    if staff != request.user:
                        try:
                            create_notification(
                                recipient=staff,
                                sender=request.user,
                                notification_type='blog_submitted',
                                title='New Blog Submission',
                                message=f'"{blog.title}" submitted by {request.user.get_full_name()}',
                                link=blog.get_absolute_url()
                            )
                        except Exception:
                            pass

            messages.success(request, msg)
            return redirect('dashboard:my_blogs')

        return render(request, self.template_name, {
            'form': form,
            'title': 'Create New Blog',
            'blog': None
        })


@method_decorator(login_required, name='dispatch')
class BlogEditView(View):
    template_name = 'blogs/blog_form.html'

    def get(self, request, slug):
        blog = get_object_or_404(Blog, slug=slug)

        if blog.author != request.user and not request.user.is_staff:
            messages.error(request, 'You do not have permission to edit this blog.')
            return redirect('blogs:detail', slug=slug)

        form = BlogForm(instance=blog)

        return render(request, self.template_name, {
            'form': form,
            'title': 'Edit Blog',
            'blog': blog
        })

    def post(self, request, slug):
        blog = get_object_or_404(Blog, slug=slug)

        if blog.author != request.user and not request.user.is_staff:
            messages.error(request, 'Permission denied.')
            return redirect('blogs:detail', slug=slug)

        form = BlogForm(request.POST, request.FILES, instance=blog)

        if form.is_valid():
            blog = form.save(commit=False)

            if blog.author == request.user and blog.status == 'rejected':
                blog.status = 'pending'

            blog.save()
            form.save_m2m()

            messages.success(request, 'Blog updated successfully!')
            return redirect('dashboard:my_blogs')

        return render(request, self.template_name, {
            'form': form,
            'title': 'Edit Blog',
            'blog': blog
        })


@method_decorator(login_required, name='dispatch')
class BlogDeleteView(View):
    def post(self, request, slug):
        blog = get_object_or_404(Blog, slug=slug)

        if blog.author != request.user and not (
            request.user.is_staff or request.user.is_superuser
        ):
            messages.error(request, 'Permission denied.')
            return redirect('dashboard:my_blogs')

        blog.delete()
        messages.success(request, 'Blog deleted.')

        return redirect('dashboard:my_blogs')


class CategoryListView(View):
    template_name = 'blogs/categories_list.html'

    def get(self, request):
        categories_all = Category.objects.filter(is_active=True).annotate(
            blog_count=Count('blogs', filter=Q(blogs__status='published'))
        ).order_by('order', 'name')

        return render(request, self.template_name, {
            'categories_all': categories_all,
            'popular_tags': Tag.objects.all()[:20],
        })


class CategoryView(View):
    template_name = 'blogs/category.html'

    def get(self, request, slug):
        category = get_object_or_404(Category, slug=slug, is_active=True)

        blogs = Blog.objects.filter(
            status='published',
            category=category
        ).select_related(
            'author', 'author__profile'
        ).order_by('-published_at')

        paginator = Paginator(blogs, settings.BLOGS_PER_PAGE)
        page = paginator.get_page(request.GET.get('page', 1))

        return render(request, self.template_name, {
            'category': category,
            'blogs': page,
        })


class TagView(View):
    template_name = 'blogs/tag.html'

    def get(self, request, slug):
        tag = get_object_or_404(Tag, slug=slug)

        blogs = Blog.objects.filter(
            status='published',
            tags=tag
        ).select_related(
            'author', 'author__profile'
        ).order_by('-published_at')

        paginator = Paginator(blogs, settings.BLOGS_PER_PAGE)
        page = paginator.get_page(request.GET.get('page', 1))

        return render(request, self.template_name, {
            'tag': tag,
            'blogs': page
        })


def like_blog(request, slug):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Login required'}, status=401)

    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    blog = get_object_or_404(Blog, slug=slug, status='published')
    like, created = Like.objects.get_or_create(user=request.user, blog=blog)

    if created:
        Blog.objects.filter(pk=blog.pk).update(likes_count=F('likes_count') + 1)

        if blog.author != request.user:
            try:
                create_notification(
                    recipient=blog.author,
                    sender=request.user,
                    notification_type='like',
                    title=f'{request.user.get_full_name()} liked your blog',
                    message=f'"{blog.title}" received a new like.',
                    link=blog.get_absolute_url()
                )
            except Exception:
                pass

        return JsonResponse({
            'liked': True,
            'count': blog.likes_count + 1
        })

    like.delete()
    Blog.objects.filter(pk=blog.pk).update(likes_count=F('likes_count') - 1)

    return JsonResponse({
        'liked': False,
        'count': max(0, blog.likes_count - 1)
    })


def bookmark_blog(request, slug):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Login required'}, status=401)

    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    blog = get_object_or_404(Blog, slug=slug, status='published')
    bookmark, created = Bookmark.objects.get_or_create(user=request.user, blog=blog)

    if not created:
        bookmark.delete()
        return JsonResponse({'bookmarked': False})

    return JsonResponse({'bookmarked': True})


def ajax_search(request):
    q = request.GET.get('q', '').strip()

    if len(q) < 2:
        return JsonResponse({'results': []})

    blogs = Blog.objects.filter(
        status='published'
    ).filter(
        Q(title__icontains=q) |
        Q(excerpt__icontains=q) |
        Q(content__icontains=q) |
        Q(author__username__icontains=q) |
        Q(author__first_name__icontains=q) |
        Q(author__last_name__icontains=q) |
        Q(category__name__icontains=q) |
        Q(category__slug__icontains=q) |
        Q(tags__name__icontains=q) |
        Q(tags__slug__icontains=q)
    ).select_related(
        'author', 'category'
    ).prefetch_related('tags').distinct()[:8]

    results = [{
        'title': b.title,
        'slug': b.slug,
        'author': b.author.get_full_name() or b.author.username,
        'category': b.category.name if b.category else '',
        'image': b.get_featured_image_url(),
        'url': b.get_absolute_url(),
        'read_time': b.read_time,
    } for b in blogs]

    return JsonResponse({'results': results})


def like_blog_by_id(request, pk):
    try:
        blog = Blog.objects.get(pk=pk)
        return like_blog(request, blog.slug)
    except Blog.DoesNotExist:
        return JsonResponse({'error': 'Not found'}, status=404)


def bookmark_blog_by_id(request, pk):
    try:
        blog = Blog.objects.get(pk=pk)
        return bookmark_blog(request, blog.slug)
    except Blog.DoesNotExist:
        return JsonResponse({'error': 'Not found'}, status=404)