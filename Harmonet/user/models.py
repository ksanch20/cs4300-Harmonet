from django.db import models
from django.contrib.auth.models import User


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
