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
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='soundcloud_artists')
    name = models.CharField(max_length=255)
    profile_url = models.URLField(blank=True, null=True)
    added_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.user.username})"
