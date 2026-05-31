from django.urls import path
from . import views

app_name = 'comments'

urlpatterns = [
    path('blog/<slug:blog_slug>/add/', views.add_comment, name='add'),
    path('blog-id/<int:blog_id>/add/', views.add_comment_by_id, name='add_by_id'),
    path('<uuid:comment_id>/like/', views.like_comment, name='like'),
    path('<uuid:comment_id>/report/', views.report_comment, name='report'),
    path('<uuid:comment_id>/delete/', views.delete_comment, name='delete'),
]
