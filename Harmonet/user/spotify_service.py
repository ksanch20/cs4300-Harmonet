import spotipy
from spotipy.oauth2 import SpotifyOAuth
from django.conf import settings
from datetime import datetime, timedelta
from .models import SpotifyAccount, SpotifyTopArtist, SpotifyTopTrack


def get_spotify_oauth():
    """Create and return SpotifyOAuth object with our app credentials"""
    return SpotifyOAuth(
        client_id=settings.SPOTIPY_CLIENT_ID,
        client_secret=settings.SPOTIPY_CLIENT_SECRET,
        redirect_uri=settings.SPOTIPY_REDIRECT_URI,
        scope="user-top-read user-read-email user-read-private",
        cache_path=None
    )


def save_spotify_connection(user, token_info):
    """
    Save or update Spotify connection for a user
    
    Args:
        user: Django User object
        token_info: Dictionary containing access_token, refresh_token, expires_at
    """
    # Get Spotify user info
    sp = spotipy.Spotify(auth=token_info['access_token'])
    spotify_user = sp.current_user()
    spotify_id = spotify_user['id']
    
    # DEBUG: Print what we got from Spotify
    print(f"=== SPOTIFY USER DATA ===")
    print(f"Harmonets user trying to connect: {user.username} (ID: {user.id})")
    print(f"Spotify ID returned: {spotify_id}")
    print(f"Spotify display name: {spotify_user.get('display_name', 'N/A')}")
    print(f"Spotify email: {spotify_user.get('email', 'N/A')}")
    print(f"========================")
    
    # Calculate token expiration time
    expires_at = datetime.fromtimestamp(token_info['expires_at'])
    
    # Check if this Spotify account is already connected to a DIFFERENT user
    existing_connection = SpotifyAccount.objects.filter(
        spotify_id=spotify_id
    ).exclude(user=user).first()
    
    if existing_connection:
        print(f"❌ ERROR: Spotify ID '{spotify_id}' is already connected to harmonets user: {existing_connection.user.username} (ID: {existing_connection.user.id})")
        raise Exception(
            f"This Spotify account ({spotify_user.get('display_name', spotify_id)}) is already "
            f"connected to another harmonets.org account. Each Spotify account can only be "
            f"connected to one harmonets user account."
        )
    
    # Save or update SpotifyAccount
    spotify_account, created = SpotifyAccount.objects.update_or_create(
        user=user,
        defaults={
            'spotify_id': spotify_id,
            'display_name': spotify_user.get('display_name', ''),
            'email': spotify_user.get('email', ''),
            'access_token': token_info['access_token'],
            'refresh_token': token_info['refresh_token'],
            'token_expires_at': expires_at,
        }
    )
    
    action = "Created" if created else "Updated"
    print(f"✅ {action} Spotify connection for {user.username}")
    
    return spotify_account

def get_valid_token(user):
    """
    Get a valid access token for the user, refreshing if needed
    
    Args:
        user: Django User object
    
    Returns:
        str: Valid access token or None if user not connected
    """
    try:
        spotify_account = user.spotify_account
    except SpotifyAccount.DoesNotExist:
        return None
    
    # Check if token is expired
    now = datetime.now()
    if now >= spotify_account.token_expires_at:
        # Refresh the token
        sp_oauth = get_spotify_oauth()
        token_info = sp_oauth.refresh_access_token(spotify_account.refresh_token)
        
        # Update stored token
        spotify_account.access_token = token_info['access_token']
        spotify_account.refresh_token = token_info['refresh_token']
        spotify_account.token_expires_at = datetime.fromtimestamp(token_info['expires_at'])
        spotify_account.save()
    
    return spotify_account.access_token


def fetch_and_save_top_artists(user):
    """
    Fetch user's top 5 artists from Spotify and save to database
    
    Args:
        user: Django User object
    
    Returns:
        bool: True if successful, False otherwise
    """
    access_token = get_valid_token(user)
    if not access_token:
        return False
    
    try:
        sp = spotipy.Spotify(auth=access_token)
        top_artists = sp.current_user_top_artists(limit=5, time_range='medium_term')
        
        # Delete old top artists for this user
        SpotifyTopArtist.objects.filter(user=user).delete()
        
        # Save new top artists
        for rank, artist in enumerate(top_artists['items'], start=1):
            SpotifyTopArtist.objects.create(
                user=user,
                spotify_artist_id=artist['id'],
                name=artist['name'],
                image_url=artist['images'][0]['url'] if artist['images'] else '',
                genres=', '.join(artist['genres'][:3]),
                popularity=artist['popularity'],
                followers=artist['followers']['total'],
                rank=rank
            )
        
        return True
    except Exception as e:
        print(f"Error fetching top artists: {e}")
        return False


def fetch_and_save_top_tracks(user):
    """
    Fetch user's top 5 tracks from Spotify and save to database
    
    Args:
        user: Django User object
    
    Returns:
        bool: True if successful, False otherwise
    """
    access_token = get_valid_token(user)
    if not access_token:
        return False
    
    try:
        sp = spotipy.Spotify(auth=access_token)
        top_tracks = sp.current_user_top_tracks(limit=5, time_range='medium_term')
        
        # Delete old top tracks for this user
        SpotifyTopTrack.objects.filter(user=user).delete()
        
        # Save new top tracks
        for rank, track in enumerate(top_tracks['items'], start=1):
            SpotifyTopTrack.objects.create(
                user=user,
                spotify_track_id=track['id'],
                name=track['name'],
                artist_name=track['artists'][0]['name'],
                album_name=track['album']['name'],
                album_image_url=track['album']['images'][0]['url'] if track['album']['images'] else '',
                popularity=track['popularity'],
                rank=rank
            )
        
        return True
    except Exception as e:
        print(f"Error fetching top tracks: {e}")
        return False


def is_spotify_connected(user):
    """
    Check if user has connected their Spotify account
    
    Args:
        user: Django User object
    
    Returns:
        bool: True if connected, False otherwise
    """
    return hasattr(user, 'spotify_account')


def disconnect_spotify(user):
    """
    Disconnect user's Spotify account and delete all associated data
    
    Args:
        user: Django User object
    """
    try:
        user.spotify_account.delete()
        SpotifyTopArtist.objects.filter(user=user).delete()
        SpotifyTopTrack.objects.filter(user=user).delete()
    except SpotifyAccount.DoesNotExist:
        pass
