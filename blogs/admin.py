from django.contrib import admin
from .models import Blog, Category, Tag, Like, Bookmark, BlogView, BlogImage


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'parent', 'is_active', 'order']
    list_editable = ['is_active', 'order']
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name']


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Blog)
class BlogAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'category', 'status', 'is_featured', 'views_count', 'created_at']
    list_filter = ['status', 'category', 'is_featured', 'is_trending']
    list_editable = ['status', 'is_featured']
    search_fields = ['title', 'author__username', 'author__email']
    prepopulated_fields = {'slug': ('title',)}
    raw_id_fields = ['author', 'category', 'reviewed_by']
    readonly_fields = ['views_count', 'likes_count', 'created_at', 'updated_at']
    date_hierarchy = 'created_at'
    filter_horizontal = ['tags']

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('author', 'category')


admin.site.register(Like)
admin.site.register(Bookmark)
