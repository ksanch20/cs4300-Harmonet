from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from user.models import MusicPreferences
from .models import FriendRequest, FriendRequestManager

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
    
