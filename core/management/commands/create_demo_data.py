from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from blogs.models import Category, Tag, Blog
from accounts.models import Profile

User = get_user_model()


class Command(BaseCommand):
    help = 'Creates demo data for BlogPlatform'

    def handle(self, *args, **kwargs):
        self.stdout.write('Creating demo data...')

        # Create admin
        admin, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@blogplatform.com',
                'first_name': 'Admin',
                'last_name': 'User',
                'role': 'admin',
                'is_superuser': True,
                'is_staff': True,
                'is_email_verified': True,
            }
        )
        if created:
            admin.set_password('Admin@1234')
            admin.save()
            Profile.objects.get_or_create(user=admin)
            self.stdout.write(f'  ✓ Admin user created: admin@blogplatform.com / Admin@1234')

        # Create moderator
        mod, created = User.objects.get_or_create(
            username='moderator',
            defaults={
                'email': 'mod@blogplatform.com',
                'first_name': 'Jane',
                'last_name': 'Moderator',
                'role': 'moderator',
                'is_email_verified': True,
            }
        )
        if created:
            mod.set_password('Mod@1234')
            mod.save()
            Profile.objects.get_or_create(user=mod)
            self.stdout.write(f'  ✓ Moderator created: mod@blogplatform.com / Mod@1234')

        # Create sample author
        author, created = User.objects.get_or_create(
            username='johndoe',
            defaults={
                'email': 'john@example.com',
                'first_name': 'John',
                'last_name': 'Doe',
                'role': 'author',
                'is_email_verified': True,
            }
        )
        if created:
            author.set_password('Author@1234')
            author.save()
            p, _ = Profile.objects.get_or_create(user=author)
            p.bio = 'Passionate developer and writer. I love exploring new technologies.'
            p.save()
            self.stdout.write(f'  ✓ Author created: john@example.com / Author@1234')

        # Categories
        cats_data = [
            ('Technology', 'fa-microchip', '#6c63ff'),
            ('Science', 'fa-flask', '#00e5ff'),
            ('Design', 'fa-palette', '#ff6b6b'),
            ('Business', 'fa-briefcase', '#f59e0b'),
            ('Health', 'fa-heartbeat', '#22c55e'),
            ('Travel', 'fa-plane', '#3b82f6'),
            ('Food', 'fa-utensils', '#ef4444'),
            ('Culture', 'fa-globe', '#8b5cf6'),
        ]
        cats = {}
        for name, icon, color in cats_data:
            cat, _ = Category.objects.get_or_create(
                name=name,
                defaults={'icon': icon, 'color': color, 'is_active': True}
            )
            cats[name] = cat
        self.stdout.write(f'  ✓ {len(cats)} categories created')

        # Tags
        tag_names = ['python', 'django', 'javascript', 'css', 'html', 'ai', 'machine-learning',
                     'react', 'design', 'ux', 'productivity', 'career', 'startup', 'remote-work', 'tutorial']
        for t in tag_names:
            Tag.objects.get_or_create(name=t)
        self.stdout.write(f'  ✓ {len(tag_names)} tags created')

        # Sample blogs
        sample_blogs = [
            {
                'title': 'Getting Started with Django REST Framework',
                'category': 'Technology',
                'excerpt': 'A comprehensive guide to building powerful APIs with Django REST Framework.',
                'content': '<h2>Introduction</h2><p>Django REST Framework (DRF) is a powerful and flexible toolkit for building Web APIs. In this tutorial, we will walk through the basics of setting up DRF and creating your first API endpoint.</p><h2>Installation</h2><p>Start by installing DRF using pip:</p><pre><code>pip install djangorestframework</code></pre><h2>Getting Started</h2><p>Add rest_framework to your INSTALLED_APPS in settings.py and you are ready to start building APIs!</p>',
                'status': 'published',
                'is_featured': True,
                'is_trending': True,
            },
            {
                'title': 'The Future of Artificial Intelligence in 2024',
                'category': 'Technology',
                'excerpt': 'Exploring how AI is transforming industries and what to expect in the coming years.',
                'content': '<h2>AI Revolution</h2><p>Artificial Intelligence has made tremendous strides in recent years. From natural language processing to computer vision, AI is now capable of performing tasks that were once thought to be exclusively human.</p><p>In this article, we explore the key trends shaping AI development and what they mean for businesses and individuals alike.</p><h2>Key Trends</h2><p>Large language models, multimodal AI, and edge computing are just some of the exciting developments defining the AI landscape today.</p>',
                'status': 'published',
                'is_featured': True,
            },
            {
                'title': 'Mastering CSS Grid Layout',
                'category': 'Design',
                'excerpt': 'Learn how to create complex, responsive layouts using CSS Grid.',
                'content': '<h2>What is CSS Grid?</h2><p>CSS Grid Layout is a two-dimensional layout system for the web. It allows you to organize content into rows and columns, and has many features that make building complex layouts straightforward.</p><h2>Basic Concepts</h2><p>A grid container is created by setting display: grid or display: inline-grid on an element. The children of that element become grid items.</p>',
                'status': 'published',
            },
            {
                'title': 'Starting a Successful Remote Business',
                'category': 'Business',
                'excerpt': 'Practical tips for launching and growing a business in the remote-first world.',
                'content': '<h2>The Remote Revolution</h2><p>The pandemic fundamentally changed how we think about work. Remote businesses that once seemed niche are now mainstream, and the tools and best practices have matured significantly.</p><p>In this guide, we share what we have learned building and scaling remote-first companies.</p>',
                'status': 'published',
            },
            {
                'title': 'My Pending Article About Python',
                'category': 'Technology',
                'excerpt': 'A pending article waiting for moderator review.',
                'content': '<p>This is a pending article that demonstrates the approval workflow.</p>',
                'status': 'pending',
            },
        ]

        for data in sample_blogs:
            cat = cats.get(data.pop('category'))
            blog, created = Blog.objects.get_or_create(
                title=data['title'],
                defaults={**data, 'author': author, 'category': cat}
            )
            if created:
                self.stdout.write(f'  ✓ Blog created: {blog.title}')

        self.stdout.write(self.style.SUCCESS('\n✅ Demo data created successfully!\n'))
        self.stdout.write('Login credentials:')
        self.stdout.write('  Admin:     admin@blogplatform.com / Admin@1234')
        self.stdout.write('  Moderator: mod@blogplatform.com / Mod@1234')
        self.stdout.write('  Author:    john@example.com / Author@1234')
