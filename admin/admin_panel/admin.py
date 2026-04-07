from django.contrib import admin
from .models import User, Pellet, Tag, Material, Job, Task

# Register your models here.
@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'phone_number', 'exp_level', 'created_at')
    list_filter = ('exp_level', 'phone_verified', 'created_at')
    search_fields = ('username', 'email', 'phone_number', 'wechat_nickname')
    readonly_fields = ('created_at', 'updated_at')

@admin.register(Pellet)
class PelletAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'status', 'ai_score', 'visibility', 'created_at')
    list_filter = ('status', 'visibility', 'pellet_type', 'created_at')
    search_fields = ('title', 'content')
    readonly_fields = ('created_at', 'updated_at')

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'color', 'created_at')
    search_fields = ('name', 'description')
    readonly_fields = ('created_at', 'updated_at')

@admin.register(Material)
class MaterialAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'content_type', 'file_size', 'created_at')
    list_filter = ('content_type', 'created_at')
    search_fields = ('title', 'file_path')
    readonly_fields = ('created_at', 'updated_at')

@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ('job_id', 'job_type', 'status', 'user', 'priority', 'created_at')
    list_filter = ('job_type', 'status', 'priority', 'created_at')
    search_fields = ('job_id',)
    readonly_fields = ('created_at', 'updated_at')

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('task_id', 'job', 'task_type', 'status', 'material_id', 'created_at')
    list_filter = ('task_type', 'status', 'created_at')
    search_fields = ('task_id', 'material_id', 'object_id')
    readonly_fields = ('created_at', 'updated_at')
