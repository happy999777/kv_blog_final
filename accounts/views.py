from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views import View
from django.views.generic import TemplateView
from django.utils.decorators import method_decorator
from django.core.mail import send_mail
from django.conf import settings
from django.db.models import Count
from .models import User, Profile, PasswordResetToken
from .forms import (RegisterForm, LoginForm, ProfileEditForm,
                    ChangePasswordForm, ForgotPasswordForm, ResetPasswordForm)
from blogs.models import Blog
from notifications.models import Notification
import uuid


class RegisterView(View):
    template_name = 'accounts/register.html'

    def get(self, request):
        if request.user.is_authenticated:
            return redirect('core:home')
        form = RegisterForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = True
            user.save()
            Profile.objects.create(user=user)
            # Send verification email
            self._send_verification_email(request, user)
            messages.success(request, 'Account created! Please check your email to verify your account.')
            return redirect('accounts:login')
        return render(request, self.template_name, {'form': form})

    def _send_verification_email(self, request, user):
        verify_url = request.build_absolute_uri(
            f'/accounts/verify-email/{user.email_verification_token}/'
        )
        try:
            send_mail(
                subject='Verify Your Email - BlogPlatform',
                message=f'Click here to verify: {verify_url}',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=True,
            )
        except Exception:
            pass


class LoginView(View):
    template_name = 'accounts/login.html'

    def get(self, request):
        if request.user.is_authenticated:
            return redirect('core:home')
        form = LoginForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = LoginForm(request.POST)
        if form.is_valid():
            identifier = form.cleaned_data['email']
            password = form.cleaned_data['password']
            remember_me = form.cleaned_data.get('remember_me', False)
            user = None
            if '@' in identifier:
                user = authenticate(request, username=identifier, password=password)
            else:
                try:
                    user_obj = User.objects.get(username=identifier)
                    user = authenticate(request, username=user_obj.email, password=password)
                except User.DoesNotExist:
                    user = None
            if user:
                login(request, user)
                if not remember_me:
                    request.session.set_expiry(0)
                next_url = request.POST.get('next') or request.GET.get('next') or 'dashboard:home'
                messages.success(request, f'Welcome back, {user.get_full_name()}!')
                return redirect(next_url)
            else:
                messages.error(request, 'Invalid email or password.')
        return render(request, self.template_name, {'form': form})


class LogoutView(View):
    def get(self, request):
        return self.post(request)

    def post(self, request):
        logout(request)
        messages.info(request, 'You have been logged out.')
        return redirect('core:home')


class VerifyEmailView(View):
    def get(self, request, token):
        try:
            user = User.objects.get(email_verification_token=token)
            user.is_email_verified = True
            user.save(update_fields=['is_email_verified'])
            messages.success(request, 'Email verified successfully! You can now log in.')
        except User.DoesNotExist:
            messages.error(request, 'Invalid verification link.')
        return redirect('accounts:login')


class ForgotPasswordView(View):
    template_name = 'accounts/forgot_password.html'

    def get(self, request):
        return render(request, self.template_name, {'form': ForgotPasswordForm()})

    def post(self, request):
        form = ForgotPasswordForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            try:
                user = User.objects.get(email=email)
                token_obj = PasswordResetToken.objects.create(user=user)
                reset_url = request.build_absolute_uri(
                    f'/accounts/reset-password/{token_obj.token}/'
                )
                send_mail(
                    subject='Reset Your Password - BlogPlatform',
                    message=f'Click here to reset: {reset_url}',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[email],
                    fail_silently=True,
                )
            except User.DoesNotExist:
                pass
            messages.success(request, 'If that email exists, you will receive a reset link.')
        return render(request, self.template_name, {'form': form})


class ResetPasswordView(View):
    template_name = 'accounts/reset_password.html'

    def get(self, request, token):
        try:
            token_obj = PasswordResetToken.objects.get(token=token)
            if not token_obj.is_valid():
                messages.error(request, 'This reset link has expired.')
                return redirect('accounts:forgot_password')
        except PasswordResetToken.DoesNotExist:
            messages.error(request, 'Invalid reset link.')
            return redirect('accounts:forgot_password')
        form = ResetPasswordForm()
        return render(request, self.template_name, {'form': form, 'token': token})

    def post(self, request, token):
        try:
            token_obj = PasswordResetToken.objects.get(token=token)
        except PasswordResetToken.DoesNotExist:
            messages.error(request, 'Invalid reset link.')
            return redirect('accounts:forgot_password')
        form = ResetPasswordForm(request.POST)
        if form.is_valid():
            token_obj.user.set_password(form.cleaned_data['password'])
            token_obj.user.save()
            token_obj.is_used = True
            token_obj.save()
            messages.success(request, 'Password reset successfully! Please log in.')
            return redirect('accounts:login')
        return render(request, self.template_name, {'form': form, 'token': token})


class AuthorProfileView(View):
    template_name = 'accounts/profile.html'

    def get(self, request, username):
        from django.core.paginator import Paginator
        from django.db.models import Sum
        profile_user = get_object_or_404(User, username=username)
        blog_qs = Blog.objects.filter(
            author=profile_user, status='published'
        ).select_related('category', 'author', 'author__profile').order_by('-published_at')

        paginator = Paginator(blog_qs, 6)
        page_num = request.GET.get('page', 1)
        blogs = paginator.get_page(page_num)

        total_views = blog_qs.aggregate(t=Sum('views_count'))['t'] or 0

        return render(request, self.template_name, {
            'profile_user': profile_user,
            'author': profile_user,
            'blogs': blogs,
            'total_views': total_views,
            'blog_count': blog_qs.count(),
        })


@method_decorator(login_required, name='dispatch')
class ProfileEditView(View):
    template_name = 'accounts/profile_edit.html'

    def get(self, request):
        form = ProfileEditForm(instance=request.user, profile_instance=request.user.profile)
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = ProfileEditForm(
            request.POST, request.FILES,
            instance=request.user,
            profile_instance=request.user.profile
        )
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('accounts:profile_edit')
        return render(request, self.template_name, {'form': form})


@method_decorator(login_required, name='dispatch')
class ChangePasswordView(View):
    template_name = 'accounts/change_password.html'

    def get(self, request):
        return render(request, self.template_name, {'form': ChangePasswordForm(request.user)})

    def post(self, request):
        form = ChangePasswordForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Password changed successfully!')
            return redirect('accounts:change_password')
        return render(request, self.template_name, {'form': form})
