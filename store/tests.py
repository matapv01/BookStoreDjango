import unittest
import logging
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.admin.sites import AdminSite
from django.contrib.auth import authenticate
from .models import Category, Books, Users
from .admin import CategoryAdmin, BooksAdmin, UsersAdmin
from .forms import UserRegistrationForm, LoginForm

# Set up logging (keep existing logging setup)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Keep existing test classes...

class UserAdminTest(TestCase):
    def setUp(self):
        logger.info("\n=== Setting up user admin tests ===")
        # Create superuser/admin
        self.admin_user = Users.objects.create_superuser(
            email='admin@example.com',
            password='adminpass123',
            name='Admin User'
        )
        # Create test users
        self.test_user = Users.objects.create(
            email='testuser@example.com',
            password='userpass123',
            name='Test User',
            type='user',
            status='active'
        )
        self.staff_user = Users.objects.create(
            email='staff@example.com',
            password='staffpass123',
            name='Staff User',
            type='admin',
            status='active',
            is_staff=True
        )
        
        self.client = Client()
        # Login as admin
        self.client.force_login(self.admin_user)
        logger.info("✓ Test users created and admin logged in")

    def test_user_list_display(self):
        logger.info("\nTesting user list display in admin...")
        response = self.client.get(reverse('admin:store_users_changelist'))
        self.assertEqual(response.status_code, 200)
        logger.info("✓ User list page loads successfully")

    def test_reset_password(self):
        logger.info("\nTesting password reset action...")
        data = {
            'action': 'reset_password',
            '_selected_action': [self.test_user.id],
        }
        response = self.client.post(reverse('admin:store_users_changelist'), data)
        self.assertEqual(response.status_code, 302)  # Redirect after success
        
        # Follow redirect and verify password was reset
        self.test_user.refresh_from_db()
        self.assertTrue(self.test_user.check_password('default123'))
        logger.info("✓ Password reset to default successfully")

    def test_make_inactive(self):
        logger.info("\nTesting make user inactive action...")
        data = {
            'action': 'make_inactive',
            '_selected_action': [self.test_user.id],
        }
        response = self.client.post(reverse('admin:store_users_changelist'), data)
        self.assertEqual(response.status_code, 302)  # Redirect after success
        
        # Follow redirect and verify user is inactive
        self.test_user.refresh_from_db()
        self.assertEqual(self.test_user.status, 'inactive')
        logger.info("✓ User status changed to inactive")

    def test_make_staff(self):
        logger.info("\nTesting grant staff status action...")
        data = {
            'action': 'make_staff',
            '_selected_action': [self.test_user.id],
        }
        response = self.client.post(reverse('admin:store_users_changelist'), data)
        self.assertEqual(response.status_code, 302)  # Redirect after success
        
        # Follow redirect and verify user is now staff
        self.test_user.refresh_from_db()
        self.assertTrue(self.test_user.is_staff)
        self.assertEqual(self.test_user.type, 'admin')
        logger.info("✓ User granted staff status and admin role")

    def test_remove_staff(self):
        logger.info("\nTesting remove staff status action...")
        data = {
            'action': 'remove_staff',
            '_selected_action': [self.staff_user.id],
        }
        response = self.client.post(reverse('admin:store_users_changelist'), data)
        self.assertEqual(response.status_code, 302)  # Redirect after success
        
        # Follow redirect and verify staff status removed
        self.staff_user.refresh_from_db()
        self.assertFalse(self.staff_user.is_staff)
        self.assertEqual(self.staff_user.type, 'user')
        logger.info("✓ Staff status removed and role changed to user")

    def test_user_change_form(self):
        logger.info("\nTesting user edit form...")
        response = self.client.get(
            reverse('admin:store_users_change', args=[self.test_user.id])
        )
        self.assertEqual(response.status_code, 200)  # GET form should be 200
        logger.info("✓ User edit form loads successfully")
        
        # Test updating user
        # Test updating user
        data = {
            'email': self.test_user.email,
            'name': 'Updated Name',
            'password': self.test_user.password,  # Keep existing password hash
            'type': 'user',
            'status': 'active',
            'is_staff': False,
            'is_superuser': False,
        }
        response = self.client.post(
            reverse('admin:store_users_change', args=[self.test_user.id]),
            data
        )
        self.assertEqual(response.status_code, 302)  # Redirect on successful save
        
        self.test_user.refresh_from_db()
        self.assertEqual(self.test_user.name, 'Updated Name')
        logger.info("✓ User details updated successfully")

    def tearDown(self):
        logger.info("\n=== Cleaning up user admin tests ===")
        Users.objects.all().delete()

    def test_admin_reset_password(self):
        logger.info("\nTesting admin password reset...")
        # Logout first to test without staff permissions
        self.client.logout()
        response = self.client.get(
            reverse('store:admin_reset_user_password'),
            {'user_id': self.test_user.id}
        )
        self.assertEqual(response.status_code, 302)  # Redirect to login
        logger.info("✓ Non-staff user redirected to login")

        # Login as admin and retry
        self.client.force_login(self.admin_user)
        response = self.client.get(
            reverse('store:admin_reset_user_password'),
            {'user_id': self.test_user.id}
        )
        self.assertEqual(response.status_code, 302)  # Redirect after success
        
        # Follow redirect and verify password was reset
        self.test_user.refresh_from_db()
        self.assertTrue(self.test_user.check_password('default123'))
        logger.info("✓ Admin successfully reset user password")

    def test_admin_change_role(self):
        logger.info("\nTesting admin role change...")
        # Login as admin
        self.client.force_login(self.admin_user)
        
        # Make test user a staff member
        response = self.client.post(
            reverse('store:admin_change_user_role') + f'?user_id={self.test_user.id}',
            {'role': 'admin'}
        )
        self.assertEqual(response.status_code, 302)  # Redirects on success
        
        # Verify role change
        self.test_user.refresh_from_db()
        self.assertTrue(self.test_user.is_staff)
        self.assertEqual(self.test_user.type, 'admin')
        logger.info("✓ User role changed to admin")

        # Change back to regular user
        response = self.client.post(
            reverse('store:admin_change_user_role') + f'?user_id={self.test_user.id}',
            {'role': 'user'}
        )
        self.assertEqual(response.status_code, 302)  # Redirects on success
        
        # Verify role change
        self.test_user.refresh_from_db()
        self.assertFalse(self.test_user.is_staff)
        self.assertEqual(self.test_user.type, 'user')
        logger.info("✓ User role changed back to user")

    def test_admin_role_permissions(self):
        logger.info("\nTesting admin role permissions...")
        # Create staff user (not superuser)
        staff_test_user = Users.objects.create(
            email='stafftest@example.com',  # Different email to avoid conflict
            name='Staff Test User',
            type='admin',
            is_staff=True,
            is_superuser=False
        )
        self.client.force_login(staff_test_user)
        
        # Staff cannot modify other staff users
        response = self.client.post(
            reverse('store:admin_change_user_role') + f'?user_id={staff_test_user.id}',
            {'role': 'user'}
        )
        self.assertEqual(response.status_code, 403)
        logger.info("✓ Staff user cannot modify other staff users")
        
        # Staff cannot reset staff passwords
        response = self.client.get(
            reverse('store:admin_reset_user_password'),
            {'user_id': staff_test_user.id}
        )
        self.assertEqual(response.status_code, 403)
        logger.info("✓ Staff user cannot reset staff passwords")
        
        # But can modify regular users
        response = self.client.post(
            reverse('store:admin_change_user_role') + f'?user_id={self.test_user.id}',
            {'role': 'user'}
        )
        self.assertEqual(response.status_code, 302)  # Redirects on success
        logger.info("✓ Staff user can modify regular users")
