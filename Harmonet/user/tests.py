from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse

#Used ChatGPT to help write tests

class UserAuthTests(TestCase):
    def setUp(self):
        # Create a user to test login
        self.user = User.objects.create_user(username='testuser', email='test@example.com', password='TestPass123')

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