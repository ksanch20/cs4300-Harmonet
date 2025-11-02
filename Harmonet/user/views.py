from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout as auth_logout
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from .forms import UserRegisterForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
import spotipy
from spotipy.oauth2 import SpotifyOAuth


from django.conf import settings
from .models import MusicPreferences


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
    return render(request, 'user/dashboard.html', {'title': 'Dashboard'})

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

# Spotify scopes
scope = "user-top-read user-read-recently-played"

# -----------------------------
# Step 1: Spotify login
# -----------------------------
@login_required
def spotify_login(request):
    """
    Start the Spotify OAuth flow. Requires user to be logged in to your site.
    """
    sp_oauth = SpotifyOAuth(
        client_id=settings.SPOTIPY_CLIENT_ID,
        client_secret=settings.SPOTIPY_CLIENT_SECRET,
        redirect_uri=settings.SPOTIPY_REDIRECT_URI,
        scope=scope,
        cache_path=None  # Optional: we store token in session, not cache file
    )
    auth_url = sp_oauth.get_authorize_url()
    return redirect(auth_url)

# -----------------------------
# Step 2: Spotify callback
# -----------------------------

@login_required
def spotify_login(request):
    sp_oauth = SpotifyOAuth(
        client_id=settings.SPOTIPY_CLIENT_ID,
        client_secret=settings.SPOTIPY_CLIENT_SECRET,
        redirect_uri=settings.SPOTIPY_REDIRECT_URI,
        scope=scope,
        cache_path=None
    )
    return redirect(sp_oauth.get_authorize_url())

@login_required
def spotify_callback(request):
    sp_oauth = SpotifyOAuth(
        client_id=settings.SPOTIPY_CLIENT_ID,
        client_secret=settings.SPOTIPY_CLIENT_SECRET,
        redirect_uri=settings.SPOTIPY_REDIRECT_URI,
        scope=scope,
        cache_path=None
    )
    code = request.GET.get('code')
    if code:
        token_info = sp_oauth.get_access_token(code)
        request.session['spotify_token'] = token_info
    return redirect('account_link')  # After linking, go back here


# -----------------------------
# Step 3: Spotify Dashboard (optional)
# -----------------------------
@login_required
def spotify_dashboard(request):
    """
    Example page showing top Spotify artists and tracks.
    """
    token_info = request.session.get('spotify_token', None)
    if not token_info:
        return redirect('spotify_login')

    sp = spotipy.Spotify(auth=token_info['access_token'])
    top_artists = sp.current_user_top_artists(limit=5)['items']
    top_tracks = sp.current_user_top_tracks(limit=5)['items']

    return render(request, 'dashboard.html', {
        'artists': top_artists,
        'tracks': top_tracks,
    })

#########################SoundCloud Form################################################
@login_required
def dashboard(request):
    user = request.user
    artists = SoundCloudArtist.objects.filter(user=user)

    if request.method == 'POST':
        form = SoundCloudArtistForm(request.POST)
        if form.is_valid():
            artist = form.save(commit=False)
            artist.user = user
            artist.save()
            return redirect('dashboard')  # reload dashboard
    else:
        form = SoundCloudArtistForm()

    context = {
        'form': form,
        'artists': artists,
    }

    return render(request, 'user/dashboard.html', context)

    
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