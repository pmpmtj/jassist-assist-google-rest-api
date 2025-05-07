from django.urls import path
from . import views

# Define URL patterns for the jassist_app
urlpatterns = [
    # Authentication
    path('', views.login_view, name='login'),
    path('success/', views.success_view, name='success'),
    path('profile/', views.profile_view, name='profile'),
] 