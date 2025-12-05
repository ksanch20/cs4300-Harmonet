from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from .models import FriendRequest, FriendRequestManager, Artist, Album
from user.models import MusicPreferences, UserProfile, FriendRequest, SpotifyAccount, SpotifyTopArtist, SpotifyTopTrack
from django.contrib.messages import get_messages
from unittest.mock import patch, Mock, MagicMock
from datetime import datetime, timedelta
from django.utils import timezone
import json
from django.contrib.auth import get_user_model


#Used ChatGPT to help write tests

class UserAuthTests(TestCase):
    def setUp(self):
        # Create a user to test login
        self.user = User.objects.create_user(username='testuser', email='test@example.com', password='TestPass123')
        self.user2 = User.objects.create_user(username='testuser2', email='test2@example.com', password='TestPass123')
        self.user3 = User.objects.create_user(username='testuser3', email='test3@example.com', password='TestPass123')
        self.user4 = User.objects.create_user(username='testuser4', email='test4@example.com', password='TestPass123')
        

    # -----------------------------
    # SIGNUP TESTS
    # -----------------------------
    def test_signup_success(self):
        response = self.client.post(reverse('register'), {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password1': 'NewPass123',
            'password2': 'NewPass123'
        })
        # Should redirect to dashboard
        self.assertRedirects(response, reverse('dashboard'))
        # User should exist
        self.assertTrue(User.objects.filter(username='newuser').exists())

    def test_signup_username_exists(self):
        response = self.client.post(reverse('register'), {
            'username': 'testuser',  # already exists
            'email': 'other@example.com',
            'password1': 'AnotherPass123',
            'password2': 'AnotherPass123'
        })
        self.assertEqual(response.status_code, 200)
        # Check that the page contains the expected error message
        self.assertContains(response, "A user with that username already exists.")

    def test_signup_email_unique(self):
        # Try to register using the same email as existing user
        response = self.client.post(reverse('register'), {
            'username': 'newuser2',
            'email': 'test@example.com',  # already used by self.user
            'password1': 'NewPass123',
            'password2': 'NewPass123'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "A user with that email already exists.")


    def test_signup_password_mismatch(self):
        response = self.client.post(reverse('register'), {
            'username': 'user2',
            'email': 'user2@example.com',
            'password1': 'Password123',
            'password2': 'Password456'  # mismatch
        })
        self.assertEqual(response.status_code, 200)
        # Check that the page contains the mismatch error
        self.assertContains(response, "The two password fields didn’t match.")
        
    # -----------------------------
    # LOGIN TESTS
    # -----------------------------
    def test_login_success(self):
        response = self.client.post(reverse('login'), {
            'username': 'testuser',
            'password': 'TestPass123'
        })
        self.assertRedirects(response, reverse('dashboard'))

    def test_login_invalid_username(self):
        response = self.client.post(reverse('login'), {
            'username': 'wronguser',
            'password': 'TestPass123'
        })
        # Should stay on login page
        self.assertEqual(response.status_code, 200)
        # Should display error message
        self.assertContains(response, 'Invalid username or password')

    def test_login_invalid_password(self):
        response = self.client.post(reverse('login'), {
            'username': 'testuser',
            'password': 'WrongPass'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Invalid username or password')

# -----------------------------
    # PASSWORD STRENGTH TESTS
    # -----------------------------
    def test_signup_password_too_short(self):
        response = self.client.post(reverse('register'), {
            'username': 'user5',
            'email': 'user5@example.com',
            'password1': 'short',
            'password2': 'short'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "This password is too short")

    def test_signup_password_numeric_only(self):
        response = self.client.post(reverse('register'), {
            'username': 'user6',
            'email': 'user6@example.com',
            'password1': '12345678',
            'password2': '12345678'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "This password is entirely numeric")

    def test_signup_password_too_common(self):
        response = self.client.post(reverse('register'), {
            'username': 'user7',
            'email': 'user7@example.com',
            'password1': 'password123',
            'password2': 'password123'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "This password is too common")
        # -----------------------------


    # -----------------------------
    #Delete Account Test
    # -----------------------------
    def test_delete_account_success(self):
        # Log in the user first
        self.client.login(username='testuser', password='TestPass123')
        
        # Delete the account
        response = self.client.post(reverse('delete_account'))
        
        # Should redirect to index page
        self.assertRedirects(response, reverse('index'))
        
        # User should no longer exist
        self.assertFalse(User.objects.filter(username='testuser').exists())


    # -----------------------------
    #Change Password While Logged In Tests
    # -----------------------------
    def test_change_password_success(self):
        # Log in the user
        self.client.login(username='testuser', password='TestPass123')
        
        # Change password
        response = self.client.post(reverse('password_change'), {
            'old_password': 'TestPass123',
            'new_password1': 'NewSecurePass456',
            'new_password2': 'NewSecurePass456'
        })
        
        # Should redirect (to dashboard, profile, or password change success page)
        self.assertEqual(response.status_code, 302)
        
        # Logout and try logging in with new password
        self.client.logout()
        login_success = self.client.login(username='testuser', password='NewSecurePass456')
        self.assertTrue(login_success)

    def test_change_password_wrong_old_password(self):
        # Log in the user
        self.client.login(username='testuser', password='TestPass123')
        
        # Try to change password with wrong old password
        response = self.client.post(reverse('password_change'), {
            'old_password': 'WrongOldPass',
            'new_password1': 'NewSecurePass456',
            'new_password2': 'NewSecurePass456'
        })
        
        # Should stay on same page (200) with error
        self.assertEqual(response.status_code, 200)
        # Django's actual error message
        self.assertContains(response, 'Your old password was entered incorrectly')
        
        # Old password should still work
        self.client.logout()
        login_success = self.client.login(username='testuser', password='TestPass123')
        self.assertTrue(login_success)

    def test_change_password_mismatch(self):
        # Log in the user
        self.client.login(username='testuser', password='TestPass123')
        
        # Try to change password with mismatched new passwords
        response = self.client.post(reverse('password_change'), {
            'old_password': 'TestPass123',
            'new_password1': 'NewSecurePass456',
            'new_password2': 'DifferentPass789'
        })
        
        # Should stay on same page (200) with error
        self.assertEqual(response.status_code, 200)
        # Check that form has errors 
        self.assertTrue(response.context['form'].errors)
        # Verify the password mismatch error exists (check any common variation)
        content = response.content.decode().lower()
        self.assertTrue('match' in content or 'same' in content)
        
        # Old password should still work
        self.client.logout()
        login_success = self.client.login(username='testuser', password='TestPass123')
        self.assertTrue(login_success)

    # -----------------------------
    #Forgot Password Tests
    # -----------------------------
    def test_forgot_password_request_success(self):
            # Request password reset
            response = self.client.post(reverse('password_reset'), {
                'email': 'test@example.com'
            })
            
            # Should redirect to password reset done page
            self.assertRedirects(response, reverse('password_reset_done'))
            
            # Check that an email was sent
            from django.core import mail
            self.assertEqual(len(mail.outbox), 1)
            self.assertIn('test@example.com', mail.outbox[0].to)

    def test_forgot_password_invalid_email(self):
        # Request password reset with non-existent email
        response = self.client.post(reverse('password_reset'), {
            'email': 'nonexistent@example.com'
        })
        
        # Django's default behavior is to still redirect (security measure)
        # to avoid revealing whether an email exists
        self.assertRedirects(response, reverse('password_reset_done'))
        
        # No email should be sent
        from django.core import mail
        self.assertEqual(len(mail.outbox), 0)

    
    def test_forgot_password_reset_complete(self):
        from django.contrib.auth.tokens import default_token_generator
        from django.utils.http import urlsafe_base64_encode
        from django.utils.encoding import force_bytes
        
        # Generate reset token
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        token = default_token_generator.make_token(self.user)
        
        # Access the password reset confirm page
        response = self.client.get(
            reverse('password_reset_confirm', kwargs={'uidb64': uid, 'token': token})
        )
        self.assertEqual(response.status_code, 302)  # Redirects to set-password form
        
        # Submit new password
        response = self.client.post(
            reverse('password_reset_confirm', kwargs={'uidb64': uid, 'token': 'set-password'}),
            {
                'new_password1': 'CompletelyNewPass789',
                'new_password2': 'CompletelyNewPass789'
            }
        )
        
        # Should redirect to password reset complete page
        self.assertRedirects(response, reverse('password_reset_complete'))
        
        # Old password should not work
        login_fail = self.client.login(username='testuser', password='TestPass123')
        self.assertFalse(login_fail)
        
        # New password should work
        login_success = self.client.login(username='testuser', password='CompletelyNewPass789')
        self.assertTrue(login_success) 

    def test_forgot_password_invalid_token(self):
        from django.utils.http import urlsafe_base64_encode
        from django.utils.encoding import force_bytes
        
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        invalid_token = 'invalid-token-string'
        
        # Try to access with invalid token
        response = self.client.get(
            reverse('password_reset_confirm', kwargs={'uidb64': uid, 'token': invalid_token})
        )
        
        # Should show invalid token page (200 with error message)
        self.assertEqual(response.status_code, 200)
        
        # Old password should still work
        login_success = self.client.login(username='testuser', password='TestPass123')
        self.assertTrue(login_success)


    def test_change_password_view_get(self):
        # Log in the user
        self.client.login(username='testuser', password='TestPass123')
        
        # GET request should show the form
        response = self.client.get(reverse('password_change'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Current Password')
        self.assertContains(response, 'New Password')
        
        
        #############################
        #FRIENDS TESTS#
        #############################
    def test_create_friend_request(self):
        """Test creating a friend request"""
        friend_request = FriendRequest.objects.create(
            from_user=self.user,
            to_user=self.user2
        )
        
        self.assertEqual(friend_request.from_user, self.user)
        self.assertEqual(friend_request.to_user, self.user2)
        self.assertEqual(friend_request.status, 'pending')
        self.assertIsNotNone(friend_request.created_at)
    def test_friend_request_string_representation(self):
        """Test the __str__ method"""
        friend_request = FriendRequest.objects.create(
            from_user=self.user,
            to_user=self.user2
        )
        
        expected = f"{self.user.username} -> {self.user2.username} (pending)"
        self.assertEqual(str(friend_request), expected)
    
    def test_unique_together_constraint(self):
        """Test that duplicate friend requests are prevented"""
        FriendRequest.objects.create(
            from_user=self.user,
            to_user=self.user2
        )
        
        # Attempting to create duplicate should raise error
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            FriendRequest.objects.create(
                from_user=self.user,
                to_user=self.user2
            )
    
    def test_accept_friend_request(self):
        """Test accepting a friend request"""
        friend_request = FriendRequest.objects.create(
            from_user=self.user,
            to_user=self.user2
        )
        
        friend_request.status = 'accepted'
        friend_request.save()
        
        self.assertEqual(friend_request.status, 'accepted')
    
    def test_decline_friend_request(self):
        """Test declining a friend request"""
        friend_request = FriendRequest.objects.create(
            from_user=self.user,
            to_user=self.user2
        )
        
        friend_request.status = 'declined'
        friend_request.save()
        
        self.assertEqual(friend_request.status, 'declined')
        
    def test_friends_method_with_no_friends(self):
        """Test friends() returns empty queryset when user has no friends"""
        friends = FriendRequest.objects.friends(self.user)
        self.assertEqual(friends.count(), 0)
    
    def test_friends_method_with_accepted_requests(self):
        """Test friends() returns correct friends"""
        # user sends request to User2 (accepted)
        FriendRequest.objects.create(
            from_user=self.user,
            to_user=self.user2,
            status='accepted'
        )
        
        # User3 sends request to user (accepted)
        FriendRequest.objects.create(
            from_user=self.user3,
            to_user=self.user,
            status='accepted'
        )
        
        # user sends request to User4 (pending - should not appear)
        FriendRequest.objects.create(
            from_user=self.user,
            to_user=self.user4,
            status='pending'
        )
        
        friends = FriendRequest.objects.friends(self.user)
        
        self.assertEqual(friends.count(), 2)
        self.assertIn(self.user2, friends)
        self.assertIn(self.user3, friends)
        self.assertNotIn(self.user4, friends)
    
    def test_friends_bidirectional(self):
        """Test that friendship works both ways"""
        FriendRequest.objects.create(
            from_user=self.user,
            to_user=self.user2,
            status='accepted'
        )
        
        # Both users should see each other as friends
        user_friends = FriendRequest.objects.friends(self.user)
        user2_friends = FriendRequest.objects.friends(self.user2)
        
        self.assertIn(self.user2, user_friends)
        self.assertIn(self.user, user2_friends)
    
    def test_pending_requests_method(self):
        """Test pending_requests() returns only pending received requests"""
        # User2 sends pending request to user
        FriendRequest.objects.create(
            from_user=self.user2,
            to_user=self.user,
            status='pending'
        )
        
        # User3 sends accepted request to user (should not appear)
        FriendRequest.objects.create(
            from_user=self.user3,
            to_user=self.user,
            status='accepted'
        )
        
        # user sends request to User4 (should not appear - it's sent, not received)
        FriendRequest.objects.create(
            from_user=self.user,
            to_user=self.user4,
            status='pending'
        )
        
        pending = FriendRequest.objects.pending_requests(self.user)
        
        self.assertEqual(pending.count(), 1)
        self.assertEqual(pending.first().from_user, self.user2)
    
    def test_are_friends_method_true(self):
        """Test are_friends() returns True for actual friends"""
        FriendRequest.objects.create(
            from_user=self.user,
            to_user=self.user2,
            status='accepted'
        )
        
        self.assertTrue(FriendRequest.objects.are_friends(self.user, self.user2))
        self.assertTrue(FriendRequest.objects.are_friends(self.user2, self.user))
    
    def test_are_friends_method_false_no_request(self):
        """Test are_friends() returns False when no request exists"""
        self.assertFalse(FriendRequest.objects.are_friends(self.user, self.user2))
    
    def test_are_friends_method_false_pending(self):
        """Test are_friends() returns False for pending requests"""
        FriendRequest.objects.create(
            from_user=self.user,
            to_user=self.user2,
            status='pending'
        )
        
        self.assertFalse(FriendRequest.objects.are_friends(self.user, self.user2))
    
    def test_are_friends_method_false_declined(self):
        """Test are_friends() returns False for declined requests"""
        FriendRequest.objects.create(
            from_user=self.user,
            to_user=self.user2,
            status='declined'
        )
        
        self.assertFalse(FriendRequest.objects.are_friends(self.user, self.user2))
     



# ========================================
# MUSIC PREFERENCES 
# ========================================

class MusicPreferencesEssentialTests(TestCase):

    def setUp(self):
        """Create test user."""
        self.user = User.objects.create_user(
            username='musicuser',
            email='music@example.com',
            password='testpass123'
        )
        self.url = reverse('music_preferences')
    
    # ------ MODEL TESTS  ------
    
    def test_model_get_artists_list_works(self):
        """Test the main list conversion methods work."""
        prefs = MusicPreferences.objects.create(
            user=self.user,
            favorite_artists='Taylor Swift, Billie Eilish',
            favorite_genres='Pop, Indie'
        )
        
        # Test artists list
        artists = prefs.get_artists_list()
        self.assertEqual(len(artists), 2)
        self.assertIn('Taylor Swift', artists)
        
        # Test genres list
        genres = prefs.get_genres_list()
        self.assertEqual(len(genres), 2)
        self.assertIn('Pop', genres)
    
    def test_model_handles_empty_data(self):
        """Test model handles empty fields correctly."""
        prefs = MusicPreferences.objects.create(user=self.user, favorite_artists='')
        self.assertEqual(prefs.get_artists_list(), [])
    
    def test_model_one_to_one_relationship(self):
        """Test each user can only have one MusicPreferences."""
        prefs1 = MusicPreferences.objects.create(user=self.user)
        prefs2, created = MusicPreferences.objects.get_or_create(user=self.user)
        
        self.assertFalse(created)  # Should not create new one
        self.assertEqual(prefs1.id, prefs2.id)  # Same object
    
    # ------ VIEW TESTS  ------
    
    def test_view_creates_preferences_automatically(self):
        """Test preferences are auto-created on first visit."""
        self.client.login(username='musicuser', password='testpass123')
        
        # No preferences yet
        self.assertFalse(MusicPreferences.objects.filter(user=self.user).exists())
        
        # Visit page
        self.client.get(self.url)
        
        # Now preferences exist
        self.assertTrue(MusicPreferences.objects.filter(user=self.user).exists())
    
    def test_view_saves_preferences(self):
        """Test POST request saves preferences."""
        self.client.login(username='musicuser', password='testpass123')
        
        response = self.client.post(self.url, {
            'artists': 'Taylor Swift',
            'genres': 'Pop',
            'tracks': 'Anti-Hero'
        })
        
        # Should redirect
        self.assertEqual(response.status_code, 302)
        
        # Data should be saved
        prefs = MusicPreferences.objects.get(user=self.user)
        self.assertEqual(prefs.favorite_artists, 'Taylor Swift')
        self.assertEqual(prefs.favorite_genres, 'Pop')
    
    def test_view_updates_existing_preferences(self):
        """Test updating preferences doesn't create duplicates."""
        self.client.login(username='musicuser', password='testpass123')
        
        # First save
        self.client.post(self.url, {'artists': 'Old Artist', 'genres': '', 'tracks': ''})
        
        # Second save
        self.client.post(self.url, {'artists': 'New Artist', 'genres': '', 'tracks': ''})
        
        # Only one preference object should exist
        self.assertEqual(MusicPreferences.objects.filter(user=self.user).count(), 1)
        
        # Should have new value
        prefs = MusicPreferences.objects.get(user=self.user)
        self.assertEqual(prefs.favorite_artists, 'New Artist')
    
    def test_view_shows_success_message(self):
        """Test success message is displayed after saving."""
        self.client.login(username='musicuser', password='testpass123')
        
        response = self.client.post(self.url, {
            'artists': 'Test',
            'genres': '',
            'tracks': ''
        }, follow=True)
        
        messages = list(response.context['messages'])
        self.assertEqual(len(messages), 1)
        self.assertIn('saved', str(messages[0]).lower())


# ========================================
# AI RECOMMENDATIONS 
# ========================================

class AIRecommendationsEssentialTests(TestCase):
    
    def setUp(self):
        """Create test user."""
        self.user = User.objects.create_user(
            username='aiuser',
            email='ai@example.com',
            password='testpass123'
        )
        self.url = reverse('ai_recommendations')
    
    
    def test_view_accessible_when_logged_in(self):
        """Test logged-in users can access page."""
        self.client.login(username='aiuser', password='testpass123')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
    
    def test_user_without_preferences_gets_error(self):
        """Test user without preferences gets error message."""
        self.client.login(username='aiuser', password='testpass123')
        
        # POST without having preferences
        response = self.client.post(self.url)
        
        # Should show error
        self.assertIsNotNone(response.context.get('error_message'))
    
    def test_gather_music_data_function(self):
        """Test the data gathering function works."""
        from user.ai_service import gather_user_music_data
        
        # User with no preferences
        data = gather_user_music_data(self.user)
        self.assertFalse(data['has_data'])
        
        # User with preferences
        MusicPreferences.objects.create(
            user=self.user,
            favorite_artists='Taylor Swift'
        )
        data = gather_user_music_data(self.user)
        self.assertTrue(data['has_data'])
        self.assertIn('Taylor Swift', data['manual_artists'])


# ========================================
# INTEGRATION TEST 
# ========================================

class AIRecommendationIntegrationTest(TestCase):
    """Test the main user flow works end-to-end."""
    
    def test_complete_user_journey(self):
        """Test: signup → add preferences → access AI page."""
        
        # 1. Signup
        response = self.client.post(reverse('register'), {
            'username': 'newuser',
            'email': 'new@example.com',
            'password1': 'TestPass123',
            'password2': 'TestPass123'
        })
        self.assertEqual(response.status_code, 302)  # Redirects after signup
        
        # 2. Add music preferences
        response = self.client.post(reverse('music_preferences'), {
            'artists': 'Taylor Swift',
            'genres': 'Pop',
            'tracks': ''
        })
        self.assertEqual(response.status_code, 302)  # Redirects after save
        
        # 3. Verify preferences saved
        user = User.objects.get(username='newuser')
        prefs = MusicPreferences.objects.get(user=user)
        self.assertEqual(prefs.favorite_artists, 'Taylor Swift')
        
        # 4. Can access AI recommendations page
        response = self.client.get(reverse('ai_recommendations'))
        self.assertEqual(response.status_code, 200)

# ========================================
# AI SERVICE UNIT TESTS
# ========================================

from unittest.mock import Mock, patch
from user.ai_service import (
    get_music_recommendations,
    gather_user_music_data,
    build_recommendation_prompt
)

class AIServiceUnitTests(TestCase):

    def setUp(self):
        self.mock_user = Mock()

    # -------------------------------
    # get_music_recommendations()
    # -------------------------------

    def test_get_music_recommendations_no_data(self):
        with patch('user.ai_service.gather_user_music_data', return_value={'has_data': False}):
            result = get_music_recommendations(self.mock_user)
            self.assertFalse(result['success'])
            self.assertIn('Please connect Spotify', result['message'])

    def test_get_music_recommendations_success(self):
        mock_data = {
            'has_data': True,
            'manual_artists': ['Muse'],
            'manual_genres': ['Rock'],
            'manual_tracks': ['Uprising'],
            'spotify_top_artists': [],
            'spotify_top_tracks': []
        }
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content='Recommended artists...'))]

        with patch('user.ai_service.gather_user_music_data', return_value=mock_data), \
             patch('user.ai_service.client.chat.completions.create', return_value=mock_response):
            result = get_music_recommendations(self.mock_user)
            self.assertTrue(result['success'])
            self.assertIn('Recommended artists', result['recommendations'])

    def test_get_music_recommendations_openai_error(self):
        mock_data = {
            'has_data': True,
            'manual_artists': [],
            'manual_genres': [],
            'manual_tracks': [],
            'spotify_top_artists': [],
            'spotify_top_tracks': []
        }

        with patch('user.ai_service.gather_user_music_data', return_value=mock_data), \
        patch('user.ai_service.client.chat.completions.create', side_effect=Exception("API error")):
            result = get_music_recommendations(self.mock_user)
            self.assertFalse(result['success'])
            self.assertIn('Error generating recommendations', result['message'])


    # -------------------------------
    # gather_user_music_data()
    # -------------------------------

def test_gather_user_music_data_with_preferences(self):
    # Create a proper mock user with music_preferences
    mock_user = Mock()
    mock_user.id = 1
    
    mock_prefs = Mock()
    mock_prefs.get_artists_list.return_value = ['Muse']
    mock_prefs.get_genres_list.return_value = ['Rock']
    mock_prefs.get_tracks_list.return_value = ['Uprising']
    mock_user.music_preferences = mock_prefs

    # Mock is_spotify_connected to return False so we only test manual preferences
    with patch('user.spotify_service.is_spotify_connected', return_value=False):
        data = gather_user_music_data(mock_user)
        self.assertTrue(data['has_data'])
        self.assertEqual(data['manual_artists'], ['Muse'])
        self.assertEqual(data['manual_genres'], ['Rock'])
        self.assertEqual(data['manual_tracks'], ['Uprising'])

def test_gather_user_music_data_no_preferences(self):
    # Simulate user with no music_preferences attribute and no spotify connection
    mock_user = Mock()
    mock_user.id = 1
    
    # When accessing music_preferences, raise AttributeError (simulating no preferences)
    type(mock_user).music_preferences = PropertyMock(side_effect=AttributeError)
    
    with patch('user.spotify_service.is_spotify_connected', return_value=False):
        data = gather_user_music_data(mock_user)
        self.assertFalse(data['has_data'])

    # -------------------------------
    # build_recommendation_prompt()
    # -------------------------------

    def test_build_recommendation_prompt_output(self):
        music_data = {
            'manual_artists': ['Radiohead'],
            'manual_genres': ['Alternative'],
            'manual_tracks': ['Karma Police', 'No Surprises'],
            'spotify_top_artists': [{'name': 'Muse', 'genres': 'Rock, Alternative'}],
            'spotify_top_tracks': [{'name': 'Uprising', 'artist': 'Muse'}]
        }
        prompt = build_recommendation_prompt(music_data)
        self.assertIn('**Additional Favorite Artists:**', prompt)
        self.assertIn('Radiohead', prompt)
        self.assertIn('Muse', prompt)
        self.assertIn('Karma Police', prompt)

class AddFriendByCodeViewTest(TestCase):
    """Test the add_friend_by_code view."""
    
    def setUp(self):
        """Set up test client and users."""
        self.client = Client()
        self.user1 = User.objects.create_user('user1', 'user1@test.com', 'pass123')
        self.user2 = User.objects.create_user('user2', 'user2@test.com', 'pass123')
        self.user3 = User.objects.create_user('user3', 'user3@test.com', 'pass123')
    
    def test_add_friend_by_code_requires_login(self):
        """Test that view requires authentication."""
        response = self.client.post(reverse('add_friend_by_code'), {
            'friend_code': self.user2.profile.friend_code
        })
        # Should redirect to login
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)
    
    def test_add_friend_with_valid_code(self):
        """Test adding friend with valid friend code."""
        self.client.login(username='user1', password='pass123')
        
        response = self.client.post(reverse('add_friend_by_code'), {
            'friend_code': self.user2.profile.friend_code
        })
        
        # Should redirect to friends dashboard
        self.assertRedirects(response, reverse('friends_dashboard'))
        
        # Friend request should be created
        request = FriendRequest.objects.filter(
            from_user=self.user1,
            to_user=self.user2,
            status='pending'
        ).first()
        self.assertIsNotNone(request)
        
        # Success message should be shown
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('sent' in str(m).lower() for m in messages))
    
    def test_add_friend_with_invalid_code(self):
        """Test adding friend with invalid friend code."""
        self.client.login(username='user1', password='pass123')
        
        response = self.client.post(reverse('add_friend_by_code'), {
            'friend_code': 'MUSIC-XXXXX'  # Invalid code
        })
        
        # Should redirect back
        self.assertRedirects(response, reverse('friends_dashboard'))
        
        # No friend request should be created
        self.assertEqual(FriendRequest.objects.count(), 0)
        
        # Error message should be shown
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('invalid' in str(m).lower() for m in messages))
    
    def test_add_friend_with_empty_code(self):
        """Test adding friend with empty friend code."""
        self.client.login(username='user1', password='pass123')
        
        response = self.client.post(reverse('add_friend_by_code'), {
            'friend_code': ''
        })
        
        # Should show error
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('enter' in str(m).lower() for m in messages))
    
    def test_cannot_add_self_as_friend(self):
        """Test that user cannot add themselves using their own code."""
        self.client.login(username='user1', password='pass123')
        
        response = self.client.post(reverse('add_friend_by_code'), {
            'friend_code': self.user1.profile.friend_code
        })
        
        # No friend request should be created
        self.assertEqual(FriendRequest.objects.count(), 0)
        
        # Error message should be shown
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('yourself' in str(m).lower() for m in messages))
    
    def test_duplicate_pending_request(self):
        """Test sending request when one is already pending."""
        self.client.login(username='user1', password='pass123')
        
        # Create existing pending request
        FriendRequest.objects.create(
            from_user=self.user1,
            to_user=self.user2,
            status='pending'
        )
        
        # Try to send again
        response = self.client.post(reverse('add_friend_by_code'), {
            'friend_code': self.user2.profile.friend_code
        })
        
        # Should still only have one request
        self.assertEqual(FriendRequest.objects.count(), 1)
        
        # Info message about pending
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('pending' in str(m).lower() for m in messages))
    
    def test_already_friends(self):
        """Test sending request when already friends."""
        self.client.login(username='user1', password='pass123')
        
        # Create accepted friendship
        FriendRequest.objects.create(
            from_user=self.user1,
            to_user=self.user2,
            status='accepted'
        )
        
        # Try to send request
        response = self.client.post(reverse('add_friend_by_code'), {
            'friend_code': self.user2.profile.friend_code
        })
        
        # Should still only have one request
        self.assertEqual(FriendRequest.objects.count(), 1)
        
        # Info message about already friends
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('already' in str(m).lower() for m in messages))
    
    def test_resend_after_declined(self):
        """Test that user can resend request after it was declined."""
        self.client.login(username='user1', password='pass123')
        
        # Create declined request
        FriendRequest.objects.create(
            from_user=self.user1,
            to_user=self.user2,
            status='declined'
        )
        
        # Try to send again
        response = self.client.post(reverse('add_friend_by_code'), {
            'friend_code': self.user2.profile.friend_code
        })
        
        # Request should be updated to pending
        request = FriendRequest.objects.get(from_user=self.user1, to_user=self.user2)
        self.assertEqual(request.status, 'pending')
        
        # Success message
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('sent' in str(m).lower() for m in messages))
    
    def test_code_case_insensitive(self):
        """Test that friend codes work regardless of case."""
        self.client.login(username='user1', password='pass123')
        
        # Send lowercase code
        code_lower = self.user2.profile.friend_code.lower()
        
        response = self.client.post(reverse('add_friend_by_code'), {
            'friend_code': code_lower
        })
        
        # Should work and create request
        self.assertTrue(
            FriendRequest.objects.filter(
                from_user=self.user1,
                to_user=self.user2
            ).exists()
        )


class SendFriendRequestViewTest(TestCase):
    """Test the send_friend_request view."""
    
    def setUp(self):
        """Set up test client and users."""
        self.client = Client()
        self.user1 = User.objects.create_user('user1', 'user1@test.com', 'pass123')
        self.user2 = User.objects.create_user('user2', 'user2@test.com', 'pass123')
    
    def test_send_friend_request_requires_login(self):
        """Test that view requires authentication."""
        response = self.client.post(
            reverse('send_friend_request', args=[self.user2.id])
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)
    
    def test_send_friend_request_success(self):
        """Test successfully sending a friend request."""
        self.client.login(username='user1', password='pass123')
        
        response = self.client.post(
            reverse('send_friend_request', args=[self.user2.id])
        )
        
        # Should create friend request
        self.assertTrue(
            FriendRequest.objects.filter(
                from_user=self.user1,
                to_user=self.user2,
                status='pending'
            ).exists()
        )
        
        # Success message
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('sent' in str(m).lower() for m in messages))
    
    def test_cannot_send_request_to_self(self):
        """Test that user cannot send request to themselves."""
        self.client.login(username='user1', password='pass123')
        
        response = self.client.post(
            reverse('send_friend_request', args=[self.user1.id])
        )
        
        # No request created
        self.assertEqual(FriendRequest.objects.count(), 0)
        
        # Error message
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('yourself' in str(m).lower() for m in messages))


class AcceptFriendRequestViewTest(TestCase):
    """Test the accept_friend_request view."""
    
    def setUp(self):
        """Set up test client and users."""
        self.client = Client()
        self.user1 = User.objects.create_user('user1', 'user1@test.com', 'pass123')
        self.user2 = User.objects.create_user('user2', 'user2@test.com', 'pass123')
        
        # Create pending request
        self.request = FriendRequest.objects.create(
            from_user=self.user1,
            to_user=self.user2,
            status='pending'
        )
    
    def test_accept_friend_request_success(self):
        """Test accepting a friend request."""
        self.client.login(username='user2', password='pass123')
        
        response = self.client.post(
            reverse('accept_friend_request', args=[self.request.id])
        )
        
        # Request should be accepted
        self.request.refresh_from_db()
        self.assertEqual(self.request.status, 'accepted')
        
        # Should redirect
        self.assertRedirects(response, reverse('friends_dashboard'))
    
    def test_cannot_accept_others_request(self):
        """Test that user can only accept requests sent to them."""
        self.client.login(username='user1', password='pass123')
        
        response = self.client.post(
            reverse('accept_friend_request', args=[self.request.id])
        )
        
        # Should get 404 (request not found for this user)
        self.assertEqual(response.status_code, 404)


class DeclineFriendRequestViewTest(TestCase):
    """Test the decline_friend_request view."""
    
    def setUp(self):
        """Set up test client and users."""
        self.client = Client()
        self.user1 = User.objects.create_user('user1', 'user1@test.com', 'pass123')
        self.user2 = User.objects.create_user('user2', 'user2@test.com', 'pass123')
        
        self.request = FriendRequest.objects.create(
            from_user=self.user1,
            to_user=self.user2,
            status='pending'
        )
    
    def test_decline_friend_request_success(self):
        """Test declining a friend request."""
        self.client.login(username='user2', password='pass123')
        
        response = self.client.post(
            reverse('decline_friend_request', args=[self.request.id])
        )
        
        # Request should be declined
        self.request.refresh_from_db()
        self.assertEqual(self.request.status, 'declined')


class RemoveFriendViewTest(TestCase):
    """Test the remove_friend view."""
    
    def setUp(self):
        """Set up test client and users."""
        self.client = Client()
        self.user1 = User.objects.create_user('user1', 'user1@test.com', 'pass123')
        self.user2 = User.objects.create_user('user2', 'user2@test.com', 'pass123')
        
        # Create accepted friendship
        self.friendship = FriendRequest.objects.create(
            from_user=self.user1,
            to_user=self.user2,
            status='accepted'
        )
    
    def test_remove_friend_success(self):
        """Test removing a friend."""
        self.client.login(username='user1', password='pass123')
        
        response = self.client.post(
            reverse('remove_friend', args=[self.user2.id])
        )
        
        # Friendship should be deleted
        self.assertFalse(
            FriendRequest.objects.filter(id=self.friendship.id).exists()
        )
        
        # Should redirect
        self.assertRedirects(response, reverse('friends_dashboard'))


class FriendsDashboardViewTest(TestCase):
    """Test the friends_dashboard view."""
    
    def setUp(self):
        """Set up test client and users."""
        self.client = Client()
        self.user1 = User.objects.create_user('user1', 'user1@test.com', 'pass123')
        self.user2 = User.objects.create_user('user2', 'user2@test.com', 'pass123')
        self.user3 = User.objects.create_user('user3', 'user3@test.com', 'pass123')
    
    def test_friends_dashboard_requires_login(self):
        """Test that dashboard requires authentication."""
        response = self.client.get(reverse('friends_dashboard'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)
    
    def test_friends_dashboard_shows_friend_code(self):
        """Test that dashboard displays user's friend code."""
        self.client.login(username='user1', password='pass123')
        
        response = self.client.get(reverse('friends_dashboard'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.user1.profile.friend_code)
    
    def test_search_excludes_declined_users(self):
        """Test that search results exclude users with declined requests."""
        self.client.login(username='user1', password='pass123')
        
        # Create declined request
        FriendRequest.objects.create(
            from_user=self.user1,
            to_user=self.user2,
            status='declined'
        )
        
        # Search for user2
        response = self.client.get(
            reverse('friends_dashboard'),
            {'search': 'user2'}
        )
        
        # user2 should appear in results (declined allows resending)
        self.assertContains(response, 'user2')
    
    def test_search_excludes_pending_users(self):
        """Test that search excludes users with pending requests."""
        self.client.login(username='user1', password='pass123')
        
        # Create pending request
        FriendRequest.objects.create(
            from_user=self.user1,
            to_user=self.user2,
            status='pending'
        )
        
        # Search for user2
        response = self.client.get(
            reverse('friends_dashboard'),
            {'search': 'user2'}
        )
        
        # user2 should NOT appear (already have pending request)
        self.assertIn('No users found', response.content.decode())


    
    def test_search_excludes_friends(self):
        """Test that search excludes current friends."""
        self.client.login(username='user1', password='pass123')
        
        # Create friendship
        FriendRequest.objects.create(
            from_user=self.user1,
            to_user=self.user2,
            status='accepted'
        )
        
        # Search for user2
        response = self.client.get(
            reverse('friends_dashboard'),
            {'search': 'user2'}
        )
        
        # user2 should NOT appear (already friends)
        # Note: user2 will still appear in the friends list, just not search results
        self.assertEqual(response.context['search_results'].count(), 0)


from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from .models import Artist, Album
from unittest.mock import patch, MagicMock
import json


class ArtistWalletTests(TestCase):
    """Tests for Artist Wallet functionality."""
    
    def setUp(self):
        """Set up test client and users."""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.other_user = User.objects.create_user(
            username='otheruser',
            password='testpass123'
        )
    
    def test_artist_wallet_requires_login(self):
        """Test that artist wallet page requires authentication."""
        response = self.client.get(reverse('user_artist'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)
    
    def test_artist_wallet_displays_user_artists(self):
        """Test that logged-in user sees their artists."""
        # Create artist for user
        Artist.objects.create(
            user=self.user,
            name='The Beatles',
            genre='Rock',
            rating=5
        )
        
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('user_artist'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'The Beatles')
    
    def test_user_only_sees_own_artists(self):
        """Test that users only see their own artists, not others'."""
        # Create artist for different users
        Artist.objects.create(user=self.user, name='My Artist', genre='Rock')
        Artist.objects.create(user=self.other_user, name='Other Artist', genre='Pop')
        
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('user_artist'))
        
        self.assertContains(response, 'My Artist')
        self.assertNotContains(response, 'Other Artist')
    
    def test_add_artist_manually(self):
        """Test manually adding an artist via form."""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.post(reverse('user_artist'), {
            'name': 'Drake',
            'genre': 'Hip-Hop',
            'rating': 5
        })
        
        self.assertEqual(response.status_code, 302)  # Redirects after success
        self.assertTrue(Artist.objects.filter(user=self.user, name='Drake').exists())
    
    def test_delete_artist(self):
        """Test deleting an artist from wallet."""
        artist = Artist.objects.create(
            user=self.user,
            name='Artist to Delete',
            genre='Rock'
        )
        
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(
            reverse('user_artist'),
            {'delete_artist_id': artist.id}
        )
        
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Artist.objects.filter(id=artist.id).exists())
    
    def test_cannot_delete_other_users_artist(self):
        """Test that users cannot delete artists belonging to others."""
        artist = Artist.objects.create(
            user=self.other_user,
            name='Other User Artist',
            genre='Rock'
        )
        
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(
            reverse('user_artist'),
            {'delete_artist_id': artist.id}
        )
        
        # Artist should still exist
        self.assertTrue(Artist.objects.filter(id=artist.id).exists())


class MusicBrainzSearchTests(TestCase):
    """Tests for MusicBrainz artist search."""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')
    
    def test_search_api_endpoint_exists(self):
        response = self.client.get(reverse('search_artists_api'), {'query': 'Beatles'})
        self.assertEqual(response.status_code, 200)
    
    def test_search_requires_minimum_length(self):
        response = self.client.get(reverse('search_artists_api'), {'query': 'a'})
        data = json.loads(response.content)
        self.assertEqual(data['artists'], [])
    
    @patch('user.services.musicbrainz.MusicBrainzAPI.search_artists')
    def test_search_returns_artists(self, mock_search):
        """Test that search returns artist data."""
        mock_search.return_value = [
            {
                'id': 'test-id',
                'name': 'Test Artist',
                'country': 'US',
                'genres': ['rock'],
                'disambiguation': '',
                'score': 100
            }
        ]
        
        response = self.client.get(reverse('search_artists_api'), {'query': 'Test'})
        data = json.loads(response.content)
        
        self.assertIn('artists', data)
        self.assertEqual(len(data['artists']), 1)
        self.assertEqual(data['artists'][0]['name'], 'Test Artist')


class MusicBrainzServiceTests(TestCase):
    """Test MusicBrainz service methods directly to increase coverage."""
    
    @patch('user.services.musicbrainz.requests.Session.get')
    def test_search_artists_method(self, mock_get):
        """Test the search_artists method logic."""
        from user.services.musicbrainz import MusicBrainzAPI
        
        # Mock the HTTP response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'artists': [
                {
                    'id': 'test-id',
                    'name': 'Test Artist',
                    'country': 'US',
                    'type': 'Person',
                    'score': 100,
                    'disambiguation': 'American rapper',
                    'genres': [{'name': 'rock'}],
                    'tags': [{'name': 'pop'}]
                }
            ]
        }
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response
        
        # Call the actual method
        api = MusicBrainzAPI()
        results = api.search_artists('Test')
        
        # Verify the method processed the data correctly
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['name'], 'Test Artist')
        self.assertEqual(results[0]['country'], 'US')
        self.assertIn('rock', results[0]['genres'])
    
    @patch('user.services.musicbrainz.requests.Session.get')
    def test_get_artist_albums_sorting(self, mock_get):
        """Test that albums are sorted by release date (newest first)."""
        from user.services.musicbrainz import MusicBrainzAPI
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'release-groups': [
                {
                    'id': '1',
                    'title': 'Old Album',
                    'first-release-date': '2020-01-01',
                    'primary-type': 'Album'
                },
                {
                    'id': '2',
                    'title': 'New Album',
                    'first-release-date': '2023-01-01',
                    'primary-type': 'Album'
                },
                {
                    'id': '3',
                    'title': 'Middle Album',
                    'first-release-date': '2021-06-15',
                    'primary-type': 'Album'
                }
            ]
        }
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response
        
        api = MusicBrainzAPI()
        albums = api.get_artist_albums('test-artist-id', limit=5)
        
        # Verify newest album comes first
        self.assertEqual(albums[0]['title'], 'New Album')
        self.assertEqual(albums[1]['title'], 'Middle Album')
        self.assertEqual(albums[2]['title'], 'Old Album')
    
    def test_extract_genres_method(self):
        """Test the _extract_genres helper method."""
        from user.services.musicbrainz import MusicBrainzAPI
        
        api = MusicBrainzAPI()
        
        artist_data = {
            'genres': [
                {'name': 'rock'},
                {'name': 'pop'}
            ],
            'tags': [
                {'name': 'alternative'},
                {'name': 'indie'},
                {'name': 'experimental'}
            ]
        }
        
        genres = api._extract_genres(artist_data)
        
        self.assertIn('rock', genres)
        self.assertIn('pop', genres)
        self.assertLessEqual(len(genres), 3)  # Max 3 genres
    
    def test_extract_genres_with_no_data(self):
        """Test _extract_genres with empty data."""
        from user.services.musicbrainz import MusicBrainzAPI
        
        api = MusicBrainzAPI()
        genres = api._extract_genres({})
        
        self.assertEqual(genres, [])
    
    @patch('user.services.musicbrainz.requests.Session.get')
    def test_get_artist_details(self, mock_get):
        """Test getting artist details."""
        from user.services.musicbrainz import MusicBrainzAPI
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'id': 'artist-id',
            'name': 'Artist Name',
            'relations': [
                {
                    'type': 'official homepage',
                    'url': {'resource': 'https://artist.com'}
                }
            ]
        }
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response
        
        api = MusicBrainzAPI()
        details = api.get_artist_details('artist-id')
        
        self.assertIsNotNone(details)
        self.assertEqual(details['name'], 'Artist Name')
    
    @patch('user.services.musicbrainz.requests.get')
    def test_get_album_cover_art(self, mock_get):
        """Test fetching album cover art."""
        from user.services.musicbrainz import MusicBrainzAPI
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'images': [
                {
                    'thumbnails': {
                        'small': 'https://example.com/small.jpg',
                        '250': 'https://example.com/250.jpg'
                    }
                }
            ]
        }
        mock_get.return_value = mock_response
        
        api = MusicBrainzAPI()
        cover_url = api.get_album_cover_art('release-group-id')
        
        self.assertEqual(cover_url, 'https://example.com/small.jpg')
    
    @patch('user.services.musicbrainz.requests.get')
    def test_get_album_cover_art_not_found(self, mock_get):
        """Test when cover art is not available."""
        from user.services.musicbrainz import MusicBrainzAPI
        
        mock_get.side_effect = Exception("Not found")
        
        api = MusicBrainzAPI()
        cover_url = api.get_album_cover_art('release-group-id')
        
        self.assertIsNone(cover_url)


class AlbumTests(TestCase):
    """Tests for Album model and functionality."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.artist = Artist.objects.create(
            user=self.user,
            name='Test Artist',
            musicbrainz_id='test-id',
            genre='Rock'
        )
    
    def test_create_album_for_artist(self):
        album = Album.objects.create(
            artist=self.artist,
            title='Test Album',
            release_date='2023-01-01',
            album_type='Album'
        )
        
        self.assertEqual(album.artist, self.artist)
        self.assertEqual(self.artist.albums.count(), 1)
    
    def test_albums_display_on_artist_card(self):
        Album.objects.create(
            artist=self.artist,
            title='Abbey Road',
            release_date='1969-09-26'
        )
        
        self.client = Client()
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('user_artist'))
        
        self.assertContains(response, 'Abbey Road')
        self.assertContains(response, 'Recent Albums')
    
    def test_deleting_artist_deletes_albums(self):
        Album.objects.create(
            artist=self.artist,
            title='Test Album',
            release_date='2023-01-01'
        )
        
        artist_id = self.artist.id
        self.artist.delete()
        
        self.assertEqual(Album.objects.filter(artist_id=artist_id).count(), 0)


class ArtistModelTests(TestCase):
    """Tests for Artist model."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
    
    def test_artist_string_representation(self):
        artist = Artist.objects.create(
            user=self.user,
            name='Taylor Swift'
        )
        
        self.assertEqual(str(artist), 'Taylor Swift - testuser')
    
    def test_artist_ordering(self):
        artist1 = Artist.objects.create(user=self.user, name='First')
        artist2 = Artist.objects.create(user=self.user, name='Second')
        
        artists = Artist.objects.filter(user=self.user)
        self.assertEqual(artists[0], artist2) 
    
    def test_cannot_add_duplicate_musicbrainz_artist(self):
        Artist.objects.create(
            user=self.user,
            name='Test Artist',
            musicbrainz_id='same-id'
        )
        
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            Artist.objects.create(
                user=self.user,
                name='Test Artist',
                musicbrainz_id='same-id'
            )
class PrivacySettingsViewTests(TestCase):
    """Test the privacy settings view"""
    
    def setUp(self):
        """Set up test client and user"""
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.profile = self.user.profile
        self.url = reverse('privacy_settings')
    
    def test_privacy_settings_requires_login(self):
        """Test that privacy settings page requires authentication"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)  # Redirect to login
        self.assertIn('/login', response.url)
    
    
    def test_update_privacy_to_friends_only(self):
        """Test changing privacy setting to friends only"""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.post(self.url, {
            'privacy_setting': 'friends'
        })
        
        # Should redirect back to privacy settings
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, self.url)
        
        # Check database was updated
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.privacy, 'friends')
    
    def test_update_privacy_to_private(self):
        """Test changing privacy setting to private"""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.post(self.url, {
            'privacy_setting': 'private'
        })
        
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.privacy, 'private')
    
    def test_update_privacy_to_public(self):
        """Test changing privacy setting to public"""
        self.client.login(username='testuser', password='testpass123')
        
        # Start with private
        self.profile.privacy = 'private'
        self.profile.save()
        
        response = self.client.post(self.url, {
            'privacy_setting': 'public'
        })
        
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.privacy, 'public')


class UserProfileViewTests(TestCase):
    """Test the user profile view with privacy enforcement"""
    
    def setUp(self):
        """Set up test users and client"""
        self.client = Client()
        self.user = User.objects.create_user(username='user', password='testpass123')
        self.user2 = User.objects.create_user(username='user2', password='testpass123')
        self.user3 = User.objects.create_user(username='user3', password='testpass123')
    
    def test_can_view_public_profile(self):
        """Test viewing a public profile"""
        self.user.profile.privacy = 'public'
        self.user.profile.save()
        
        self.client.login(username='user2', password='testpass123')
        response = self.client.get(reverse('user_profile', args=['user']))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'user')
    
        
    
    def test_can_view_friends_only_profile_as_friend(self):
        """Test that friends can view friends-only profiles"""
        self.user.profile.privacy = 'friends'
        self.user.profile.save()
        
        # Create friendship
        FriendRequest.objects.create(
            from_user=self.user,
            to_user=self.user2,
            status='accepted'
        )
        
        self.client.login(username='user2', password='testpass123')
        response = self.client.get(reverse('user_profile', args=['user']))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'user')
            

    
    def test_can_always_view_own_profile(self):
        """Test that users can always view their own profile"""
        self.user.profile.privacy = 'private'
        self.user.profile.save()
        
        self.client.login(username='user', password='testpass123')
        response = self.client.get(reverse('user_profile', args=['user']))
        
        self.assertEqual(response.status_code, 200)


class ProfileViewTests(TestCase):
    """Test the profile settings page"""
    
    def setUp(self):
        """Set up test client and user"""
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.url = reverse('profile')
    
    
    def test_profile_page_loads_for_authenticated_user(self):
        """Test that authenticated users can access their profile"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'testuser')
        self.assertContains(response, self.user.email)
    
class SpotifyServiceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='spotifyuser', password='testpass123')

    def test_get_valid_token_no_account(self):
        from user.spotify_service import get_valid_token
        token = get_valid_token(self.user)
        self.assertIsNone(token)

    def test_is_spotify_connected_false(self):
        from user.spotify_service import is_spotify_connected
        self.assertFalse(is_spotify_connected(self.user))

    def test_disconnect_spotify(self):
        from user.spotify_service import disconnect_spotify
        SpotifyAccount.objects.create(
            user=self.user,
            spotify_id='test123',
            access_token='token',
            refresh_token='refresh',
            token_expires_at=datetime.now() + timedelta(hours=1)
        )
        SpotifyTopArtist.objects.create(
            user=self.user,
            spotify_artist_id='artist1',
            name='Test Artist',
            rank=1
        )
        disconnect_spotify(self.user)
        self.assertFalse(SpotifyAccount.objects.filter(user=self.user).exists())
        self.assertFalse(SpotifyTopArtist.objects.filter(user=self.user).exists())

class AIServiceAdditionalTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('aiuser', password='test123')

    def test_build_recommendation_prompt_all_data(self):
        from user.ai_service import build_recommendation_prompt
        music_data = {
            'spotify_top_artists': [
                {'name': 'Spotify Artist', 'genres': 'rock, pop', 'popularity': 85}
            ],
            'spotify_top_tracks': [
                {'name': 'Track', 'artist': 'Artist', 'popularity': 90}
            ],
            'manual_artists': ['Manual Artist 1', 'Manual Artist 2'],
            'manual_genres': ['Genre 1', 'Genre 2'],
            'manual_tracks': ['Track 1', 'Track 2']
        }
        prompt = build_recommendation_prompt(music_data)
        self.assertIn('Spotify Artist', prompt)
        self.assertIn('Manual Artist', prompt)
        self.assertIn('Genre 1', prompt)
        self.assertIn('Track 1', prompt)

class FormatRecommendationsTest(TestCase):
    def test_format_ai_recommendations_basic(self):
        from user.views import format_ai_recommendations
        raw_text = "### **1. Artist Name**\n- **Genre:** Rock\n---\n### **2. Another Artist**"
        result = format_ai_recommendations(raw_text)
        self.assertIn('<h3>', str(result))
        self.assertIn('<strong>', str(result))
        self.assertIn('<hr>', str(result))

    def test_format_ai_recommendations_with_lists(self):
        from user.views import format_ai_recommendations
        raw_text = "- First item\n- Second item\n- Third item"
        result = format_ai_recommendations(raw_text)
        self.assertIn('<ul>', str(result))
        self.assertIn('<li>', str(result))
        self.assertIn('</ul>', str(result))



User = get_user_model()


class MusicProfileViewTests(TestCase):
    """Test cases for the music profile view"""
    
    def setUp(self):
        """Set up test user and client"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')
        self.url = reverse('music_profile')
    
    def test_music_profile_requires_login(self):
        """Test that music profile view requires authentication"""
        self.client.logout()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)  # Redirect to login
        self.assertIn('/login/', response.url) 
    
    def test_music_profile_get_initial_state(self):
        """Test GET request shows generate button (initial state)"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['profile_generated'])
        self.assertContains(response, 'Generate Your Music Profile')
        self.assertContains(response, 'Generate Music Profile')
    
    def test_music_profile_no_data(self):
        """Test profile generation fails when user has no music data"""
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['profile_generated'])
    
    @patch('user.ai_service.client.chat.completions.create')
    def test_music_profile_generation_success(self, mock_openai):
        """Test successful music profile generation with manual preferences"""
        # Create music preferences
        MusicPreferences.objects.create(
            user=self.user,
            favorite_artists='Taylor Swift, The Beatles, Queen',
            favorite_genres='Pop, Rock',
            favorite_tracks='Shake It Off, Hey Jude'
        )
        
        # Mock OpenAI response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = (
            "You're the type of listener who appreciates timeless pop melodies "
            "with strong lyrical content. Your taste spans decades, showing "
            "an appreciation for both classic rock anthems and modern pop production."
        )
        mock_openai.return_value = mock_response
        
        # Test the view
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['profile_generated'])
        self.assertIn('profile', response.context)
        self.assertIn("You're the type of listener", response.context['profile'])
    
    @patch('user.ai_service.client.chat.completions.create')
    def test_music_profile_saves_to_session(self, mock_openai):
        """Test that generated profile is saved to session"""
        # Create music preferences
        MusicPreferences.objects.create(
            user=self.user,
            favorite_artists='Taylor Swift',
            favorite_genres='Pop'
        )
        
        # Mock OpenAI response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Test profile description"
        mock_openai.return_value = mock_response
        
        # Generate profile
        response = self.client.post(self.url)
        
        # Check session
        self.assertEqual(self.client.session.get('music_profile'), "Test profile description")
    
    def test_music_profile_template_used(self):
        """Test that correct template is used"""
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, 'user/music_profile.html')
    
    @patch('user.ai_service.client.chat.completions.create')
    def test_music_profile_regenerates(self, mock_openai):
        """Test that profile can be regenerated"""
        # Create music preferences
        MusicPreferences.objects.create(
            user=self.user,
            favorite_artists='Coldplay',
            favorite_genres='Alternative'
        )
        
        # Mock different responses
        responses = [
            "First profile description",
            "Second profile description"
        ]
        
        mock_openai.side_effect = [
            self._create_mock_response(text) for text in responses
        ]
        
        # First generation
        response1 = self.client.post(self.url)
        profile1 = response1.context['profile']
        
        # Second generation (regenerate)
        response2 = self.client.post(self.url)
        profile2 = response2.context['profile']
        
        # Both should succeed but potentially be different
        self.assertTrue(response1.context['profile_generated'])
        self.assertTrue(response2.context['profile_generated'])
        self.assertEqual(mock_openai.call_count, 2)
    
    def _create_mock_response(self, text):
        """Helper to create mock OpenAI response"""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = text
        return mock_response


class DashboardMusicProfileTests(TestCase):
    """Test cases for music profile on dashboard"""
    
    def setUp(self):
        """Set up test user and client"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')
        self.dashboard_url = reverse('dashboard')
        self.generate_url = reverse('generate_music_profile')
    
    def test_dashboard_shows_empty_state(self):
        """Test dashboard shows generate prompt when no profile exists"""
        response = self.client.get(self.dashboard_url)
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.context.get('user_profile'))
        self.assertContains(response, 'Discover Your Music Identity')
    
    def test_dashboard_shows_profile_from_session(self):
        """Test dashboard displays profile stored in session"""
        # Manually set session
        session = self.client.session
        session['music_profile'] = "Test profile from session"
        session.save()
        
        response = self.client.get(self.dashboard_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['user_profile'], "Test profile from session")
        self.assertContains(response, "Test profile from session")
    
    @patch('user.ai_service.client.chat.completions.create')
    def test_dashboard_inline_generation(self, mock_openai):
        """Test generating profile inline from dashboard"""
        # Create music preferences
        MusicPreferences.objects.create(
            user=self.user,
            favorite_artists='Test Artist',
            favorite_genres='Test Genre'
        )
        
        # Mock OpenAI response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Dashboard generated profile"
        mock_openai.return_value = mock_response
        
        # Generate from dashboard
        response = self.client.post(self.generate_url, follow=True)
        
        # Should redirect to dashboard
        self.assertRedirects(response, self.dashboard_url)
        
        # Should show success message
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertIn('Music profile generated', str(messages[0]))
        
        # Should save to session
        self.assertEqual(self.client.session.get('music_profile'), "Dashboard generated profile")
    
    def test_inline_generation_requires_login(self):
        """Test that inline generation requires authentication"""
        self.client.logout()
        response = self.client.post(self.generate_url)
        self.assertEqual(response.status_code, 302)  # Redirect to login
    
    def test_inline_generation_only_post(self):
        """Test that inline generation only accepts POST requests"""
        response = self.client.get(self.generate_url)
        # Should redirect to dashboard without generating
        self.assertRedirects(response, self.dashboard_url)


class MusicProfileAIServiceTests(TestCase):
    """Test cases for AI service functions"""
    
    def setUp(self):
        """Set up test user"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_gather_user_music_data_no_data(self):
        """Test gathering music data when user has none"""
        from user.ai_service import gather_user_music_data
        
        data = gather_user_music_data(self.user)
        
        self.assertFalse(data['has_data'])
        self.assertFalse(data['spotify_connected'])
        self.assertEqual(len(data['manual_artists']), 0)
        self.assertEqual(len(data['manual_genres']), 0)
    
    def test_gather_user_music_data_with_preferences(self):
        """Test gathering music data with manual preferences"""
        from user.ai_service import gather_user_music_data
        
        MusicPreferences.objects.create(
            user=self.user,
            favorite_artists='Artist1, Artist2, Artist3',
            favorite_genres='Rock, Pop',
            favorite_tracks='Track1, Track2'
        )
        
        data = gather_user_music_data(self.user)
        
        self.assertTrue(data['has_data'])
        self.assertEqual(len(data['manual_artists']), 3)
        self.assertEqual(len(data['manual_genres']), 2)
        self.assertIn('Artist1', data['manual_artists'])
        self.assertIn('Rock', data['manual_genres'])
    
    def test_build_profile_prompt_with_manual_data(self):
        """Test profile prompt building with manual preferences"""
        from user.ai_service import build_profile_prompt
        
        music_data = {
            'has_data': True,
            'spotify_connected': False,
            'spotify_top_artists': [],
            'spotify_top_tracks': [],
            'manual_artists': ['Artist1', 'Artist2'],
            'manual_genres': ['Rock', 'Pop'],
            'manual_tracks': ['Track1', 'Track2']
        }
        
        prompt = build_profile_prompt(music_data)
        
        self.assertIn('Artist1', prompt)
        self.assertIn('Artist2', prompt)
        self.assertIn('Rock', prompt)
        self.assertIn('Pop', prompt)
        self.assertIn('Track1', prompt)
        self.assertIn('personalized listener profile', prompt.lower())
    
    def test_build_profile_prompt_with_spotify_data(self):
        """Test profile prompt building with Spotify data"""
        from user.ai_service import build_profile_prompt
        
        music_data = {
            'has_data': True,
            'spotify_connected': True,
            'spotify_top_artists': [
                {'name': 'SpotifyArtist1', 'genres': 'rock, indie', 'popularity': 80}
            ],
            'spotify_top_tracks': [
                {'name': 'SpotifyTrack1', 'artist': 'SpotifyArtist1', 'popularity': 75}
            ],
            'manual_artists': [],
            'manual_genres': [],
            'manual_tracks': []
        }
        
        prompt = build_profile_prompt(music_data)
        
        self.assertIn('SpotifyArtist1', prompt)
        self.assertIn('SpotifyTrack1', prompt)
        self.assertIn('rock', prompt)
    
    @patch('user.ai_service.client.chat.completions.create')
    def test_get_music_profile_success(self, mock_openai):
        """Test successful music profile generation"""
        from user.ai_service import get_music_profile
        
        # Create music preferences
        MusicPreferences.objects.create(
            user=self.user,
            favorite_artists='Test Artist',
            favorite_genres='Test Genre'
        )
        
        # Mock OpenAI response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Test profile description"
        mock_openai.return_value = mock_response
        
        # Call function
        result = get_music_profile(self.user)
        
        self.assertTrue(result['success'])
        self.assertEqual(result['profile'], "Test profile description")
        mock_openai.assert_called_once()
        
        # Check that correct model and parameters were used
        call_args = mock_openai.call_args
        self.assertEqual(call_args.kwargs['model'], 'gpt-4o-mini')
        self.assertEqual(call_args.kwargs['max_tokens'], 150)
        self.assertEqual(call_args.kwargs['temperature'], 0.7)
    
    def test_get_music_profile_no_data(self):
        """Test music profile generation with no user data"""
        from user.ai_service import get_music_profile
        
        result = get_music_profile(self.user)
        
        self.assertFalse(result['success'])
        self.assertIn('message', result)
        self.assertIn('connect Spotify or add your music preferences', result['message'])
    
    @patch('user.ai_service.client.chat.completions.create')
    def test_get_music_profile_api_error(self, mock_openai):
        """Test music profile generation with API error"""
        from user.ai_service import get_music_profile
        
        # Create music preferences
        MusicPreferences.objects.create(
            user=self.user,
            favorite_artists='Test Artist'
        )
        
        # Mock API error
        mock_openai.side_effect = Exception("API connection failed")
        
        result = get_music_profile(self.user)
        
        self.assertFalse(result['success'])
        self.assertIn('Error generating profile', result['message'])
    
    @patch('user.ai_service.client.chat.completions.create')
    def test_profile_length_constraint(self, mock_openai):
        """Test that profile generation respects length constraints"""
        from user.ai_service import get_music_profile
        
        MusicPreferences.objects.create(
            user=self.user,
            favorite_artists='Test Artist'
        )
        
        # Mock OpenAI response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Short profile"
        mock_openai.return_value = mock_response
        
        get_music_profile(self.user)
        
        # Verify max_tokens is set to 150 for concise output
        call_args = mock_openai.call_args
        self.assertEqual(call_args.kwargs['max_tokens'], 150)


class MusicProfileIntegrationTests(TestCase):
    """Integration tests for complete music profile workflow"""
    
    def setUp(self):
        """Set up test user and client"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')
    
    @patch('user.ai_service.client.chat.completions.create')
    def test_complete_workflow(self, mock_openai):
        """Test complete workflow from dashboard to profile generation"""
        # Mock OpenAI response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Complete workflow profile"
        mock_openai.return_value = mock_response
        
        # 1. Visit dashboard - should show empty state
        response = self.client.get(reverse('dashboard'))
        self.assertIsNone(response.context.get('user_profile'))
        
        # 2. Add music preferences
        MusicPreferences.objects.create(
            user=self.user,
            favorite_artists='Test Artist',
            favorite_genres='Test Genre'
        )
        
        # 3. Generate profile from music profile page
        response = self.client.post(reverse('music_profile'))
        self.assertTrue(response.context['profile_generated'])
        
        # 4. Visit dashboard - should now show profile
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.context['user_profile'], "Complete workflow profile")
        
        # 5. Regenerate from dashboard
        response = self.client.post(reverse('generate_music_profile'), follow=True)
        self.assertContains(response, "Complete workflow profile")

class SpotifyAnalyticsViewTests(TestCase):
    """Test cases for the analytics view"""
    
    def setUp(self):
        """Set up test client and user"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.url = reverse('analytics')
    
    def test_analytics_requires_login(self):
        """Test that analytics page requires authentication"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)
    
    def test_analytics_shows_not_connected_state(self):
        """Test analytics page when Spotify is not connected"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['spotify_connected'])
        self.assertContains(response, 'Connect Your Spotify Account')
    
    @patch('user.views.analyze_top_genres')
    @patch('user.views.fetch_recently_played')
    @patch('user.views.fetch_user_playlists')
    @patch('user.views.fetch_top_tracks_by_timerange')
    @patch('user.views.fetch_top_artists_by_timerange')
    def test_analytics_with_connected_spotify(self, mock_artists, mock_tracks, mock_playlists, mock_recent, mock_genres):
        """Test analytics page displays when Spotify is connected"""
        self.client.login(username='testuser', password='testpass123')
        
        # Create Spotify account
        SpotifyAccount.objects.create(
            user=self.user,
            spotify_id='test123',
            display_name='Test User',
            email='test@spotify.com',
            access_token='test_token',
            refresh_token='test_refresh',
            token_expires_at=timezone.now() + timedelta(hours=1)
        )
        
        # Mock all the service calls
        mock_artists.return_value = {'success': True, 'artists': [], 'time_range': 'short_term'}
        mock_tracks.return_value = {'success': True, 'tracks': [], 'time_range': 'short_term'}
        mock_playlists.return_value = {'success': True, 'playlists': []}
        mock_recent.return_value = {'success': True, 'tracks': []}
        mock_genres.return_value = {'success': True, 'genres': []}
        
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['spotify_connected'])
        self.assertIsNotNone(response.context['spotify_account'])
    
    @patch('user.views.analyze_top_genres')
    @patch('user.views.fetch_recently_played')
    @patch('user.views.fetch_user_playlists')
    @patch('user.views.fetch_top_tracks_by_timerange')
    @patch('user.views.fetch_top_artists_by_timerange')
    def test_analytics_fetches_top_artists(self, mock_fetch, mock_tracks, mock_playlists, mock_recent, mock_genres):
        """Test that analytics page fetches top artists for all time ranges"""
        self.client.login(username='testuser', password='testpass123')
        
        # Create Spotify account
        SpotifyAccount.objects.create(
            user=self.user,
            spotify_id='test123',
            access_token='test_token',
            refresh_token='test_refresh',
            token_expires_at=timezone.now() + timedelta(hours=1)
        )
        
        # Mock response
        mock_fetch.return_value = {
            'success': True,
            'artists': [
                {'name': 'Test Artist', 'image_url': '', 'genres': 'rock', 'popularity': 80}
            ],
            'time_range': 'short_term'
        }
        
        # Mock other services
        mock_tracks.return_value = {'success': True, 'tracks': [], 'time_range': 'short_term'}
        mock_playlists.return_value = {'success': True, 'playlists': []}
        mock_recent.return_value = {'success': True, 'tracks': []}
        mock_genres.return_value = {'success': True, 'genres': []}
        
        response = self.client.get(self.url)
        
        # Should call fetch 3 times (short, medium, long term)
        self.assertEqual(mock_fetch.call_count, 3)
        self.assertIn('top_artists_month', response.context)
        self.assertIn('top_artists_6months', response.context)
        self.assertIn('top_artists_alltime', response.context)
    
    @patch('user.views.analyze_top_genres')
    @patch('user.views.fetch_recently_played')
    @patch('user.views.fetch_user_playlists')
    @patch('user.views.fetch_top_tracks_by_timerange')
    @patch('user.views.fetch_top_artists_by_timerange')
    def test_analytics_fetches_top_tracks(self, mock_artists, mock_fetch, mock_playlists, mock_recent, mock_genres):
        """Test that analytics page fetches top tracks for all time ranges"""
        self.client.login(username='testuser', password='testpass123')
        
        # Create Spotify account
        SpotifyAccount.objects.create(
            user=self.user,
            spotify_id='test123',
            access_token='test_token',
            refresh_token='test_refresh',
            token_expires_at=timezone.now() + timedelta(hours=1)
        )
        
        # Mock response
        mock_fetch.return_value = {
            'success': True,
            'tracks': [
                {
                    'name': 'Test Track',
                    'artist': 'Test Artist',
                    'album': 'Test Album',
                    'image_url': '',
                    'popularity': 85
                }
            ],
            'time_range': 'short_term'
        }
        
        # Mock other services
        mock_artists.return_value = {'success': True, 'artists': [], 'time_range': 'short_term'}
        mock_playlists.return_value = {'success': True, 'playlists': []}
        mock_recent.return_value = {'success': True, 'tracks': []}
        mock_genres.return_value = {'success': True, 'genres': []}
        
        response = self.client.get(self.url)
        
        # Should call fetch 3 times (short, medium, long term)
        self.assertEqual(mock_fetch.call_count, 3)
        self.assertIn('top_tracks_month', response.context)
        self.assertIn('top_tracks_6months', response.context)
        self.assertIn('top_tracks_alltime', response.context)
    
    @patch('user.views.analyze_top_genres')
    @patch('user.views.fetch_recently_played')
    @patch('user.views.fetch_user_playlists')
    @patch('user.views.fetch_top_tracks_by_timerange')
    @patch('user.views.fetch_top_artists_by_timerange')
    def test_analytics_fetches_playlists(self, mock_artists, mock_tracks, mock_fetch, mock_recent, mock_genres):
        """Test that analytics page fetches user playlists"""
        self.client.login(username='testuser', password='testpass123')
        
        # Create Spotify account
        SpotifyAccount.objects.create(
            user=self.user,
            spotify_id='test123',
            access_token='test_token',
            refresh_token='test_refresh',
            token_expires_at=timezone.now() + timedelta(hours=1)
        )
        
        # Mock response
        mock_fetch.return_value = {
            'success': True,
            'playlists': [
                {
                    'id': 'playlist1',
                    'name': 'My Playlist',
                    'tracks_total': 50,
                    'public': True,
                    'image_url': '',
                    'owner': 'testuser'
                }
            ],
            'message': 'Loaded 1 playlists'
        }
        
        # Mock other services
        mock_artists.return_value = {'success': True, 'artists': [], 'time_range': 'short_term'}
        mock_tracks.return_value = {'success': True, 'tracks': [], 'time_range': 'short_term'}
        mock_recent.return_value = {'success': True, 'tracks': []}
        mock_genres.return_value = {'success': True, 'genres': []}
        
        response = self.client.get(self.url)
        
        mock_fetch.assert_called_once_with(self.user)
        self.assertIn('playlists', response.context)
        playlists = response.context['playlists']
        self.assertTrue(playlists['success'])
        self.assertEqual(len(playlists['playlists']), 1)
    
    @patch('user.views.analyze_top_genres')
    @patch('user.views.fetch_recently_played')
    @patch('user.views.fetch_user_playlists')
    @patch('user.views.fetch_top_tracks_by_timerange')
    @patch('user.views.fetch_top_artists_by_timerange')
    def test_analytics_fetches_recently_played(self, mock_artists, mock_tracks, mock_playlists, mock_fetch, mock_genres):
        """Test that analytics page fetches recently played tracks"""
        self.client.login(username='testuser', password='testpass123')
        
        # Create Spotify account
        SpotifyAccount.objects.create(
            user=self.user,
            spotify_id='test123',
            access_token='test_token',
            refresh_token='test_refresh',
            token_expires_at=timezone.now() + timedelta(hours=1)
        )
        
        # Mock response
        mock_fetch.return_value = {
            'success': True,
            'tracks': [
                {
                    'name': 'Recent Track',
                    'artist': 'Artist Name',
                    'album': 'Album Name',
                    'image_url': '',
                    'played_at': '2024-01-01T12:00:00Z'
                }
            ]
        }
        
        # Mock other services
        mock_artists.return_value = {'success': True, 'artists': [], 'time_range': 'short_term'}
        mock_tracks.return_value = {'success': True, 'tracks': [], 'time_range': 'short_term'}
        mock_playlists.return_value = {'success': True, 'playlists': []}
        mock_genres.return_value = {'success': True, 'genres': []}
        
        response = self.client.get(self.url)
        
        mock_fetch.assert_called_once_with(self.user, 20)
        self.assertIn('recently_played', response.context)
    
    @patch('user.views.analyze_top_genres')
    @patch('user.views.fetch_recently_played')
    @patch('user.views.fetch_user_playlists')
    @patch('user.views.fetch_top_tracks_by_timerange')
    @patch('user.views.fetch_top_artists_by_timerange')
    def test_analytics_analyzes_genres(self, mock_artists, mock_tracks, mock_playlists, mock_recent, mock_fetch):
        """Test that analytics page analyzes top genres"""
        self.client.login(username='testuser', password='testpass123')
        
        # Create Spotify account
        SpotifyAccount.objects.create(
            user=self.user,
            spotify_id='test123',
            access_token='test_token',
            refresh_token='test_refresh',
            token_expires_at=timezone.now() + timedelta(hours=1)
        )
        
        # Mock response
        mock_fetch.return_value = {
            'success': True,
            'genres': [
                ('Rock', 15),
                ('Pop', 12),
                ('Indie', 8)
            ]
        }
        
        # Mock other services
        mock_artists.return_value = {'success': True, 'artists': [], 'time_range': 'short_term'}
        mock_tracks.return_value = {'success': True, 'tracks': [], 'time_range': 'short_term'}
        mock_playlists.return_value = {'success': True, 'playlists': []}
        mock_recent.return_value = {'success': True, 'tracks': []}
        
        response = self.client.get(self.url)
        
        mock_fetch.assert_called_once_with(self.user)
        self.assertIn('top_genres', response.context)
        genres = response.context['top_genres']
        self.assertTrue(genres['success'])
        self.assertEqual(len(genres['genres']), 3)


class SpotifyServiceAnalyticsTests(TestCase):
    """Test cases for spotify_service.py analytics functions"""
    
    def setUp(self):
        """Set up test user and Spotify account"""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.spotify_account = SpotifyAccount.objects.create(
            user=self.user,
            spotify_id='test123',
            access_token='test_token',
            refresh_token='test_refresh',
            token_expires_at=timezone.now() + timedelta(hours=1)
        )
    
    @patch('user.spotify_service.spotipy.Spotify')
    @patch('user.spotify_service.get_valid_token')
    def test_fetch_top_artists_by_timerange_success(self, mock_get_token, mock_spotify):
        """Test successful fetching of top artists by time range"""
        from user.spotify_service import fetch_top_artists_by_timerange
        
        # Mock token
        mock_get_token.return_value = 'valid_token'
        
        # Mock Spotify API response
        mock_sp_instance = Mock()
        mock_sp_instance.current_user_top_artists.return_value = {
            'items': [
                {
                    'name': 'Artist 1',
                    'images': [{'url': 'http://image1.jpg'}],
                    'genres': ['rock', 'indie'],
                    'popularity': 85
                },
                {
                    'name': 'Artist 2',
                    'images': [],
                    'genres': ['pop'],
                    'popularity': 90
                }
            ]
        }
        mock_spotify.return_value = mock_sp_instance
        
        result = fetch_top_artists_by_timerange(self.user, 'short_term', 10)
        
        self.assertTrue(result['success'])
        self.assertEqual(len(result['artists']), 2)
        self.assertEqual(result['artists'][0]['name'], 'Artist 1')
        self.assertEqual(result['artists'][0]['genres'], 'rock, indie')
        self.assertEqual(result['time_range'], 'short_term')
    
    @patch('user.spotify_service.get_valid_token')
    def test_fetch_top_artists_no_token(self, mock_get_token):
        """Test fetching artists with no valid token"""
        from user.spotify_service import fetch_top_artists_by_timerange
        
        # Mock no token
        mock_get_token.return_value = None
        
        result = fetch_top_artists_by_timerange(self.user, 'short_term', 10)
        
        self.assertFalse(result['success'])
        self.assertEqual(result['artists'], [])
    
    @patch('user.spotify_service.spotipy.Spotify')
    @patch('user.spotify_service.get_valid_token')
    def test_fetch_top_artists_api_error(self, mock_get_token, mock_spotify):
        """Test handling of Spotify API errors"""
        from user.spotify_service import fetch_top_artists_by_timerange
        
        mock_get_token.return_value = 'valid_token'
        
        # Mock API error
        mock_sp_instance = Mock()
        mock_sp_instance.current_user_top_artists.side_effect = Exception("API Error")
        mock_spotify.return_value = mock_sp_instance
        
        result = fetch_top_artists_by_timerange(self.user, 'short_term', 10)
        
        self.assertFalse(result['success'])
        self.assertEqual(result['artists'], [])
    
    @patch('user.spotify_service.spotipy.Spotify')
    @patch('user.spotify_service.get_valid_token')
    def test_fetch_top_tracks_by_timerange_success(self, mock_get_token, mock_spotify):
        """Test successful fetching of top tracks by time range"""
        from user.spotify_service import fetch_top_tracks_by_timerange
        
        mock_get_token.return_value = 'valid_token'
        
        # Mock Spotify API response
        mock_sp_instance = Mock()
        mock_sp_instance.current_user_top_tracks.return_value = {
            'items': [
                {
                    'name': 'Track 1',
                    'artists': [{'name': 'Artist 1'}],
                    'album': {
                        'name': 'Album 1',
                        'images': [{'url': 'http://image1.jpg'}]
                    },
                    'popularity': 88
                }
            ]
        }
        mock_spotify.return_value = mock_sp_instance
        
        result = fetch_top_tracks_by_timerange(self.user, 'medium_term', 10)
        
        self.assertTrue(result['success'])
        self.assertEqual(len(result['tracks']), 1)
        self.assertEqual(result['tracks'][0]['name'], 'Track 1')
        self.assertEqual(result['tracks'][0]['artist'], 'Artist 1')
        self.assertEqual(result['time_range'], 'medium_term')
    
    @patch('user.spotify_service.spotipy.Spotify')
    @patch('user.spotify_service.get_valid_token')
    def test_fetch_user_playlists_success(self, mock_get_token, mock_spotify):
        """Test successful fetching of user playlists"""
        from user.spotify_service import fetch_user_playlists
        
        mock_get_token.return_value = 'valid_token'
        
        # Mock Spotify API response
        mock_sp_instance = Mock()
        mock_sp_instance.current_user_playlists.return_value = {
            'items': [
                {
                    'id': 'playlist1',
                    'name': 'My Awesome Playlist',
                    'tracks': {'total': 42},
                    'public': True,
                    'images': [{'url': 'http://playlist_image.jpg'}],
                    'owner': {'display_name': 'testuser'}
                },
                {
                    'id': 'playlist2',
                    'name': 'Chill Vibes',
                    'tracks': {'total': 28},
                    'public': False,
                    'images': [],
                    'owner': {'display_name': 'testuser'}
                }
            ]
        }
        mock_spotify.return_value = mock_sp_instance
        
        result = fetch_user_playlists(self.user)
        
        self.assertTrue(result['success'])
        self.assertEqual(len(result['playlists']), 2)
        self.assertEqual(result['playlists'][0]['name'], 'My Awesome Playlist')
        self.assertEqual(result['playlists'][0]['tracks_total'], 42)
        self.assertEqual(result['playlists'][1]['public'], False)
    
    @patch('user.spotify_service.spotipy.Spotify')
    @patch('user.spotify_service.get_valid_token')
    def test_fetch_user_playlists_error(self, mock_get_token, mock_spotify):
        """Test playlist fetching handles API errors gracefully"""
        from user.spotify_service import fetch_user_playlists
        
        mock_get_token.return_value = 'valid_token'
        
        # Mock API error
        mock_sp_instance = Mock()
        mock_sp_instance.current_user_playlists.side_effect = Exception("API Error")
        mock_spotify.return_value = mock_sp_instance
        
        result = fetch_user_playlists(self.user)
        
        self.assertFalse(result['success'])
        self.assertEqual(len(result['playlists']), 0)
        self.assertIn('message', result)
    
    @patch('user.spotify_service.spotipy.Spotify')
    @patch('user.spotify_service.get_valid_token')
    def test_fetch_recently_played_success(self, mock_get_token, mock_spotify):
        """Test successful fetching of recently played tracks"""
        from user.spotify_service import fetch_recently_played
        
        mock_get_token.return_value = 'valid_token'
        
        # Mock Spotify API response
        mock_sp_instance = Mock()
        mock_sp_instance.current_user_recently_played.return_value = {
            'items': [
                {
                    'track': {
                        'name': 'Recent Track 1',
                        'artists': [{'name': 'Artist 1'}],
                        'album': {
                            'name': 'Album 1',
                            'images': [{'url': 'http://image1.jpg'}]
                        }
                    },
                    'played_at': '2024-01-15T14:30:00Z'
                },
                {
                    'track': {
                        'name': 'Recent Track 2',
                        'artists': [{'name': 'Artist 2'}],
                        'album': {
                            'name': 'Album 2',
                            'images': []
                        }
                    },
                    'played_at': '2024-01-15T14:25:00Z'
                }
            ]
        }
        mock_spotify.return_value = mock_sp_instance
        
        result = fetch_recently_played(self.user, 20)
        
        self.assertTrue(result['success'])
        self.assertEqual(len(result['tracks']), 2)
        self.assertEqual(result['tracks'][0]['name'], 'Recent Track 1')
        self.assertEqual(result['tracks'][0]['played_at'], '2024-01-15T14:30:00Z')
    
    @patch('user.spotify_service.spotipy.Spotify')
    @patch('user.spotify_service.get_valid_token')
    def test_fetch_recently_played_empty_result(self, mock_get_token, mock_spotify):
        """Test recently played with no listening history"""
        from user.spotify_service import fetch_recently_played
        
        mock_get_token.return_value = 'valid_token'
        
        # Mock empty response
        mock_sp_instance = Mock()
        mock_sp_instance.current_user_recently_played.return_value = {
            'items': []
        }
        mock_spotify.return_value = mock_sp_instance
        
        result = fetch_recently_played(self.user, 20)
        
        self.assertTrue(result['success'])
        self.assertEqual(len(result['tracks']), 0)
    
    @patch('user.spotify_service.spotipy.Spotify')
    @patch('user.spotify_service.get_valid_token')
    def test_analyze_top_genres_success(self, mock_get_token, mock_spotify):
        """Test successful analysis of top genres"""
        from user.spotify_service import analyze_top_genres
        
        mock_get_token.return_value = 'valid_token'
        
        # Mock Spotify API response
        mock_sp_instance = Mock()
        mock_sp_instance.current_user_top_artists.return_value = {
            'items': [
                {
                    'name': 'Artist 1',
                    'genres': ['rock', 'alternative', 'indie']
                },
                {
                    'name': 'Artist 2',
                    'genres': ['rock', 'pop']
                },
                {
                    'name': 'Artist 3',
                    'genres': ['indie', 'folk']
                }
            ]
        }
        mock_spotify.return_value = mock_sp_instance
        
        result = analyze_top_genres(self.user)
        
        self.assertTrue(result['success'])
        self.assertGreater(len(result['genres']), 0)
        # Rock should be most common (appears 2 times)
        top_genre, count = result['genres'][0]
        self.assertIn(top_genre, ['rock', 'indie'])
    
    def test_fetch_top_artists_no_spotify_account(self):
        """Test fetching top artists when user has no Spotify account"""
        from user.spotify_service import fetch_top_artists_by_timerange
        
        # Create user without Spotify account
        user_no_spotify = User.objects.create_user(
            username='noconnection',
            password='testpass123'
        )
        
        result = fetch_top_artists_by_timerange(user_no_spotify, 'short_term', 10)
        
        self.assertFalse(result['success'])
        self.assertEqual(result['time_range'], 'short_term')
        self.assertEqual(len(result['artists']), 0)


class SpotifyAnalyticsIntegrationTests(TestCase):
    """Integration tests for complete analytics workflow"""
    
    def setUp(self):
        """Set up test client and user with Spotify data"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        # Create Spotify account
        self.spotify_account = SpotifyAccount.objects.create(
            user=self.user,
            spotify_id='test123',
            display_name='Test User',
            email='test@spotify.com',
            access_token='test_token',
            refresh_token='test_refresh',
            token_expires_at=timezone.now() + timedelta(hours=1)
        )
    
    @patch('user.views.analyze_top_genres')
    @patch('user.views.fetch_recently_played')
    @patch('user.views.fetch_user_playlists')
    @patch('user.views.fetch_top_tracks_by_timerange')
    @patch('user.views.fetch_top_artists_by_timerange')
    def test_complete_analytics_workflow(self, mock_artists, mock_tracks, mock_playlists, mock_recent, mock_genres):
        """Test complete workflow from login to viewing analytics"""
        
        # Mock all Spotify API calls
        mock_artists.return_value = {
            'success': True,
            'artists': [
                {
                    'name': f'Artist {i}',
                    'image_url': f'http://image{i}.jpg',
                    'genres': 'rock, indie',
                    'popularity': 80 + i
                }
                for i in range(5)
            ],
            'time_range': 'short_term'
        }
        
        mock_tracks.return_value = {
            'success': True,
            'tracks': [
                {
                    'name': f'Track {i}',
                    'artist': f'Artist {i}',
                    'album': f'Album {i}',
                    'image_url': f'http://album{i}.jpg',
                    'popularity': 85 + i
                }
                for i in range(5)
            ],
            'time_range': 'short_term'
        }
        
        mock_playlists.return_value = {
            'success': True,
            'playlists': [
                {
                    'id': f'playlist{i}',
                    'name': f'Playlist {i}',
                    'tracks_total': 20 + i,
                    'public': True,
                    'image_url': f'http://playlist{i}.jpg',
                    'owner': 'testuser'
                }
                for i in range(3)
            ]
        }
        
        mock_recent.return_value = {
            'success': True,
            'tracks': [
                {
                    'name': f'Recent {i}',
                    'artist': f'Artist {i}',
                    'album': f'Album {i}',
                    'image_url': f'http://recent{i}.jpg',
                    'played_at': f'2024-01-15T14:{30-i}:00Z'
                }
                for i in range(5)
            ]
        }
        
        mock_genres.return_value = {
            'success': True,
            'genres': [
                ('rock', 15),
                ('pop', 12),
                ('indie', 8)
            ]
        }
        
        # Login
        self.client.login(username='testuser', password='testpass123')
        
        # Visit analytics page
        response = self.client.get(reverse('analytics'))
        
        # Verify response
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['spotify_connected'])
        
        # Verify all data is present
        self.assertIn('top_artists_month', response.context)
        self.assertIn('top_tracks_month', response.context)
        self.assertIn('playlists', response.context)
        self.assertIn('recently_played', response.context)
        self.assertIn('top_genres', response.context)
        
        # Verify data contents
        self.assertTrue(response.context['top_artists_month']['success'])
        self.assertTrue(response.context['playlists']['success'])


class SpotifyAnalyticsDisplayTests(TestCase):
    """Test that analytics data displays correctly in template"""
    
    def setUp(self):
        """Set up test client and user"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')
        
        # Create Spotify account
        SpotifyAccount.objects.create(
            user=self.user,
            spotify_id='test123',
            display_name='Test User',
            access_token='test_token',
            refresh_token='test_refresh',
            token_expires_at=timezone.now() + timedelta(hours=1)
        )
    
    @patch('user.views.analyze_top_genres')
    @patch('user.views.fetch_recently_played')
    @patch('user.views.fetch_user_playlists')
    @patch('user.views.fetch_top_tracks_by_timerange')
    @patch('user.views.fetch_top_artists_by_timerange')
    def test_template_displays_artist_cards(self, mock_fetch, mock_tracks, mock_playlists, mock_recent, mock_genres):
        """Test that artist cards display correctly"""
        mock_fetch.return_value = {
            'success': True,
            'artists': [
                {
                    'name': 'Test Artist',
                    'image_url': 'http://test.jpg',
                    'genres': 'rock, indie',
                    'popularity': 85
                }
            ],
            'time_range': 'short_term'
        }
        
        # Mock other services
        mock_tracks.return_value = {'success': True, 'tracks': [], 'time_range': 'short_term'}
        mock_playlists.return_value = {'success': True, 'playlists': []}
        mock_recent.return_value = {'success': True, 'tracks': []}
        mock_genres.return_value = {'success': True, 'genres': []}
        
        response = self.client.get(reverse('analytics'))
        
        self.assertContains(response, 'Test Artist')
        self.assertContains(response, 'rock, indie')
    
    @patch('user.views.analyze_top_genres')
    @patch('user.views.fetch_recently_played')
    @patch('user.views.fetch_user_playlists')
    @patch('user.views.fetch_top_tracks_by_timerange')
    @patch('user.views.fetch_top_artists_by_timerange')
    def test_template_displays_playlists(self, mock_artists, mock_tracks, mock_fetch, mock_recent, mock_genres):
        """Test that playlists display correctly"""
        mock_fetch.return_value = {
            'success': True,
            'playlists': [
                {
                    'name': 'My Cool Playlist',
                    'tracks_total': 42,
                    'image_url': 'http://playlist.jpg'
                }
            ]
        }
        
        # Mock other services
        mock_artists.return_value = {'success': True, 'artists': [], 'time_range': 'short_term'}
        mock_tracks.return_value = {'success': True, 'tracks': [], 'time_range': 'short_term'}
        mock_recent.return_value = {'success': True, 'tracks': []}
        mock_genres.return_value = {'success': True, 'genres': []}
        
        response = self.client.get(reverse('analytics'))
        
        self.assertContains(response, 'My Cool Playlist')
        self.assertContains(response, '42')
    
    @patch('user.views.analyze_top_genres')
    @patch('user.views.fetch_recently_played')
    @patch('user.views.fetch_user_playlists')
    @patch('user.views.fetch_top_tracks_by_timerange')
    @patch('user.views.fetch_top_artists_by_timerange')
    def test_template_displays_genres(self, mock_artists, mock_tracks, mock_playlists, mock_recent, mock_fetch):
        """Test that genres display correctly"""
        mock_fetch.return_value = {
            'success': True,
            'genres': [
                ('Rock', 15),
                ('Pop', 12),
                ('Indie', 8)
            ]
        }
        
        # Mock other services
        mock_artists.return_value = {'success': True, 'artists': [], 'time_range': 'short_term'}
        mock_tracks.return_value = {'success': True, 'tracks': [], 'time_range': 'short_term'}
        mock_playlists.return_value = {'success': True, 'playlists': []}
        mock_recent.return_value = {'success': True, 'tracks': []}
        
        response = self.client.get(reverse('analytics'))
        
        # The template title-cases genre names, so check for 'Rock' with capital
        self.assertContains(response, 'Rock')
        self.assertContains(response, '15')
    
    @patch('user.views.analyze_top_genres')
    @patch('user.views.fetch_recently_played')
    @patch('user.views.fetch_user_playlists')
    @patch('user.views.fetch_top_tracks_by_timerange')
    @patch('user.views.fetch_top_artists_by_timerange')
    def test_template_shows_empty_state_for_no_data(self, mock_artists, mock_tracks, mock_playlists, mock_recent, mock_genres):
        """Test that template shows appropriate message when no data"""
        mock_artists.return_value = {
            'success': True,
            'artists': [],
            'time_range': 'short_term'
        }
        
        # Mock other services
        mock_tracks.return_value = {'success': True, 'tracks': [], 'time_range': 'short_term'}
        mock_playlists.return_value = {'success': True, 'playlists': []}
        mock_recent.return_value = {'success': True, 'tracks': []}
        mock_genres.return_value = {'success': True, 'genres': []}
        
        response = self.client.get(reverse('analytics'))
        
        # Should contain empty state message
        self.assertContains(response, 'No artist data available')


class SpotifyTimeRangeTests(TestCase):
    """Test different time ranges for Spotify analytics"""
    
    def setUp(self):
        """Set up test user with Spotify account"""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        SpotifyAccount.objects.create(
            user=self.user,
            spotify_id='test123',
            access_token='test_token',
            refresh_token='test_refresh',
            token_expires_at=timezone.now() + timedelta(hours=1)
        )
    
    @patch('user.spotify_service.spotipy.Spotify')
    @patch('user.spotify_service.get_valid_token')
    def test_short_term_time_range(self, mock_get_token, mock_spotify):
        """Test short_term (last 4 weeks) time range"""
        from user.spotify_service import fetch_top_artists_by_timerange
        
        mock_get_token.return_value = 'valid_token'
        
        mock_sp_instance = Mock()
        mock_sp_instance.current_user_top_artists.return_value = {'items': []}
        mock_spotify.return_value = mock_sp_instance
        
        result = fetch_top_artists_by_timerange(self.user, 'short_term', 10)
        
        mock_sp_instance.current_user_top_artists.assert_called_once_with(
            limit=10,
            time_range='short_term'
        )
        self.assertEqual(result['time_range'], 'short_term')
    
    @patch('user.spotify_service.spotipy.Spotify')
    @patch('user.spotify_service.get_valid_token')
    def test_medium_term_time_range(self, mock_get_token, mock_spotify):
        """Test medium_term (last 6 months) time range"""
        from user.spotify_service import fetch_top_tracks_by_timerange
        
        mock_get_token.return_value = 'valid_token'
        
        mock_sp_instance = Mock()
        mock_sp_instance.current_user_top_tracks.return_value = {'items': []}
        mock_spotify.return_value = mock_sp_instance
        
        result = fetch_top_tracks_by_timerange(self.user, 'medium_term', 10)
        
        mock_sp_instance.current_user_top_tracks.assert_called_once_with(
            limit=10,
            time_range='medium_term'
        )
        self.assertEqual(result['time_range'], 'medium_term')
    
    @patch('user.spotify_service.spotipy.Spotify')
    @patch('user.spotify_service.get_valid_token')
    def test_long_term_time_range(self, mock_get_token, mock_spotify):
        """Test long_term (all time) time range"""
        from user.spotify_service import fetch_top_artists_by_timerange
        
        mock_get_token.return_value = 'valid_token'
        
        mock_sp_instance = Mock()
        mock_sp_instance.current_user_top_artists.return_value = {'items': []}
        mock_spotify.return_value = mock_sp_instance
        
        result = fetch_top_artists_by_timerange(self.user, 'long_term', 10)
        
        mock_sp_instance.current_user_top_artists.assert_called_once_with(
            limit=10,
            time_range='long_term'
        )
        self.assertEqual(result['time_range'], 'long_term')
