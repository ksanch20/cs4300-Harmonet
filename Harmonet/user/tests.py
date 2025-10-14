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

