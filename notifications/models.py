from django.db import models
from accounts.models import User
import uuid


class Notification(models.Model):
    TYPE_CHOICES = [
        ('blog_submitted', 'Blog Submitted'),
        ('blog_approved', 'Blog Approved'),
        ('blog_rejected', 'Blog Rejected'),
        ('comment', 'New Comment'),
        ('reply', 'Comment Reply'),
        ('like', 'Blog Liked'),
        ('comment_like', 'Comment Liked'),
        ('system', 'System Notification'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    sender = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='sent_notifications')
    notification_type = models.CharField(max_length=30, choices=TYPE_CHOICES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    link = models.URLField(blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'notifications'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient', 'is_read']),
        ]

    def __str__(self):
        return f"Notification for {self.recipient.username}: {self.title}"

    def mark_as_read(self):
        self.is_read = True
        self.save(update_fields=['is_read'])
