from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import SoundCloudArtist

class UserRegisterForm(UserCreationForm):
    email = forms.EmailField()
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("A user with that email already exists.")
        return email

GENRE_CHOICES = [
    ('', 'Select Genre'), 
    ('Rap', 'Rap'),
    ('Pop', 'Pop'),
    ('Rock', 'Rock'),
    ('Hip-Hop', 'Hip-Hop'),
    ('Electronic', 'Electronic'),
    ('Other', 'Other'),
]

AVERAGE_TIME_CHOICES = [
    ('', 'Select Average Time'),
    ('5', '5 minutes'),
    ('10', '10 minutes'),
    ('15', '15 minutes'),
    ('20', '20 minutes'),
    ('30', '30 minutes'),
    ('45', '45 minutes'),
    ('60', '60 minutes'),
    ('90', '90 minutes'),
]

RATING_CHOICES = [
    ('', 'Select Rating'),
    ('1', '1'),
    ('2', '2'),
    ('3', '3'),
    ('4', '4'),
    ('5', '5'),
]

class SoundCloudArtistForm(forms.ModelForm):
    genre = forms.ChoiceField(
        choices=GENRE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    average_time_listened = forms.ChoiceField(
        choices=AVERAGE_TIME_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    rating = forms.ChoiceField(
        choices=RATING_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=False
    )

    class Meta:
        model = SoundCloudArtist
        fields = ['name', 'profile_url', 'genre', 'average_time_listened', 'rating']
        labels = {
            'name': 'Artist Name',
            'profile_url': 'SoundCloud Profile URL',
            'genre': 'Genre',
            'average_time_listened': 'Average Time Listened (minutes)',
            'rating': 'Rating (1-5)',
        }
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'e.g., Fred again..', 'class': 'form-control'}),
            'profile_url': forms.URLInput(attrs={'placeholder': 'https://soundcloud.com/artist', 'class': 'form-control'}),
        }

    def clean_average_time_listened(self):
        avg_time = self.cleaned_data.get('average_time_listened')
        if avg_time:
            avg_time = int(avg_time)
            if avg_time < 0:
                raise forms.ValidationError("Average time listened cannot be negative.")
        return avg_time

    def clean_rating(self):
        rating = self.cleaned_data.get('rating')
        if rating:
            rating = int(rating)
            if rating < 1 or rating > 5:
                raise forms.ValidationError("Rating must be between 1 and 5.")
            return rating
        return None
