from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import F
from django.views.decorators.http import require_POST
from .models import Comment, CommentLike, CommentReport
from blogs.models import Blog
from notifications.utils import create_notification
from django.templatetags.static import static


def get_avatar_url(user):
    try:
        if hasattr(user, 'profile') and user.profile.avatar:
            if user.profile.avatar.storage.exists(user.profile.avatar.name):
                return user.profile.avatar.url
    except Exception:
        pass
    return static('images/default-avatar.png')


@login_required
@require_POST
def add_comment(request, blog_slug):
    try:
        blog = get_object_or_404(Blog, slug=blog_slug, status='published')
    except Exception:
        return JsonResponse({'error': 'Blog not found'}, status=404)

    if not blog.allow_comments:
        return JsonResponse({'error': 'Comments are disabled for this post.'}, status=403)

    content = request.POST.get('content', '').strip()
    parent_id = request.POST.get('parent_id', '').strip()

    if not content:
        return JsonResponse({'error': 'Comment cannot be empty.'}, status=400)

    parent = None
    if parent_id:
        try:
            parent = Comment.objects.get(id=parent_id, blog=blog)
        except (Comment.DoesNotExist, ValueError):
            pass

    try:
        comment = Comment.objects.create(
            blog=blog,
            author=request.user,
            content=content,
            parent=parent,
        )
    except Exception as e:
        return JsonResponse({'error': 'Failed to save comment. Please try again.'}, status=500)

    # Notify blog author
    try:
        if blog.author != request.user:
            create_notification(
                recipient=blog.author,
                sender=request.user,
                notification_type='comment',
                title='New comment on your blog',
                message=f'{request.user.get_full_name() or request.user.username} commented on "{blog.title}"',
                link=blog.get_absolute_url() + '#comments'
            )

        # Notify parent comment author if reply
        if parent and parent.author != request.user:
            create_notification(
                recipient=parent.author,
                sender=request.user,
                notification_type='reply',
                title='New reply to your comment',
                message=f'{request.user.get_full_name() or request.user.username} replied to your comment on "{blog.title}"',
                link=blog.get_absolute_url() + '#comments'
            )
    except Exception:
        pass

    return JsonResponse({
        'success': True,
        'comment': {
            'id': str(comment.id),
            'content': comment.content,
            'author': comment.author.get_full_name() or comment.author.username,
            'avatar': get_avatar_url(request.user),
            'created_at': comment.created_at.strftime('%b %d, %Y'),
            'is_reply': comment.is_reply,
        }
    })


@login_required
@require_POST
def like_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id, is_approved=True)
    like, created = CommentLike.objects.get_or_create(user=request.user, comment=comment)
    if created:
        Comment.objects.filter(pk=comment.pk).update(likes_count=F('likes_count') + 1)
        return JsonResponse({'liked': True, 'count': comment.likes_count + 1})
    else:
        like.delete()
        Comment.objects.filter(pk=comment.pk).update(likes_count=F('likes_count') - 1)
        return JsonResponse({'liked': False, 'count': max(0, comment.likes_count - 1)})


@login_required
@require_POST
def report_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    reason = request.POST.get('reason', 'other')
    CommentReport.objects.get_or_create(
        reporter=request.user,
        comment=comment,
        defaults={'reason': reason}
    )
    return JsonResponse({'success': True, 'message': 'Comment reported. Thank you.'})


@login_required
@require_POST
def delete_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    if comment.author == request.user or request.user.is_staff:
        blog_url = comment.blog.get_absolute_url()
        comment.delete()
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True})
        return redirect(blog_url + '#comments')
    return JsonResponse({'error': 'Permission denied'}, status=403)


def add_comment_by_id(request, blog_id):
    """Add comment by blog ID (used by AJAX forms)"""
    from blogs.models import Blog
    blog = get_object_or_404(Blog, id=blog_id)
    # Reuse the main add_comment logic
    return add_comment(request, blog.slug)
