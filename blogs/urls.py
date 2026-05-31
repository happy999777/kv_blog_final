from django.urls import path
from . import views

app_name = 'blogs'

urlpatterns = [
    path('', views.BlogListView.as_view(), name='list'),
    path('create/', views.BlogCreateView.as_view(), name='create'),
    path('search/', views.ajax_search, name='ajax_search'),
    path('categories/', views.CategoryListView.as_view(), name='categories_list'),
    path('category/<slug:slug>/', views.CategoryView.as_view(), name='category'),
    path('tag/<slug:slug>/', views.TagView.as_view(), name='tag'),
    path('<slug:slug>/', views.BlogDetailView.as_view(), name='detail'),
    path('<slug:slug>/edit/', views.BlogEditView.as_view(), name='edit'),
    path('<slug:slug>/delete/', views.BlogDeleteView.as_view(), name='delete'),
    path('<slug:slug>/like/', views.like_blog, name='like'),
    path('<int:pk>/like/', views.like_blog_by_id, name='like_by_id'),
    path('<int:pk>/bookmark/', views.bookmark_blog_by_id, name='bookmark_by_id'),
    path('<slug:slug>/bookmark/', views.bookmark_blog, name='bookmark'),
]
