from django.urls import path
from . import views

app_name = 'api'

urlpatterns = [
    path('blogs/', views.BlogListAPIView.as_view(), name='blog_list'),
    path('blogs/<slug:slug>/', views.BlogDetailAPIView.as_view(), name='blog_detail'),
    path('blogs/<slug:slug>/comments/', views.CommentListAPIView.as_view(), name='blog_comments'),
    path('categories/', views.CategoryListAPIView.as_view(), name='categories'),
    path('search/', views.SearchAPIView.as_view(), name='search'),
    path('notifications/', views.NotificationAPIView.as_view(), name='notifications'),
]
