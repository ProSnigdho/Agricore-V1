"""
Automated tests for the AgriCore authentication system.
Tests cover: registration, login, JWT validation, role-based access, Google login, and logout.
"""

from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from unittest.mock import patch, MagicMock

from users.models import User


class UserModelTests(TestCase):
    """Tests for the custom User model."""

    def test_create_customer_user(self):
        """Test creating a customer user."""
        user = User.objects.create_user(
            email='customer@test.com',
            password='TestPass123!',
            first_name='John',
            last_name='Doe',
            role=User.Role.CUSTOMER,
        )
        self.assertEqual(user.email, 'customer@test.com')
        self.assertEqual(user.role, 'customer')
        self.assertTrue(user.is_customer)
        self.assertFalse(user.is_admin)
        self.assertTrue(user.check_password('TestPass123!'))

    def test_create_admin_user(self):
        """Test creating an admin user."""
        user = User.objects.create_user(
            email='admin@test.com',
            password='AdminPass123!',
            first_name='Admin',
            last_name='User',
            role=User.Role.ADMIN,
        )
        self.assertEqual(user.role, 'admin')
        self.assertTrue(user.is_admin)
        self.assertFalse(user.is_customer)

    def test_create_superuser(self):
        """Test creating a superuser."""
        user = User.objects.create_superuser(
            email='super@test.com',
            password='SuperPass123!',
            first_name='Super',
            last_name='Admin',
        )
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)
        self.assertEqual(user.role, 'admin')

    def test_user_without_email_raises(self):
        """Test that creating a user without email raises ValueError."""
        with self.assertRaises(ValueError):
            User.objects.create_user(email='', password='test')

    def test_full_name_property(self):
        """Test the full_name computed property."""
        user = User(first_name='John', last_name='Doe')
        self.assertEqual(user.full_name, 'John Doe')


class RegistrationTests(TestCase):
    """Tests for customer registration endpoint."""

    def setUp(self):
        self.client = APIClient()
        self.register_url = reverse('auth-register')

    def test_successful_registration(self):
        """Test successful customer registration."""
        data = {
            'email': 'newuser@test.com',
            'first_name': 'New',
            'last_name': 'User',
            'password': 'SecurePass123!',
            'password_confirm': 'SecurePass123!',
        }
        response = self.client.post(self.register_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertEqual(response.data['user']['role'], 'customer')

    def test_registration_password_mismatch(self):
        """Test registration with mismatched passwords."""
        data = {
            'email': 'mismatch@test.com',
            'first_name': 'Test',
            'last_name': 'User',
            'password': 'SecurePass123!',
            'password_confirm': 'DifferentPass!',
        }
        response = self.client.post(self.register_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_registration_duplicate_email(self):
        """Test registration with an existing email."""
        User.objects.create_user(email='existing@test.com', password='test123!')
        data = {
            'email': 'existing@test.com',
            'first_name': 'Dup',
            'last_name': 'User',
            'password': 'SecurePass123!',
            'password_confirm': 'SecurePass123!',
        }
        response = self.client.post(self.register_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_registration_short_password(self):
        """Test registration with a password shorter than 8 characters."""
        data = {
            'email': 'short@test.com',
            'first_name': 'Short',
            'last_name': 'Pass',
            'password': 'abc',
            'password_confirm': 'abc',
        }
        response = self.client.post(self.register_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class LoginTests(TestCase):
    """Tests for JWT login endpoint."""

    def setUp(self):
        self.client = APIClient()
        self.login_url = reverse('auth-login')
        self.user = User.objects.create_user(
            email='login@test.com',
            password='TestPassword123!',
            first_name='Login',
            last_name='Test',
            role=User.Role.CUSTOMER,
        )

    def test_successful_login(self):
        """Test successful JWT login."""
        data = {'email': 'login@test.com', 'password': 'TestPassword123!'}
        response = self.client.post(self.login_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertEqual(response.data['user']['role'], 'customer')

    def test_login_wrong_password(self):
        """Test login with incorrect password."""
        data = {'email': 'login@test.com', 'password': 'WrongPassword!'}
        response = self.client.post(self.login_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_nonexistent_user(self):
        """Test login with non-existent email."""
        data = {'email': 'nobody@test.com', 'password': 'Test123!'}
        response = self.client.post(self.login_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class JWTValidationTests(TestCase):
    """Tests for JWT token validation and refresh."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='jwt@test.com',
            password='TestPassword123!',
            first_name='JWT',
            last_name='Test',
        )
        # Get tokens
        response = self.client.post(
            reverse('auth-login'),
            {'email': 'jwt@test.com', 'password': 'TestPassword123!'},
            format='json',
        )
        self.access_token = response.data['access']
        self.refresh_token = response.data['refresh']

    def test_verify_valid_token(self):
        """Test verifying a valid access token."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        response = self.client.get(reverse('auth-verify'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['valid'])

    def test_verify_invalid_token(self):
        """Test verifying an invalid access token."""
        self.client.credentials(HTTP_AUTHORIZATION='Bearer invalid-token-here')
        response = self.client.get(reverse('auth-verify'))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_access_without_token(self):
        """Test accessing a protected endpoint without a token."""
        response = self.client.get(reverse('auth-verify'))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_token_refresh(self):
        """Test refreshing an access token."""
        response = self.client.post(
            reverse('token-refresh'),
            {'refresh': self.refresh_token},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)


class RoleBasedAccessTests(TestCase):
    """Tests for role-based access control (RBAC)."""

    def setUp(self):
        self.client = APIClient()

        # Create admin user
        self.admin = User.objects.create_user(
            email='admin@test.com',
            password='AdminPass123!',
            first_name='Admin',
            last_name='User',
            role=User.Role.ADMIN,
            is_staff=True,
        )
        admin_response = self.client.post(
            reverse('auth-login'),
            {'email': 'admin@test.com', 'password': 'AdminPass123!'},
            format='json',
        )
        self.admin_token = admin_response.data['access']

        # Create customer user
        self.customer = User.objects.create_user(
            email='customer@test.com',
            password='CustomerPass123!',
            first_name='Customer',
            last_name='User',
            role=User.Role.CUSTOMER,
        )
        cust_response = self.client.post(
            reverse('auth-login'),
            {'email': 'customer@test.com', 'password': 'CustomerPass123!'},
            format='json',
        )
        self.customer_token = cust_response.data['access']

    def test_admin_can_access_admin_dashboard(self):
        """Test that admin can access admin dashboard."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.admin_token}')
        response = self.client.get(reverse('admin-dashboard'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('stats', response.data)

    def test_customer_cannot_access_admin_dashboard(self):
        """Test that customer CANNOT access admin dashboard (403 Forbidden)."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.customer_token}')
        response = self.client.get(reverse('admin-dashboard'))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_customer_can_access_customer_dashboard(self):
        """Test that customer can access customer dashboard."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.customer_token}')
        response = self.client.get(reverse('customer-dashboard'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_admin_cannot_access_customer_dashboard(self):
        """Test that admin CANNOT access customer dashboard (403 Forbidden)."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.admin_token}')
        response = self.client.get(reverse('customer-dashboard'))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_list_users(self):
        """Test that admin can list all users."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.admin_token}')
        response = self.client.get(reverse('admin-user-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_customer_cannot_list_users(self):
        """Test that customer CANNOT list all users (403 Forbidden)."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.customer_token}')
        response = self.client.get(reverse('admin-user-list'))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class ProfileTests(TestCase):
    """Tests for user profile endpoint."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='profile@test.com',
            password='TestPass123!',
            first_name='Profile',
            last_name='Test',
        )
        response = self.client.post(
            reverse('auth-login'),
            {'email': 'profile@test.com', 'password': 'TestPass123!'},
            format='json',
        )
        self.token = response.data['access']

    def test_get_profile(self):
        """Test fetching user profile."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        response = self.client.get(reverse('user-profile'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], 'profile@test.com')

    def test_update_profile(self):
        """Test updating user profile."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        response = self.client.put(
            reverse('user-profile'),
            {'first_name': 'Updated', 'last_name': 'Name'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['first_name'], 'Updated')

    def test_unauthenticated_profile_access(self):
        """Test accessing profile without authentication."""
        response = self.client.get(reverse('user-profile'))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class GoogleLoginTests(TestCase):
    """Tests for Google OAuth login endpoint."""

    def setUp(self):
        self.client = APIClient()
        self.google_url = reverse('auth-google')

    def test_google_login_missing_token(self):
        """Test Google login without providing a token."""
        response = self.client.post(self.google_url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch('authentication.views.id_token.verify_oauth2_token')
    def test_google_login_new_user(self, mock_verify):
        """Test Google login creating a new user."""
        mock_verify.return_value = {
            'sub': '123456789',
            'email': 'google@test.com',
            'given_name': 'Google',
            'family_name': 'User',
            'picture': 'https://lh3.googleusercontent.com/a/photo.jpg',
        }
        response = self.client.post(
            self.google_url,
            {'token': 'mock-google-token'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertTrue(response.data['is_new_user'])
        self.assertEqual(response.data['user']['role'], 'customer')

        # Verify user was created in the database
        user = User.objects.get(email='google@test.com')
        self.assertEqual(user.google_id, '123456789')
        self.assertEqual(user.auth_provider, 'google')

    @patch('authentication.views.id_token.verify_oauth2_token')
    def test_google_login_existing_user(self, mock_verify):
        """Test Google login with an existing user."""
        User.objects.create_user(
            email='existing@test.com',
            password='test',
            first_name='Existing',
            last_name='User',
        )
        mock_verify.return_value = {
            'sub': '987654321',
            'email': 'existing@test.com',
            'given_name': 'Existing',
            'family_name': 'User',
            'picture': 'https://lh3.googleusercontent.com/a/photo.jpg',
        }
        response = self.client.post(
            self.google_url,
            {'token': 'mock-google-token'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['is_new_user'])

    @patch('authentication.views.id_token.verify_oauth2_token')
    def test_google_login_invalid_token(self, mock_verify):
        """Test Google login with an invalid token."""
        mock_verify.side_effect = ValueError('Invalid token')
        response = self.client.post(
            self.google_url,
            {'token': 'invalid-token'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class LogoutTests(TestCase):
    """Tests for logout endpoint."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='logout@test.com',
            password='TestPass123!',
        )
        response = self.client.post(
            reverse('auth-login'),
            {'email': 'logout@test.com', 'password': 'TestPass123!'},
            format='json',
        )
        self.access_token = response.data['access']
        self.refresh_token = response.data['refresh']

    def test_successful_logout(self):
        """Test successful logout with refresh token blacklisting."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        response = self.client.post(
            reverse('auth-logout'),
            {'refresh': self.refresh_token},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_logout_unauthenticated(self):
        """Test logout without authentication."""
        response = self.client.post(reverse('auth-logout'))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
