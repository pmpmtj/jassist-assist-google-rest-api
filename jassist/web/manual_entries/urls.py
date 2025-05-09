from django.urls import path
from . import views

app_name = 'manual_entries'

urlpatterns = [
    path('create/', views.create_entry, name='create_entry'),
    path('list/', views.list_entries, name='list_entries'),
    path('edit/<int:entry_id>/', views.edit_entry, name='edit_entry'),
] 