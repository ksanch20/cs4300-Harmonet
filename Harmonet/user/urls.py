from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.index, name='index'),  # user homepage / index
    path('login/', views.user_login, name='login'),  # login page
    path('logout/', views.user_logout, name='logout'),   # logout
    path('register/', views.register, name='register'),  # register page
    path('dashboard/', views.dashboard, name='dashboard'),  # dashboard
]
