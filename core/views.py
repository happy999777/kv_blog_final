from django.shortcuts import render, redirect
from django.views import View
from django.db.models import Sum, Count, Q
from django.http import JsonResponse
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from blogs.models import Blog, Category, Tag
from accounts.models import User


class HomeView(View):
    template_name = 'core/home.html'

    def get(self, request):
        featured_blogs = Blog.objects.filter(
            status='published', is_featured=True
        ).select_related('author', 'author__profile', 'category').order_by('-published_at')[:5]

        if not featured_blogs.exists():
            featured_blogs = Blog.objects.filter(
                status='published'
            ).select_related('author', 'author__profile', 'category').order_by('-views_count')[:5]

        recent_blogs = Blog.objects.filter(
            status='published'
        ).select_related('author', 'author__profile', 'category').order_by('-published_at')[:6]

        trending_blogs = Blog.objects.filter(
            status='published'
        ).select_related('author', 'author__profile', 'category').order_by('-views_count')[:8]

        categories = Category.objects.filter(is_active=True).order_by('name')[:8]

        featured_authors = User.objects.filter(
            is_active=True
        ).annotate(
            post_count=Count('blogs', filter=Q(blogs__status='published'))
        ).filter(post_count__gt=0).select_related('profile').order_by('-post_count')[:4]

        stats = {
            'total_blogs': Blog.objects.filter(status='published').count(),
            'total_users': User.objects.filter(is_active=True).count(),
            'total_authors': User.objects.filter(
                is_active=True
            ).annotate(pc=Count('blogs', filter=Q(blogs__status='published'))).filter(pc__gt=0).count(),
            'total_categories': Category.objects.filter(is_active=True).count(),
            'total_views': Blog.objects.filter(status='published').aggregate(t=Sum('views_count'))['t'] or 0,
        }

        return render(request, self.template_name, {
            'featured_blogs': featured_blogs,
            'recent_blogs': recent_blogs,
            'trending_blogs': trending_blogs,
            'categories': categories,
            'featured_authors': featured_authors,
            'stats': stats,
        })


class AboutView(View):
    template_name = 'core/about.html'
    def get(self, request):
        stats = {
            'total_blogs': Blog.objects.filter(status='published').count(),
            'total_authors': User.objects.filter(is_active=True).annotate(
                pc=Count('blogs', filter=Q(blogs__status='published'))).filter(pc__gt=0).count(),
            'total_views': Blog.objects.filter(status='published').aggregate(t=Sum('views_count'))['t'] or 0,
        }
        return render(request, self.template_name, {'stats': stats})


class PrivacyView(View):
    template_name = 'core/privacy.html'
    def get(self, request):
        return render(request, self.template_name)


class TermsView(View):
    template_name = 'core/terms.html'
    def get(self, request):
        return render(request, self.template_name)


class FAQView(View):
    template_name = 'core/faq.html'
    def get(self, request):
        return render(request, self.template_name)


class SitemapPageView(View):
    def get(self, request):
        blogs = Blog.objects.filter(status='published').order_by('-published_at')[:100]
        categories = Category.objects.filter(is_active=True)
        return render(request, 'core/sitemap_page.html', {'blogs': blogs, 'categories': categories})


@require_POST
def newsletter_subscribe(request):
    email = request.POST.get('email', '').strip()
    if email and '@' in email:
        # Save to newsletter list (you can add NewsletterSubscriber model)
        messages.success(request, f'🎉 Successfully subscribed with {email}!')
    else:
        messages.error(request, 'Please enter a valid email address.')
    next_url = request.META.get('HTTP_REFERER', '/')
    return redirect(next_url)


def custom_404(request, exception):
    return render(request, 'errors/404.html', status=404)


def custom_500(request):
    return render(request, 'errors/500.html', status=500)
