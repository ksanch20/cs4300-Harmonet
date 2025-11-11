from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout as auth_logout
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from .forms import UserRegisterForm, SoundCloudArtistForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from django.db import models
from django.db.models import Q

from django.contrib.auth.models import User
from .ai_service import get_music_recommendations
from django.conf import settings
from .models import MusicPreferences, SoundCloudArtist, FriendRequest, FriendRequestManager, SpotifyTopArtist, SpotifyTopTrack


from django.core.paginator import Paginator
from .models import SoundCloudArtist
from .forms import SoundCloudArtistForm

import re
from django.utils.safestring import mark_safe

from .spotify_service import (
    get_spotify_oauth, 
    save_spotify_connection, 
    fetch_and_save_top_artists,
    fetch_and_save_top_tracks,
    is_spotify_connected,
    disconnect_spotify
)

#################### index ####################################### 
def index(request):
    return render(request, 'index.html', {'title':'index'})

########### register here ##################################### 
def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')

            # Automatically log the user in after signup (optional)
            login(request, user)
            return redirect('dashboard')
    else:
        form = UserRegisterForm()
    return render(request, 'user/register.html', {'form': form, 'title':'register here'})

################ login forms ################################################### 
def user_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, "Invalid username or password")
            
    form = AuthenticationForm()
    return render(request, 'user/login.html', {'form': form, 'title':'log in'})

@login_required
def dashboard(request):
    """Dashboard view with Spotify integration"""
    # Check if Spotify is connected
    spotify_connected = is_spotify_connected(request.user)
    
    # Get top artists if connected
    top_artists = []
    if spotify_connected:
        top_artists = SpotifyTopArtist.objects.filter(user=request.user).order_by('rank')[:5]
        print(f"Found {len(top_artists)} top artists for {request.user.username}")
    
    return render(request, 'user/dashboard.html', {
        'title': 'Dashboard',
        'spotify_connected': spotify_connected,
        'top_artists': top_artists
    })

# ---------------- Logout -----------------
def user_logout(request):
    auth_logout(request)
    return redirect('index')

@login_required
def account_link(request):
    token_info = request.session.get('spotify_token')
    spotify_data = None

    if token_info:
        sp = spotipy.Spotify(auth=token_info['access_token'])
        try:
            spotify_user = sp.current_user()
            spotify_data = {
                'display_name': spotify_user.get('display_name'),
                'email': spotify_user.get('email'),
                'id': spotify_user.get('id'),
            }
        except Exception as e:
            spotify_data = {'error': str(e)}
    
    return render(request, 'user/account_link.html', {
        'title': 'Account Link',
        'spotify_data': spotify_data,
    })

def profile(request):
    return render(request, 'user/profile.html', {'title': 'profile'})

def analytics(request):
    return render(request, 'user/analytics.html', {'title': 'analytics'})

def AI_Recommendation(request):
    return render(request, 'user/AI_Recommendation.html', {'title': 'AI_Recommendation'})

def user_artist(request):
    return render(request, 'user/user_artist.html', {'title': 'user_artist'})

# Add this function to your views.py
@login_required
def password_change(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            # Important: Update the session to prevent logout
            from django.contrib.auth import update_session_auth_hash
            update_session_auth_hash(request, user)
            
            messages.success(request, 'Your password was successfully updated!')
            return redirect('password_change')  # Redirect to same page to show message
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = PasswordChangeForm(request.user)
    
    return render(request, 'user/password_change.html', {
        'form': form,
        'title': 'Change Password'
    })

#########################Spotify OAuth######################

@login_required
def spotify_login(request):
    """Start the Spotify OAuth flow"""
    sp_oauth = get_spotify_oauth()
    auth_url = sp_oauth.get_authorize_url()
    return redirect(auth_url)

@login_required
def spotify_callback(request):
    """
    Handle Spotify OAuth callback
    Save connection and fetch user's top artists/tracks
    """
    sp_oauth = get_spotify_oauth()
    code = request.GET.get('code')
    
    if code:
        try:
            # Get access token
            token_info = sp_oauth.get_access_token(code)
            print(f"Got token for user: {request.user.username}")
            
            # Save Spotify connection to database
            spotify_account = save_spotify_connection(request.user, token_info)
            print(f"Saved Spotify account: {spotify_account.spotify_id}")
            
            # Fetch and save top artists and tracks
            artists_success = fetch_and_save_top_artists(request.user)
            tracks_success = fetch_and_save_top_tracks(request.user)
            
            print(f"Artists fetch: {artists_success}, Tracks fetch: {tracks_success}")
            
            if artists_success and tracks_success:
                messages.success(request, 'Spotify account connected successfully! Your top music has been loaded.')
            elif artists_success or tracks_success:
                messages.warning(request, 'Spotify connected but some data could not be loaded.')
            else:
                messages.error(request, 'Spotify connected but could not load your music data.')
                
        except Exception as e:
            print(f"Error in spotify_callback: {str(e)}")
            import traceback
            traceback.print_exc()
            messages.error(request, f'Error connecting Spotify: {str(e)}')
    else:
        messages.error(request, 'No authorization code received from Spotify.')
    
    # Redirect to dashboard instead of account_link
    return redirect('dashboard')

@login_required
def spotify_disconnect(request):
    """Disconnect user's Spotify account"""
    if request.method == 'POST':
        disconnect_spotify(request.user)
        messages.success(request, 'Spotify account disconnected successfully.')
    return redirect('account_link')


@login_required
def spotify_refresh_data(request):
    """Manually refresh Spotify top artists and tracks"""
    if request.method == 'POST':
        if is_spotify_connected(request.user):
            success_artists = fetch_and_save_top_artists(request.user)
            success_tracks = fetch_and_save_top_tracks(request.user)
            
            if success_artists and success_tracks:
                messages.success(request, 'Your Spotify data has been refreshed!')
            else:
                messages.error(request, 'Error refreshing Spotify data.')
        else:
            messages.error(request, 'Please connect your Spotify account first.')
    
    return redirect('dashboard')

#########################SoundCloud Form################################################

@login_required
def user_artist(request):
    user = request.user
    artists_list = SoundCloudArtist.objects.filter(user=user).order_by('-added_on')

    paginator = Paginator(artists_list, 5)
    page_number = request.GET.get('page')
    artists = paginator.get_page(page_number)

    if request.method == 'POST':
        if 'delete_artist_id' in request.POST:
            artist_id = request.POST.get('delete_artist_id')
            artist = get_object_or_404(SoundCloudArtist, id=artist_id, user=user)
            artist.delete()
            return redirect('user_artist')


        form = SoundCloudArtistForm(request.POST)
        if form.is_valid():
            artist = form.save(commit=False)
            artist.user = user
            artist.save()
            return redirect('user_artist')
    else:
        form = SoundCloudArtistForm()

    context = {
        'form': form,
        'artists': artists,
    }

    return render(request, 'user/user_artist.html', context)


@login_required
def delete_account(request):
    if request.method == "POST":
        user = request.user
        auth_logout(request) #Log user out
        user.delete() #Delete user account
        return redirect('index') #Redirect user to home page
    return redirect('profile') 

#View for users to add/edit their general music preferences
@login_required
def music_preferences(request):
    #Get existing preferences or create new blank ones for this user
    preferences, created = MusicPreferences.objects.get_or_create(user=request.user)
    
    #Check if this is a form submission (user clicked "Save")
    if request.method == 'POST':
        # Extract form data from POST request
        # .get() returns the value or empty string if field wasn't filled
        preferences.favorite_artists = request.POST.get('artists', '')
        preferences.favorite_genres = request.POST.get('genres', '')
        preferences.favorite_tracks = request.POST.get('tracks', '')
        
        # Save to database
        # This also automatically updates the 'updated_at' timestamp
        preferences.save()
        
        # Create a success message that will be shown on the next page
        messages.success(request, 'Your music preferences have been saved!')
        
        # Redirect user back to dashboard
        # This prevents form resubmission if user refreshes the page
        return redirect('music_preferences')
    
    # If not POST show the form
    # Pass preferences object to template so form can be pre-filled
    return render(request, 'user/music_preferences.html', {
        'preferences': preferences,
        'title': 'Music Preferences'
    })

###############################FRIEND REQUESTS#########################
# views.py


@login_required
def friends_dashboard(request):
    friends = FriendRequest.objects.friends(request.user)
    pending_received = FriendRequest.objects.pending_requests(request.user)
    pending_sent = FriendRequest.objects.filter(
        from_user=request.user, 
        status='pending'
    )
    
    # Search functionality
    search_query = request.GET.get('search', '')
    search_results = []
    
    if search_query:
        # Get all friend request user IDs (both directions, all statuses)
        friend_request_users = FriendRequest.objects.filter(
            Q(from_user=request.user) | Q(to_user=request.user)
        ).values_list('from_user_id', 'to_user_id')
        
        # Flatten the list to get all user IDs involved in requests
        related_user_ids = set()
        for from_id, to_id in friend_request_users:
            related_user_ids.add(from_id)
            related_user_ids.add(to_id)
        
        # Search users by username or email, exclude self and existing connections
        search_results = User.objects.filter(
            Q(username__icontains=search_query) | 
            Q(email__icontains=search_query)
        ).exclude(
            id=request.user.id  # Exclude self
        ).exclude(
            id__in=related_user_ids  # Exclude anyone with existing request/friendship
        )[:10]  # Limit to 10 results
    
    context = {
        'friends': friends,
        'pending_received': pending_received,
        'pending_sent': pending_sent,
        'search_query': search_query,
        'search_results': search_results,
    }
    return render(request, 'user/friends_dashboard.html', context)

@login_required
def send_friend_request(request, user_id):
    to_user = get_object_or_404(User, id=user_id)
    
    if to_user == request.user:
        messages.error(request, "You cannot send a friend request to yourself.")
        return redirect('profile')
    # Check if request already exists
    existing = FriendRequest.objects.filter(
        models.Q(from_user=request.user, to_user=to_user) |
        models.Q(from_user=to_user, to_user=request.user)
    ).first()
    
    if existing:
        if existing.status == 'accepted':
            messages.info(request, "You are already friends.")
        elif existing.status == 'pending':
            messages.info(request, "Friend request already pending.")
        else:
            messages.info(request, "A friend request already exists.")
    else:
        FriendRequest.objects.create(from_user=request.user, to_user=to_user)
      
    return redirect('friends_dashboard')

@login_required
def accept_friend_request(request, request_id):
    friend_request = get_object_or_404(FriendRequest, id=request_id, to_user=request.user)
    friend_request.status = 'accepted'
    friend_request.save()

    return redirect('friends_dashboard')

@login_required
def decline_friend_request(request, request_id):
    friend_request = get_object_or_404(FriendRequest, id=request_id, to_user=request.user)
    friend_request.status = 'declined'
    friend_request.save()
    return redirect('friends_dashboard')

@login_required
def remove_friend(request, user_id):
    friend = get_object_or_404(User, id=user_id)
    
    FriendRequest.objects.filter(
        models.Q(from_user=request.user, to_user=friend) |
        models.Q(from_user=friend, to_user=request.user),
        status='accepted'
    ).delete()
    
    
    return redirect('friends_dashboard')




def format_ai_recommendations(raw_text):

    # Replace ### headers (artist names)
    text = re.sub(r'###\s*\*\*(\d+)\.\s*(.+?)\*\*', r'<h3>\1. \2</h3>', raw_text)
    
    # Replace **bold text** with styled spans  
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    
    # Process line by line to handle lists properly
    lines = text.split('\n')
    formatted_lines = []
    in_list = False
    
    for line in lines:
        stripped = line.strip()
        
        # Handle bullet points
        if stripped.startswith('- '):
            if not in_list:
                formatted_lines.append('<ul>')
                in_list = True
            item = stripped[2:]  # Remove '- '
            formatted_lines.append(f'<li>{item}</li>')
        else:
            # Close list if we were in one
            if in_list:
                formatted_lines.append('</ul>')
                in_list = False
            
            # Handle horizontal rules
            if stripped == '---':
                formatted_lines.append('<hr>')
            # Handle regular paragraphs (skip empty lines)
            elif stripped:
                formatted_lines.append(f'<p>{line}</p>')
            else:
                formatted_lines.append('')
    
    # Close list if still open
    if in_list:
        formatted_lines.append('</ul>')
    
    return mark_safe('\n'.join(formatted_lines))


@login_required
def ai_recommendations(request):
    """
    Display AI-generated music recommendations for the user.
    """
    
    recommendations = None
    error_message = None
    
    # Check if user clicked "Generate Recommendations" button
    if request.method == 'POST':
        result = get_music_recommendations(request.user)
        
        if result['success']:
            # Format the recommendations with HTML
            recommendations = format_ai_recommendations(result['recommendations'])
        else:
            error_message = result['message']
    
    return render(request, 'user/ai_recommendations.html', {
        'recommendations': recommendations,
        'error_message': error_message,
        'title': 'AI Recommendations'
    })
