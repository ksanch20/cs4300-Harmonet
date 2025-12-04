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
        scope="user-top-read user-read-email user-read-private user-read-recently-played user-library-read user-follow-read playlist-read-private playlist-read-collaborative",
        cache_path=None,
        show_dialog=True  # ← ADD THIS LINE - Forces Spotify to show login dialog
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
    #print(f"=== SPOTIFY USER DATA ===")
    #print(f"Harmonets user trying to connect: {user.username} (ID: {user.id})")
    #print(f"Spotify ID returned: {spotify_id}")
    #print(f"Spotify display name: {spotify_user.get('display_name', 'N/A')}")
    #print(f"Spotify email: {spotify_user.get('email', 'N/A')}")
    #print(f"========================")
    
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

# Add these functions to user/spotify_service.py

def get_user_playlists(user):
    """
    Get user's Spotify playlists
    
    Args:
        user: Django User object
    
    Returns:
        list: List of playlist dictionaries or empty list if error
    """
    access_token = get_valid_token(user)
    if not access_token:
        return []
    
    try:
        sp = spotipy.Spotify(auth=access_token)
        playlists = sp.current_user_playlists(limit=50)
        
        playlist_data = []
        for playlist in playlists['items']:
            playlist_data.append({
                'id': playlist['id'],
                'name': playlist['name'],
                'tracks_total': playlist['tracks']['total'],
                'public': playlist['public'],
                'image_url': playlist['images'][0]['url'] if playlist['images'] else '',
                'external_url': playlist['external_urls']['spotify']
            })
        
        return playlist_data
    except Exception as e:
        print(f"Error fetching playlists: {e}")
        return []


def get_user_stats(user):
    """
    Get comprehensive user statistics from Spotify
    
    Args:
        user: Django User object
    
    Returns:
        dict: Dictionary containing various user statistics
    """
    access_token = get_valid_token(user)
    if not access_token:
        return None
    
    try:
        sp = spotipy.Spotify(auth=access_token)
        
        # Get top artists (different time ranges)
        top_artists_short = sp.current_user_top_artists(limit=10, time_range='short_term')
        top_artists_medium = sp.current_user_top_artists(limit=10, time_range='medium_term')
        top_artists_long = sp.current_user_top_artists(limit=10, time_range='long_term')
        
        # Get top tracks (different time ranges)
        top_tracks_short = sp.current_user_top_tracks(limit=10, time_range='short_term')
        top_tracks_medium = sp.current_user_top_tracks(limit=10, time_range='medium_term')
        top_tracks_long = sp.current_user_top_tracks(limit=10, time_range='long_term')
        
        # Get user's saved tracks count
        saved_tracks = sp.current_user_saved_tracks(limit=1)
        
        # Get user's followed artists
        followed_artists = sp.current_user_followed_artists(limit=1)
        
        # Extract top genres from top artists
        all_genres = []
        for artist in top_artists_medium['items']:
            all_genres.extend(artist['genres'])
        
        # Count genre occurrences
        from collections import Counter
        genre_counts = Counter(all_genres)
        top_genres = [{'name': genre, 'count': count} for genre, count in genre_counts.most_common(5)]
        
        stats = {
            'top_artists_short': top_artists_short['items'][:5],
            'top_artists_medium': top_artists_medium['items'][:5],
            'top_artists_long': top_artists_long['items'][:5],
            'top_tracks_short': top_tracks_short['items'][:5],
            'top_tracks_medium': top_tracks_medium['items'][:5],
            'top_tracks_long': top_tracks_long['items'][:5],
            'total_saved_tracks': saved_tracks['total'],
            'total_followed_artists': followed_artists['artists']['total'],
            'top_genres': top_genres
        }
        
        return stats
        
    except Exception as e:
        print(f"Error fetching user stats: {e}")
        return None


def get_recently_played(user, limit=20):
    """
    Get user's recently played tracks
    
    Args:
        user: Django User object
        limit: Number of tracks to retrieve (max 50)
    
    Returns:
        list: List of recently played tracks or empty list if error
    """
    access_token = get_valid_token(user)
    if not access_token:
        return []
    
    try:
        sp = spotipy.Spotify(auth=access_token)
        results = sp.current_user_recently_played(limit=limit)
        
        recent_tracks = []
        for item in results['items']:
            track = item['track']
            recent_tracks.append({
                'name': track['name'],
                'artist': track['artists'][0]['name'],
                'album': track['album']['name'],
                'image_url': track['album']['images'][0]['url'] if track['album']['images'] else '',
                'played_at': item['played_at'],
                'external_url': track['external_urls']['spotify']
            })
        
        return recent_tracks
    except Exception as e:
        print(f"Error fetching recently played: {e}")
        return []
