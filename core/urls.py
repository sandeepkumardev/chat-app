from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('signup/', views.signup_view, name='signup'),
    path('logout/', views.logout_view, name='logout'),
    path('create-room/', views.create_room, name='create_room'),
    path('delete-room/<int:room_id>/', views.delete_room, name='delete_room'),
    path('profile/', views.profile, name='profile'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('create_room_ajax/', views.create_room_ajax, name='create_room_ajax'),
]