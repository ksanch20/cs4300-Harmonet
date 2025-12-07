from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models import Q
import random
import string
from django.db.models.signals import post_save
from django.dispatch import receiver

#Stores additional music preferences that users manually input

class FriendRequestManager(models.Manager):
    def friends(self, user):
        """Get all friends of a user"""
        friend_ids = self.filter(
            models.Q(from_user=user, status='accepted') |
            models.Q(to_user=user, status='accepted')
        ).values_list('from_user_id', 'to_user_id')
        
        # Flatten and get unique user IDs excluding the user themselves
        ids = set()
        for from_id, to_id in friend_ids:
            ids.add(from_id if from_id != user.id else to_id)
        
        return User.objects.filter(id__in=ids)
    
    def pending_requests(self, user):
        """Get pending friend requests received by user"""
        return self.filter(to_user=user, status='pending')
    
    def are_friends(self, user1, user2):
        """Check if two users are friends"""
        return self.filter(
            models.Q(from_user=user1, to_user=user2, status='accepted') |
            models.Q(from_user=user2, to_user=user1, status='accepted')
        ).exists()


class FriendRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('declined', 'Declined'),
    ]
    
    from_user = models.ForeignKey(User, related_name='friend_requests_sent', on_delete=models.CASCADE)
    to_user = models.ForeignKey(User, related_name='friend_requests_received', on_delete=models.CASCADE)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Add the custom manager HERE, inside the model class
    objects = FriendRequestManager()
    
    class Meta:
        unique_together = ('from_user', 'to_user')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.from_user.username} -> {self.to_user.username} ({self.status})"



        
class MusicPreferences(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='music_preferences')
    favorite_artists = models.TextField(blank=True, help_text="Comma-separated list of favorite artists")
    favorite_genres = models.TextField(blank=True, help_text="Comma-separated list of favorite music genres")
    favorite_tracks = models.TextField(blank=True, help_text="Comma-separated list of favorite tracks")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s Music Preferences"

    #Converts comma-seperated artists string into a clean Python list
    def get_artists_list(self):
        if not self.favorite_artists:
            return [] 
        #split by comma, strip whitespace from each item, filter out empty strings
        return [artist.strip() for artist in self.favorite_artists.split(',') if artist.strip()]

    #Converts comma-seperated genres string into a clean Python list
    def get_genres_list(self):
        if not self.favorite_genres:
            return []
        #split by comma, strip whitespace from each item, filter out empty strings
        return [genre.strip() for genre in self.favorite_genres.split(',') if genre.strip()]
   
    #Converts comma-seperated tracks string into a clean Python list
    def get_tracks_list(self):
        if not self.favorite_tracks:
            return []
        #split by comma, strip whitespace from each item, filter out empty strings
        return [track.strip() for track in self.favorite_tracks.split(',') if track.strip()]


    class Meta:
        verbose_name_plural = "Music Preferences"
        
        
class SoundCloudArtist(models.Model):

    GENRE_CHOICES = [
        ('Rap', 'Rap'),
        ('Pop', 'Pop'),
        ('Rock', 'Rock'),
        ('Hip-Hop', 'Hip-Hop'),
        ('Electronic', 'Electronic'),
        ('Other', 'Other'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='soundcloud_artists')
    name = models.CharField(max_length=255)
    profile_url = models.URLField(blank=True, null=True)
    genre = models.CharField(max_length=100, blank=True, null=True, choices=GENRE_CHOICES)
    average_time_listened = models.FloatField(blank=True, null=True, help_text="Average listening time in minutes")
    

    rating = models.IntegerField(
        blank=True,
        null=True,
        choices=[(i, str(i)) for i in range(1, 6)],
        help_text="Rate this artist from 1 to 5"
    )

    added_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.user.username})"

class SpotifyAccount(models.Model):
    """Store Spotify account connection info for each user"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='spotify_account')
    
    # Spotify user info
    spotify_id = models.CharField(max_length=255, unique=True)
    display_name = models.CharField(max_length=255, blank=True)
    email = models.EmailField(blank=True)
    
    # OAuth tokens
    access_token = models.TextField()
    refresh_token = models.TextField()
    token_expires_at = models.DateTimeField()
    
    # Connection timestamps
    connected_at = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username} - Spotify: {self.display_name}"
    
    class Meta:
        verbose_name = "Spotify Account"
        verbose_name_plural = "Spotify Accounts"


class SpotifyTopArtist(models.Model):
    """Cache user's top Spotify artists"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='top_artists')
    
    # Artist info from Spotify
    spotify_artist_id = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    image_url = models.URLField(blank=True)
    genres = models.CharField(max_length=500, blank=True)
    popularity = models.IntegerField(default=0)
    followers = models.IntegerField(default=0)
    
    # Metadata
    rank = models.IntegerField(default=0)
    fetched_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['rank']
        unique_together = ['user', 'rank']
    
    def __str__(self):
        return f"{self.user.username} - #{self.rank}: {self.name}"


class SpotifyTopTrack(models.Model):
    """Cache user's top Spotify tracks"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='top_tracks')
    
    # Track info from Spotify
    spotify_track_id = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    artist_name = models.CharField(max_length=255)
    album_name = models.CharField(max_length=255)
    album_image_url = models.URLField(blank=True)
    popularity = models.IntegerField(default=0)
    
    # Metadata
    rank = models.IntegerField(default=0)
    fetched_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['rank']
        unique_together = ['user', 'rank']
    
    def __str__(self):
        return f"{self.user.username} - #{self.rank}: {self.name}"


class UserProfile(models.Model):
    """Extended user profile with friend code."""
    
    PRIVACY_CHOICES = [
        ('public', 'Public'),
        ('friends', 'Friends Only'),
        ('private', 'Private'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    friend_code = models.CharField(max_length=20, unique=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    privacy = models.CharField(
        max_length=10, 
        choices=PRIVACY_CHOICES, 
        default='public',
        help_text="Control who can see your profile and music data")
    
    def save(self, *args, **kwargs):
        if not self.friend_code:
            self.friend_code = self.generate_friend_code()
        super().save(*args, **kwargs)
    
    @staticmethod
    def generate_friend_code():
        """Generate a unique, user-friendly friend code."""
        # Format: MUSIC-XXXXX (e.g., MUSIC-A7X9K)
        while True:
            # Generate 5 random alphanumeric characters (excluding confusing ones)
            chars = ''.join(random.choices('ABCDEFGHJKLMNPQRSTUVWXYZ23456789', k=5))
            code = f'MUSIC-{chars}'
            
            # Check if code already exists
            if not UserProfile.objects.filter(friend_code=code).exists():
                return code
            
    def can_view_profile(self, viewer):
        """Check if a user can view this profile based on privacy settings."""
        # User can always view their own profile
        if viewer == self.user:
            return True
        
        # Public profiles can be viewed by anyone
        if self.privacy == 'public':
            return True
        
        # Private profiles can only be viewed by the owner
        if self.privacy == 'private':
            return False
        
        # Friends-only: check if viewer is a friend
        if self.privacy == 'friends':
            return FriendRequest.objects.are_friends(self.user, viewer)
        
        return False
    def get_privacy_display(self):
        privacy_dict = dict(self.PRIVACY_CHOICES)
        return privacy_dict.get(self.privacy, self.privacy)
    def __str__(self):
        return f"{self.user.username} ({self.friend_code})"

# Signal to auto-create profile when user is created
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, 'profile'):
        instance.profile.save()

from django.db import models
from django.contrib.auth.models import User

# ... other models ...

class Artist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='artists')
    name = models.CharField(max_length=255)
    musicbrainz_id = models.CharField(max_length=100, blank=True, null=True)
    profile_url = models.URLField(blank=True, null=True)
    genre = models.CharField(max_length=100, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)
    disambiguation = models.CharField(max_length=255, blank=True, null=True)
    artist_image = models.URLField(blank=True, null=True)
    
    # User tracking fields
    average_time_listened = models.IntegerField(
        null=True,
        blank=True,
        help_text="Average minutes listened per week"
    )
    rating = models.IntegerField(
        choices=[(i, i) for i in range(1, 6)],
        null=True,
        blank=True,
        help_text="Rate this artist from 1 to 5 stars"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ['user', 'musicbrainz_id']

    def __str__(self):
        return self.name


# Album model MUST come AFTER Artist model
class Album(models.Model):
    artist = models.ForeignKey(Artist, on_delete=models.CASCADE, related_name='albums')
    title = models.CharField(max_length=200)
    release_date = models.CharField(max_length=100, blank=True, null=True)
    album_type = models.CharField(max_length=50, blank=True, null=True)  # Album, EP, Single
    musicbrainz_id = models.CharField(max_length=100, blank=True, null=True)
    cover_art_url = models.URLField(blank=True, null=True)
    
    # Rating field for album ratings (1-5 stars)
    rating = models.IntegerField(
        choices=[(i, i) for i in range(1, 6)],
        null=True,
        blank=True,
        help_text="Rate this album from 1 to 5 stars"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-release_date']

    def __str__(self):
        return f"{self.title} - {self.artist.name}"



class Song(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='songs')
    title = models.CharField(max_length=255)
    artist_name = models.CharField(max_length=255)
    musicbrainz_id = models.CharField(max_length=100, blank=True, null=True)
    album_name = models.CharField(max_length=255, blank=True, null=True)
    release_date = models.CharField(max_length=100, blank=True, null=True)
    duration = models.IntegerField(blank=True, null=True, help_text="Duration in milliseconds")
    
    # User tracking fields
    rating = models.IntegerField(
        choices=[(i, i) for i in range(1, 6)],
        null=True,
        blank=True,
        help_text="Rate this song from 1 to 5 stars"
    )
    times_played = models.IntegerField(
        default=0,
        help_text="Number of times played"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ['user', 'musicbrainz_id']

    def __str__(self):
        return f"{self.title} - {self.artist_name}"
    
    def get_duration_display(self):
        """Convert milliseconds to MM:SS format"""
        if not self.duration:
            return "Unknown"
        seconds = self.duration // 1000
        minutes = seconds // 60
        remaining_seconds = seconds % 60
        return f"{minutes}:{remaining_seconds:02d}"