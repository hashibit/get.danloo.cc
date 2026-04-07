from django.db import models
import uuid
from datetime import datetime

# User model based on UserDB
class User(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(max_length=255, unique=True, null=True, blank=True)
    username = models.CharField(max_length=255, unique=True)
    password_hash = models.TextField(null=True, blank=True)
    phone_number = models.CharField(max_length=20, unique=True, null=True, blank=True)
    phone_verified = models.BooleanField(default=False)
    wechat_openid = models.CharField(max_length=255, unique=True, null=True, blank=True)
    wechat_unionid = models.CharField(max_length=255, unique=True, null=True, blank=True)
    wechat_nickname = models.CharField(max_length=255, null=True, blank=True)
    wechat_avatar = models.TextField(null=True, blank=True)
    exp_level = models.CharField(max_length=10, default="1")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.username

    class Meta:
        db_table = "users"

# Pellet model based on PelletDB
class Pellet(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    material_ids = models.TextField(null=True, blank=True)
    title = models.CharField(max_length=255, null=True, blank=True)
    content = models.TextField()
    status = models.CharField(max_length=50, default="in-queue")
    ai_score = models.FloatField(null=True, blank=True)
    pellet_type = models.CharField(max_length=50, null=True, blank=True)
    generation_metadata = models.TextField(null=True, blank=True)
    visibility = models.CharField(max_length=10, default="private")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title if self.title else f"Pellet {self.id}"

    class Meta:
        db_table = "pellets"

# Tag model based on TagDB
class Tag(models.Model):
    id = models.CharField(max_length=255, primary_key=True)
    name = models.CharField(max_length=255, unique=True)
    color = models.CharField(max_length=50)
    description = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    pellets = models.ManyToManyField(Pellet, related_name='tags', blank=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = "tags"

# Material model based on MaterialDB
class Material(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    content_type = models.CharField(max_length=100)
    file_path = models.TextField()
    file_size = models.BigIntegerField(null=True, blank=True)
    object_id = models.CharField(max_length=36, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    class Meta:
        db_table = "materials"

# Job model based on JobDB
class Job(models.Model):
    JOB_TYPES = [
        ('material_processing', 'Material Processing'),
        ('pellet_generation', 'Pellet Generation'),
        ('batch_analysis', 'Batch Analysis'),
    ]

    JOB_STATUS = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]

    job_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    job_type = models.CharField(max_length=50, choices=JOB_TYPES, default='material_processing')
    status = models.CharField(max_length=50, choices=JOB_STATUS, default='pending')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    priority = models.IntegerField(default=0)
    job_metadata = models.JSONField(null=True, blank=True)
    error_message = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Job {self.job_id} - {self.job_type}"

    class Meta:
        db_table = "jobs"

# Task model based on TaskDB
class Task(models.Model):
    TASK_STATUS = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('skipped', 'Skipped'),
    ]

    TASK_TYPES = [
        ('PROCESS_MATERIAL', 'Process Material'),
    ]

    task_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='tasks')
    material_id = models.CharField(max_length=36)
    object_id = models.CharField(max_length=36, null=True, blank=True)
    content_type = models.CharField(max_length=50, null=True, blank=True)
    task_type = models.CharField(max_length=50, choices=TASK_TYPES, default='PROCESS_MATERIAL')
    status = models.CharField(max_length=50, choices=TASK_STATUS, default='pending')
    result = models.TextField(null=True, blank=True)
    error_message = models.TextField(null=True, blank=True)
    retry_count = models.CharField(max_length=10, default="0")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Task {self.task_id} - {self.task_type}"

    class Meta:
        db_table = "tasks"
