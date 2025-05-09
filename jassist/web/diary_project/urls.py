"""
diary_project URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    # Include allauth URLs for handling the entire authentication flow
    path('accounts/', include('allauth.urls')), 
    # Include Drive download URLs with the namespace 'gdrive'
    path('drive/', include('jassist.web.download_gdrive.urls', namespace='download_gdrive')),
    # Manual entries URLs
    path('entries/', include('jassist.web.manual_entries.urls', namespace='manual_entries')),
    # Contacts URLs
    path('contacts/', include('jassist.web.contacts.urls', namespace='contacts')),
    # API endpoints
    path('api/', include('jassist.web.api.urls')),
    # Include your jassist_app URLs, making them the default for the site
    path('', include('jassist.web.jassist_app.urls')), 
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) 