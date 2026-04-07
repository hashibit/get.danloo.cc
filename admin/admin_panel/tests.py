from django.test import TestCase
from django.contrib.auth.models import User as DjangoUser
from django.urls import reverse
from .models import User, Pellet, Tag, Material, Job, Task

class AdminPanelTestCase(TestCase):
    def setUp(self):
        # Create a test user
        self.user = DjangoUser.objects.create_superuser(
            username='admin',
            email='admin@test.com',
            password='adminpassword'
        )

        # Create test data
        self.danloo_user = User.objects.create(
            username='testuser',
            email='test@example.com',
            exp_level='1'
        )

        self.tag = Tag.objects.create(
            id='test-tag',
            name='Test Tag',
            color='#FF0000',
            description='A test tag'
        )

        self.material = Material.objects.create(
            user=self.danloo_user,
            title='Test Material',
            content_type='text/plain',
            file_path='/path/to/test/file.txt',
            file_size=1024
        )

        self.pellet = Pellet.objects.create(
            user=self.danloo_user,
            title='Test Pellet',
            content='This is a test pellet content',
            status='completed',
            ai_score=0.85,
            pellet_type='test',
            visibility='public'
        )

        self.job = Job.objects.create(
            job_type='material_processing',
            status='completed',
            user=self.danloo_user,
            priority=1
        )

        self.task = Task.objects.create(
            job=self.job,
            material_id=str(self.material.id),
            task_type='PROCESS_MATERIAL',
            status='completed'
        )

    def test_dashboard_view(self):
        """Test that the dashboard view loads correctly"""
        self.client.login(username='admin', password='adminpassword')
        response = self.client.get(reverse('admin_panel:dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Admin Dashboard')

    def test_user_management_view(self):
        """Test that the user management view loads correctly"""
        self.client.login(username='admin', password='adminpassword')
        response = self.client.get(reverse('admin_panel:user_management'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'User Management')

    def test_pellet_management_view(self):
        """Test that the pellet management view loads correctly"""
        self.client.login(username='admin', password='adminpassword')
        response = self.client.get(reverse('admin_panel:pellet_management'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Pellet Management')

    def test_task_management_view(self):
        """Test that the task management view loads correctly"""
        self.client.login(username='admin', password='adminpassword')
        response = self.client.get(reverse('admin_panel:task_management'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Task & Job Management')

    def test_tag_management_view(self):
        """Test that the tag management view loads correctly"""
        self.client.login(username='admin', password='adminpassword')
        response = self.client.get(reverse('admin_panel:tag_management'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Tag Management')

    def test_material_management_view(self):
        """Test that the material management view loads correctly"""
        self.client.login(username='admin', password='adminpassword')
        response = self.client.get(reverse('admin_panel:material_management'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Material Management')
