from rest_framework import serializers, viewsets, permissions, filters
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Q
from blogs.models import Blog, Category, Tag
from accounts.models import User
from comments.models import Comment
from notifications.models import Notification


# --- Serializers ---

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'description', 'color', 'blog_count']


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['id', 'name', 'slug']


class AuthorSerializer(serializers.ModelSerializer):
    avatar = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'avatar']

    def get_avatar(self, obj):
        try:
            return obj.profile.get_avatar_url()
        except Exception:
            from django.templatetags.static import static
            return static('images/default-avatar.png')


class BlogListSerializer(serializers.ModelSerializer):
    author = AuthorSerializer(read_only=True)
    category = CategorySerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    featured_image = serializers.SerializerMethodField()

    class Meta:
        model = Blog
        fields = [
            'id', 'title', 'slug', 'author', 'category', 'tags',
            'excerpt', 'featured_image', 'views_count', 'likes_count',
            'read_time', 'published_at', 'created_at'
        ]

    def get_featured_image(self, obj):
        return obj.get_featured_image_url()


class BlogDetailSerializer(BlogListSerializer):
    class Meta(BlogListSerializer.Meta):
        fields = BlogListSerializer.Meta.fields + ['content', 'allow_comments']


class CommentSerializer(serializers.ModelSerializer):
    author = AuthorSerializer(read_only=True)

    class Meta:
        model = Comment
        fields = ['id', 'content', 'author', 'likes_count', 'created_at']

    def create(self, validated_data):
        validated_data['author'] = self.context['request'].user
        return super().create(validated_data)


# --- API Views ---

class BlogListAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        blogs = Blog.objects.filter(status='published').select_related(
            'author', 'author__profile', 'category'
        ).prefetch_related('tags')

        q = request.query_params.get('q')
        category = request.query_params.get('category')
        tag = request.query_params.get('tag')

        if q:
            blogs = blogs.filter(Q(title__icontains=q) | Q(excerpt__icontains=q))
        if category:
            blogs = blogs.filter(category__slug=category)
        if tag:
            blogs = blogs.filter(tags__slug=tag)

        blogs = blogs.filter(status='published').order_by('-published_at')[:20]
        serializer = BlogListSerializer(blogs, many=True)
        return Response({'results': serializer.data, 'count': blogs.count()})


class BlogDetailAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, slug):
        try:
            blog = Blog.objects.get(slug=slug, status='published')
        except Blog.DoesNotExist:
            return Response({'error': 'Not found'}, status=404)
        return Response(BlogDetailSerializer(blog).data)


class CommentListAPIView(APIView):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get(self, request, slug):
        try:
            blog = Blog.objects.get(slug=slug, status='published')
        except Blog.DoesNotExist:
            return Response({'error': 'Not found'}, status=404)
        comments = Comment.objects.filter(
            blog=blog, is_approved=True, parent=None
        ).select_related('author', 'author__profile')[:50]
        return Response(CommentSerializer(comments, many=True).data)

    def post(self, request, slug):
        try:
            blog = Blog.objects.get(slug=slug, status='published')
        except Blog.DoesNotExist:
            return Response({'error': 'Not found'}, status=404)
        serializer = CommentSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save(blog=blog)
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)


class CategoryListAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        categories = Category.objects.filter(is_active=True)
        return Response(CategorySerializer(categories, many=True).data)


class SearchAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        q = request.query_params.get('q', '').strip()
        if len(q) < 2:
            return Response({'results': []})
        blogs = Blog.objects.filter(
            status='published'
        ).filter(Q(title__icontains=q) | Q(excerpt__icontains=q))[:10]
        return Response({'results': BlogListSerializer(blogs, many=True).data})


class NotificationAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        notifications = Notification.objects.filter(
            recipient=request.user
        ).order_by('-created_at')[:20]
        data = [{
            'id': str(n.id),
            'type': n.notification_type,
            'title': n.title,
            'message': n.message,
            'link': n.link,
            'is_read': n.is_read,
            'created_at': n.created_at.isoformat(),
        } for n in notifications]
        return Response({'notifications': data})
