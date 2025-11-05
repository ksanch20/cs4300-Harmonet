from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

#Stores additional music preferences that users manually input

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

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
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='soundcloud_artists')
    name = models.CharField(max_length=255)
    profile_url = models.URLField(blank=True, null=True)
    added_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.user.username})"

