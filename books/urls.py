from django.urls import path
from .views import LibraryManagementView

urlpatterns = [
    path('', LibraryManagementView.as_view(action='home'), name='home'),
    path('issue', LibraryManagementView.as_view(action='issue'), name='issue'),
    path('login/', LibraryManagementView.as_view(action='login'), name='login'),
    path('register/', LibraryManagementView.as_view(action='register'), name='register'),
    path('logout', LibraryManagementView.as_view(action='logout'), name='logout'),
    path('return_item', LibraryManagementView.as_view(action='return_item'), name='return_item'),
    path('history', LibraryManagementView.as_view(action='history'), name='history'),
]
