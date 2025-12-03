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
from django.utils import timezone
from django.contrib.auth.models import User
from .ai_service import get_music_recommendations, get_music_profile
from django.conf import settings
from .models import MusicPreferences, SoundCloudArtist, FriendRequest, FriendRequestManager, SpotifyTopArtist, SpotifyTopTrack
from django.http import JsonResponse
from .models import Artist, Album

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


from django.http import JsonResponse
from .models import Artist, Album 
from .forms import ArtistForm
import logging

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
    """Dashboard view with Spotify integration and detailed debugging"""
    # Check if Spotify is connected
    spotify_connected = is_spotify_connected(request.user)
    
    # Get top artists and tracks if connected
    top_artists = []
    top_tracks = []
    spotify_account = None
    
    if spotify_connected:
        try:
            spotify_account = request.user.spotify_account
            top_artists = SpotifyTopArtist.objects.filter(user=request.user).order_by('rank')[:5]
            top_tracks = SpotifyTopTrack.objects.filter(user=request.user).order_by('rank')[:5]
            
            # Debug: Show if data exists but isn't loading
            if len(top_artists) == 0:
                total_artists = SpotifyTopArtist.objects.filter(user=request.user).count()
                print(f"⚠️ WARNING: No artists in top 5, but {total_artists} total artists in database")
            
            if len(top_tracks) == 0:
                total_tracks = SpotifyTopTrack.objects.filter(user=request.user).count()
                print(f"⚠️ WARNING: No tracks in top 5, but {total_tracks} total tracks in database")
            
        except Exception as e:
            print(f"❌ Error loading Spotify data for {request.user.username}: {e}")
            import traceback
            traceback.print_exc()
    else:
        print(f"Dashboard load for {request.user.username}: Spotify NOT connected")
    
    # Get music profile from session (if exists)
    user_profile = request.session.get('music_profile', None)

    friends = FriendRequest.objects.friends(request.user)
    
    return render(request, 'user/dashboard.html', {
        'title': 'Dashboard',
        'spotify_connected': spotify_connected,
        'spotify_account': spotify_account,
        'top_artists': top_artists,
        'top_tracks': top_tracks,
        'user_profile': user_profile,
        'friends': friends
    })

# ---------------- Logout -----------------
def user_logout(request):
    auth_logout(request)
    return redirect('index')


@login_required
def generate_music_profile_inline(request):
    """
    Generate music profile from dashboard and redirect back
    """
    if request.method == 'POST':
        result = get_music_profile(request.user)
        if result['success']:
            # Store in session
            request.session['music_profile'] = result['profile']
            messages.success(request, 'Music profile generated!')
        else:
            messages.error(request, result['message'])
    
    return redirect('dashboard')


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
@login_required
def privacy_settings(request):

    # Handle privacy settings update
    if request.method == 'POST':
        new_privacy = request.POST.get('privacy_setting')
        if new_privacy in ['public', 'friends', 'private']:
            user_profile = request.user.profile
            old_privacy = user_profile.get_privacy_display()
            user_profile.privacy = new_privacy
            user_profile.save()
            
            # Refresh the user profile from database to get updated display value
            user_profile.refresh_from_db()
            
            
            return redirect('privacy_settings')
        else:
            messages.error(request, 'Invalid privacy setting selected.')
    
    # Fetch fresh profile data for display
    user_profile = request.user.profile
    user_profile.refresh_from_db()
    
    
    
    context = {
        'title': 'Privacy Settings',
        'user_profile': user_profile,
    }
    return render(request, 'user/privacy_settings.html', context)


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
    # COMPREHENSIVE SESSION CLEARING
    keys_to_clear = ['spotify_token', 'spotify_auth_user_id']
    for key in keys_to_clear:
        if key in request.session:
            del request.session[key]
    
    # Force session save
    request.session.modified = True
    
    # Store the user ID in the session to verify after the callback
    request.session['spotify_auth_user_id'] = request.user.id
    
    sp_oauth = get_spotify_oauth()
    
    # Add state parameter for security and debugging
    state = f"{request.user.id}"
    auth_url = sp_oauth.get_authorize_url(state=state)
    
    return redirect(auth_url)

@login_required
def spotify_callback(request):
    """
    Handle Spotify OAuth callback
    Save connection and fetch user's top artists/tracks
    """
    # Verify this is the same user who started the OAuth flow
    auth_user_id = request.session.get('spotify_auth_user_id')
    if auth_user_id != request.user.id:
        messages.error(request, 'Session mismatch. Please try connecting again.')
        return redirect('dashboard')
    
    sp_oauth = get_spotify_oauth()
    code = request.GET.get('code')
    
    if code:
        try:
            print(f"=== SPOTIFY CALLBACK START ===")
            print(f"Harmonets user: {request.user.username} (ID: {request.user.id})")
            
            # Get access token
            token_info = sp_oauth.get_access_token(code)
            print(f"Got token for user: {request.user.username}")
            
            # Save Spotify connection to database (this will print debug info)
            spotify_account = save_spotify_connection(request.user, token_info)
            print(f"Successfully saved Spotify account: {spotify_account.spotify_id}")
            print(f"==============================")
            
            # Clean up session
            if 'spotify_auth_user_id' in request.session:
                del request.session['spotify_auth_user_id']
            
            # Fetch and save top artists and tracks with detailed error handling
            print(f"\n=== STARTING DATA FETCH FOR {request.user.username} ===")
            artists_result = fetch_and_save_top_artists(request.user)
            tracks_result = fetch_and_save_top_tracks(request.user)
            print(f"=== DATA FETCH COMPLETE ===\n")
            
            # Check results and show appropriate message
            if artists_result['success'] and tracks_result['success']:
                messages.success(
                    request, 
                    f'✅ Spotify connected as {spotify_account.display_name}! '
                    f'Loaded {artists_result["count"]} artists and {tracks_result["count"]} tracks.'
                )
            elif artists_result['success'] or tracks_result['success']:
                messages.warning(
                    request,
                    f'⚠️ Spotify connected but only partial data loaded. '
                    f'Artists: {artists_result["count"]}, Tracks: {tracks_result["count"]}. '
                    f'Try refreshing your data from the dashboard.'
                )
            else:
                messages.warning(
                    request,
                    f'⚠️ Spotify connected as {spotify_account.display_name}, but could not load your music data. '
                    f'Error: {artists_result.get("message", "Unknown error")}. '
                    f'Please try the "Refresh Data" button on your dashboard.'
                )
                
        except Exception as e:
            error_str = str(e)
            print(f"=== SPOTIFY CALLBACK ERROR ===")
            print(f"Error in spotify_callback: {error_str}")
            print(f"Harmonets user: {request.user.username}")
            import traceback
            traceback.print_exc()
            print(f"==============================")
            
            # User-friendly error message
            if "already connected" in error_str.lower():
                messages.error(
                    request, 
                    f'❌ {error_str} Please disconnect from the other account first, '
                    f'or use a different Spotify account.'
                )
            else:
                messages.error(request, f'❌ Error connecting Spotify: {error_str}')
    else:
        messages.error(request, 'No authorization code received from Spotify.')
    
    return redirect('dashboard')

@login_required
def spotify_disconnect(request):
    """Disconnect user's Spotify account"""
    if request.method == 'POST':
        print(f"Disconnecting Spotify for user: {request.user.username}")
        disconnect_spotify(request.user)
        messages.success(request, 'Spotify account disconnected successfully.')
    return redirect('dashboard')


@login_required
def spotify_refresh_data(request):
    """Manually refresh Spotify top artists and tracks with detailed feedback"""
    if request.method == 'POST':
        if is_spotify_connected(request.user):
            print(f"\n=== MANUAL REFRESH FOR {request.user.username} ===")
            
            artists_result = fetch_and_save_top_artists(request.user)
            tracks_result = fetch_and_save_top_tracks(request.user)
            
            if artists_result['success'] and tracks_result['success']:
                messages.success(
                    request, 
                    f'✅ Data refreshed! Loaded {artists_result["count"]} artists and {tracks_result["count"]} tracks.'
                )
            elif artists_result['success'] or tracks_result['success']:
                messages.warning(
                    request,
                    f'⚠️ Partial refresh. Artists: {artists_result["count"]}, Tracks: {tracks_result["count"]}. '
                    f'Errors: {artists_result.get("message", "N/A")} / {tracks_result.get("message", "N/A")}'
                )
            else:
                messages.error(
                    request,
                    f'❌ Could not refresh data. '
                    f'Artists error: {artists_result.get("message", "Unknown")}. '
                    f'Tracks error: {tracks_result.get("message", "Unknown")}. '
                    f'Your Spotify connection may have expired - try disconnecting and reconnecting.'
                )
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
    
    # Get user's friend code
    friend_code = request.user.profile.friend_code
    
    # Search functionality
    search_query = request.GET.get('search', '')
    search_results = []
    
    if search_query:
        friend_request_users = FriendRequest.objects.filter(
            Q(from_user=request.user) | Q(to_user=request.user),
            status__in=['pending', 'accepted']  
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
        'friend_code': friend_code,  # ADD THIS LINE
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
        return redirect('friends_dashboard')
    
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
        elif existing.status == 'declined':
            # Allow resending after decline - UPDATE TIMESTAMP
            existing.from_user = request.user
            existing.to_user = to_user
            existing.status = 'pending'
            existing.created_at = timezone.now()  # ← ADD THIS LINE
            existing.save()
            messages.success(request, f"Friend request sent to {to_user.username}!")
    else:
        # Create new friend request
        FriendRequest.objects.create(from_user=request.user, to_user=to_user)
        messages.success(request, f"Friend request sent to {to_user.username}!")
    
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
    
    # Check Spotify connection status
    spotify_connected = is_spotify_connected(request.user)
    
    # Check if user has manual preferences
    has_manual_prefs = False
    try:
        prefs = request.user.music_preferences
        has_manual_prefs = bool(
            prefs.get_artists_list() or 
            prefs.get_genres_list() or 
            prefs.get_tracks_list()
        )
    except:
        pass
    
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
        'spotify_connected': spotify_connected,
        'has_manual_prefs': has_manual_prefs,
        'title': 'AI Recommendations'
    })


@login_required
def add_friend_by_code(request):
    """Add friend using their friend code."""
    
    if request.method == 'POST':
        friend_code = request.POST.get('friend_code', '').strip().upper()
        
        if not friend_code:
            messages.error(request, 'Please enter a friend code.')
            return redirect('friends_dashboard')
        
        # Try to find user with this code
        try:
            from .models import UserProfile
            profile = UserProfile.objects.get(friend_code=friend_code)
            to_user = profile.user
            
            # Can't add yourself
            if to_user == request.user:
                messages.error(request, 'You cannot add yourself as a friend!')
                return redirect('friends_dashboard')
            
            # Check if request already exists
            existing = FriendRequest.objects.filter(
                Q(from_user=request.user, to_user=to_user) |
                Q(from_user=to_user, to_user=request.user)
            ).first()
            
            if existing:
                if existing.status == 'accepted':
                    messages.info(request, f'You are already friends with {to_user.username}!')
                elif existing.status == 'pending':
                    messages.info(request, f'Friend request with {to_user.username} is already pending.')
                elif existing.status == 'declined':
                    # Allow resending after decline - UPDATE TIMESTAMP
                    existing.from_user = request.user
                    existing.to_user = to_user
                    existing.status = 'pending'
                    existing.created_at = timezone.now()  # ← ADD THIS LINE
                    existing.save()
                    messages.success(request, f'Friend request sent to {to_user.username}!')
            else:
                # Create new friend request
                FriendRequest.objects.create(
                    from_user=request.user,
                    to_user=to_user,
                    status='pending'
                )
                messages.success(request, f'Friend request sent to {to_user.username}!')
        
        except UserProfile.DoesNotExist:
            messages.error(request, 'Invalid friend code. Please check and try again.')
    
    return redirect('friends_dashboard')


from django.db.models import Q
from .models import Artist, FriendRequest


@login_required
@login_required
def user_profile(request, username):
    """View another user's public profile."""
    
    # Get the user or 404
    profile_user = get_object_or_404(User, username=username)
    user_profile = profile_user.profile
    # Check if they're friends
    are_friends = FriendRequest.objects.are_friends(request.user, profile_user)
    can_view = user_profile.can_view_profile(request.user)
    # Check for existing friend request
    existing_request = None
    if request.user != profile_user:
        existing_request = FriendRequest.objects.filter(
            Q(from_user=request.user, to_user=profile_user) |
            Q(from_user=profile_user, to_user=request.user)
        ).first()
    
    # Determine if own profile or friends
    is_own_profile = request.user == profile_user
    can_view_artists = can_view
    
    # Get user's artists based on privacy settings
    user_artists = []
    show_artists = False
    
    if can_view_artists:
        user_artists = SoundCloudArtist.objects.filter(
            user=profile_user
        ).order_by('-rating', 'name')[:6]
        show_artists = True
    
    context = {
        'profile_user': profile_user,
        'are_friends': are_friends,
        'existing_request': existing_request,
        'is_own_profile': is_own_profile,
        'user_artists': user_artists,
        'show_artists': show_artists,
    }
    
    return render(request, 'user/user_profile.html', context)

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.http import JsonResponse
from .models import Artist, Album  # Update this in views.py
from .forms import ArtistForm
import logging

logger = logging.getLogger(__name__)

try:
    from .services.musicbrainz import MusicBrainzAPI
except ImportError as e:
    logger.error(f"Failed to import MusicBrainzAPI: {e}")
    MusicBrainzAPI = None

@login_required
def artist_wallet(request):
    """Main artist wallet view"""
    # Handle artist deletion
    if request.method == 'POST' and 'delete_artist_id' in request.POST:
        artist_id = request.POST.get('delete_artist_id')
        try:
            artist = Artist.objects.get(id=artist_id, user=request.user)
            artist_name = artist.name
            artist.delete()
            messages.success(request, f'Artist "{artist_name}" removed successfully!')
        except Artist.DoesNotExist:
            messages.error(request, 'Artist not found.')
        return redirect('user_artist')
    
    # Handle manual artist addition
    if request.method == 'POST' and 'name' in request.POST:
        form = ArtistForm(request.POST)
        if form.is_valid():
            artist = form.save(commit=False)
            artist.user = request.user
            artist.save()
            messages.success(request, f'Artist "{artist.name}" added successfully!')
            return redirect('user_artist')
    else:
        form = ArtistForm()
    
    # Get user's artists with their albums
    artists_list = Artist.objects.filter(user=request.user).prefetch_related('albums').order_by('-created_at')
    
    paginator = Paginator(artists_list, 10)
    page_number = request.GET.get('page', 1)
    artists = paginator.get_page(page_number)
    
    context = {
        'form': form,
        'artists': artists,
    }
    return render(request, 'user/user_artist.html', context)


@login_required
def search_artists_api(request):
    """AJAX endpoint to search for artists using MusicBrainz API"""
    try:
        query = request.GET.get('query', '').strip()
        
        if not query or len(query) < 2:
            return JsonResponse({'artists': []})
        
        if MusicBrainzAPI is None:
            return JsonResponse({
                'error': 'API service not configured properly',
                'artists': []
            }, status=500)
        
        api = MusicBrainzAPI()
        artists = api.search_artists(query, limit=15)
        
        return JsonResponse({'artists': artists})
        
    except Exception as e:
        logger.error(f"Error in search_artists_api: {str(e)}", exc_info=True)
        return JsonResponse({
            'error': f'Search failed: {str(e)}',
            'artists': []
        }, status=500)


@login_required
def add_artist_from_api(request):
    """Add an artist from MusicBrainz API search results"""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=400)
    
    try:
        artist_id = request.POST.get('artist_id')
        artist_name = request.POST.get('artist_name')
        country = request.POST.get('country', '')
        disambiguation = request.POST.get('disambiguation', '')
        genres = request.POST.get('genres', '')
        
        logger.info(f"User {request.user.username} adding artist: {artist_name}")
        
        if not artist_id or not artist_name:
            return JsonResponse({'error': 'Missing required fields', 'success': False}, status=400)
        
        # Check if artist already exists for this user
        if Artist.objects.filter(user=request.user, musicbrainz_id=artist_id).exists():
            return JsonResponse({
                'error': 'You already have this artist in your wallet',
                'success': False
            }, status=400)
        
        if MusicBrainzAPI is None:
            return JsonResponse({
                'error': 'API service not configured properly',
                'success': False
            }, status=500)
        
        # Get additional details from API
        api = MusicBrainzAPI()
        details = api.get_artist_details(artist_id)
        
        # Try to get artist image
        image_url = None
        if details:
            image_url = api.get_artist_image(artist_id)
        
        # Extract profile URL from relationships
        profile_url = ''
        if details and 'relations' in details:
            for relation in details.get('relations', []):
                if relation.get('type') in ['official homepage', 'social network']:
                    profile_url = relation.get('url', {}).get('resource', '')
                    break
        
# Create artist first
        artist = Artist.objects.create(
            user=request.user,
            name=artist_name,
            musicbrainz_id=artist_id,
            profile_url=profile_url,
            genre=genres or 'Not specified',
            country=country,
            disambiguation=disambiguation,
            artist_image=image_url,
            rating=5
        )
        
        logger.info(f"Created artist {artist_name} (ID: {artist.id})")
        
        # Fetch and save albums - with better error handling
        albums_created = 0
        try:
            logger.info(f"Attempting to fetch albums for MusicBrainz ID: {artist_id}")
            albums_data = api.get_artist_albums(artist_id, limit=5)
            logger.info(f"API returned {len(albums_data)} albums")
            
            for album_data in albums_data:
                try:
                    album = Album.objects.create(
                        artist=artist,
                        title=album_data.get('title', 'Unknown Title'),
                        release_date=album_data.get('release_date', ''),
                        album_type=album_data.get('type', 'Album'),
                        musicbrainz_id=album_data.get('id', ''),
                        cover_art_url=album_data.get('cover_art', '')
                    )
                    albums_created += 1
                    logger.info(f"Created album: {album.title}")
                except Exception as album_error:
                    logger.error(f"Error creating album: {album_error}")
                    continue
            
            logger.info(f"Successfully created {albums_created} albums for {artist_name}")
        except Exception as albums_error:
            logger.error(f"Error fetching albums: {albums_error}", exc_info=True)
        
        return JsonResponse({
            'success': True,
            'message': f'Artist "{artist_name}" added with {albums_created} albums!',
            'artist_id': artist.id,
            'albums_count': albums_created
        })
        
    except Exception as e:
        logger.error(f"Error adding artist: {str(e)}", exc_info=True)
        return JsonResponse({
            'error': f'Failed to add artist: {str(e)}',
            'success': False
        }, status=500)


@login_required
def music_profile_view(request):
    """
    Display the user's AI-generated music profile.
    Only generates when user clicks the "Generate Profile" button.
    """
    
    context = {
        'profile_generated': False,
    }
    
    # Only generate profile if user submitted the form
    if request.method == 'POST':
        result = get_music_profile(request.user)
        
        if result['success']:
            context['profile_generated'] = True
            context['profile'] = result['profile']
            # Save to session so it shows on dashboard
            request.session['music_profile'] = result['profile']
        else:
            messages.error(request, result['message'])
    
    return render(request, 'user/music_profile.html', context)

@login_required
def ratings_view(request):
    """
    Display the user's song and album ratings.
    """
    
    context = {
        # You can add ratings data here when you implement the rating system
        # For now, we'll show a placeholder
    }
    
    return render(request, 'user/ratings.html', context)