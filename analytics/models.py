from django.db import models
from accounts.models import User


class ActivityLog(models.Model):
    ACTION_CHOICES = [
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('blog_create', 'Blog Created'),
        ('blog_edit', 'Blog Edited'),
        ('blog_delete', 'Blog Deleted'),
        ('blog_approve', 'Blog Approved'),
        ('blog_reject', 'Blog Rejected'),
        ('comment_add', 'Comment Added'),
        ('profile_edit', 'Profile Edited'),
    ]
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=30, choices=ACTION_CHOICES)
    description = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'activity_logs'
        ordering = ['-created_at']
        indexes = [models.Index(fields=['user', 'created_at'])]

    def __str__(self):
        return f"{self.user} - {self.action} at {self.created_at}"


class SiteStatistic(models.Model):
    date = models.DateField(unique=True)
    total_views = models.PositiveBigIntegerField(default=0)
    unique_visitors = models.PositiveIntegerField(default=0)
    new_users = models.PositiveIntegerField(default=0)
    new_blogs = models.PositiveIntegerField(default=0)
    new_comments = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = 'site_statistics'
        ordering = ['-date']

    def __str__(self):
        return f"Stats for {self.date}"
