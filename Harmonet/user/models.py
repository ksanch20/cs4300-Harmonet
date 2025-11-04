from django.db import models
from django.contrib.auth.models import User

class friendsList(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="user")
    
    friends = ManytoManyField(settings.AUTH_USER_MODEL, blank=True, related_name="friends")
    
    def __str__(self):
        return f"{self.user.username}'s friends list"
    def add_friend(self, account):
        if not account in self.friends.all():
            self.friends.add(account)
            self.save()
    def remove_friend(self, account):
        
        if account in self.friends.all():
            self.friends.remove(account)
    def unfriend(self, removee):
        
        remover_friends_list = self
        
        remover_friends_list.remove_friend(removee)
        
        friendsList = friendsList.objects.get(user=remove)
        friends_list.remove_friend(self.user)
        
    def is_mutual_friend(self, friend):
        if friend in self.friends.all():
            return true
        return false
class friendRequests(models.Model):
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="sender")
    reciever = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="receiver")
    
    is_active = models.BooleanField(blank=true, null=false, default=true)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __self__(self):
        return self.sender.username
    
    def accept(self):
        receiver_friend_list = friendsList.object.get(user=self.reciever)
        if reciever_friend_list:
            reciever_friend_list.add_friend(self.sender)
            sender_friend_list = friendsList.object.get(user=self.sender)
            if sender_friend_list:
                sender_friend_list.add_friend(self.reciever)
                self.is_active = False
                self.save()
    def decline(self):
        self.is_active = False
        self.save()

#Stores additional music preferences that users manually input
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
