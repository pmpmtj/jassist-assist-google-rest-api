from django.urls import path
from . import views

app_name = 'contacts'

urlpatterns = [
    path('', views.contact_list, name='list'),
    path('add/', views.contact_create, name='create'),
    path('<int:contact_id>/', views.contact_detail, name='detail'),
    path('<int:contact_id>/edit/', views.contact_edit, name='edit'),
    path('<int:contact_id>/delete/', views.contact_delete, name='delete'),
] 