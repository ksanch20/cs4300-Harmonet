from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.index, name='index'),  # user homepage / index
    path('login/', views.user_login, name='login'),  # login page
    path('logout/', views.user_logout, name='logout'),   # logout
    path('register/', views.register, name='register'),# register page
    path('dashboard/', views.dashboard, name='dashboard'),
    path('account_link/', views.account_link, name='account_link'),  # unique name
    path('user_artist/', views.user_artist, name='user_artist'),



    path('profile/', views.profile, name='profile'),
    path('analytics/', views.analytics, name='analytics'),
    path('AI_Recommendation/', views.AI_Recommendation, name='AI_Recommendation'), #Change password
    path('password-change/', views.password_change, name='password_change'),
    path('delete-account/', views.delete_account, name='delete_account'),

    ####Spotify patterns####
    path('spotify/login/', views.spotify_login, name='spotify_login'),
    path('spotify/callback/', views.spotify_callback, name='spotify_callback'),
    path('account/link/', views.account_link, name='account_link'),

    #Password reset URLS
    path('password-reset/', auth_views.PasswordResetView.as_view(template_name='user/password_reset.html'), name='password_reset'),
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='user/password_reset_done.html'), name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='user/password_reset_confirm.html'), name='password_reset_confirm'),
    path('password-reset-complete/', auth_views.PasswordResetCompleteView.as_view(template_name='user/password_reset_complete.html'), name='password_reset_complete'),

    #Music preferences
    path('music-preferences/', views.music_preferences, name='music_preferences'),
    
    path('friends_dashboard/', views.friends_dashboard, name='friends_dashboard'),
    path('send-request/<int:user_id>/', views.send_friend_request, name='send_friend_request'),
    path('accept-request/<int:request_id>/', views.accept_friend_request, name='accept_friend_request'),
    path('decline-request/<int:request_id>/', views.decline_friend_request, name='decline_friend_request'),
    path('remove-friend/<int:user_id>/', views.remove_friend, name='remove_friend'),

    path('ai-recommendations/', views.ai_recommendations, name='ai_recommendations'),
]

