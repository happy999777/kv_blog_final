from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

app_name = 'accounts'

urlpatterns = [
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('verify-email/<uuid:token>/', views.VerifyEmailView.as_view(), name='verify_email'),
    path('forgot-password/', views.ForgotPasswordView.as_view(), name='forgot_password'),
    path('reset-password/<uuid:token>/', views.ResetPasswordView.as_view(), name='reset_password'),
    # password_reset for Django's built-in forgot password link used in template
    path('password-reset/', views.ForgotPasswordView.as_view(), name='password_reset'),
    path('profile/edit/', views.ProfileEditView.as_view(), name='profile_edit'),
    path('change-password/', views.ChangePasswordView.as_view(), name='change_password'),
    # Named profile URL - accepts username, used via accounts:profile
    path('profile/<str:username>/', views.AuthorProfileView.as_view(), name='profile'),
    path('author/<str:username>/', views.AuthorProfileView.as_view(), name='author_profile'),
]
