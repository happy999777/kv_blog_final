from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.UserDashboardView.as_view(), name='home'),
    path('my-blogs/', views.MyBlogsView.as_view(), name='my_blogs'),
    path('bookmarks/', views.BookmarksView.as_view(), name='bookmarks'),
    path('settings/', views.DashboardSettingsView.as_view(), name='settings'),
    # Admin - only accessible to staff/superuser
    path('admin/', views.AdminDashboardView.as_view(), name='admin_home'),
    path('admin/blogs/', views.AdminBlogsView.as_view(), name='admin_blogs'),
    path('admin/blogs/<slug:slug>/approve/', views.ApproveBlogView.as_view(), name='approve_blog'),
    path('admin/blogs/<slug:slug>/reject/', views.RejectBlogView.as_view(), name='reject_blog'),
    path('admin/users/', views.AdminUsersView.as_view(), name='admin_users'),
    path('admin/messages/', views.AdminMessagesView.as_view(), name='admin_contact'),
    path('admin/categories/', views.AdminCategoriesView.as_view(), name='admin_categories'),
    path('admin/comments/', views.AdminCommentsView.as_view(), name='admin_comments'),
    path('admin/settings/', views.SiteSettingsView.as_view(), name='site_settings'),
    # AJAX actions
    path('admin/blog/<int:pk>/approve/', views.ajax_approve_blog, name='ajax_approve'),
    path('admin/blog/<int:pk>/reject/', views.ajax_reject_blog, name='ajax_reject'),
    path('admin/blog/<int:pk>/delete/', views.ajax_delete_blog, name='ajax_delete'),
]
