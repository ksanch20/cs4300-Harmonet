from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.index, name='index'),  # user homepage / index
    path('login/', views.user_login, name='login'),  # login page
    path('logout/', views.user_logout, name='logout'),   # logout
    path('register/', views.register, name='register'),# register page
    path('dashboard/', views.dashboard, name='dashboard'),  # dashboard
    path('profile/', views.profile, name='profile'),
    path('analytics/', views.analytics, name='analytics'),
    path('AI_Recommendation/', views.AI_Recommendation, name='AI_Recommendation'),
    ####Spotify patterns####
    path('spotify/login/', views.spotify_login, name='spotify_login'),
    path('spotify/callback/', views.spotify_callback, name='spotify_callback'),
    path('spotify/dashboard/', views.spotify_dashboard, name='spotify_dashboard'),
]
