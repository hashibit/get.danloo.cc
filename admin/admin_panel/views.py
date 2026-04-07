from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, JsonResponse
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
import json
from .models import User, Pellet, Tag, Material, Job, Task

@staff_member_required
def dashboard(request):
    """Admin dashboard view showing overview statistics"""
    # Get counts for each model
    user_count = User.objects.count()
    pellet_count = Pellet.objects.count()
    tag_count = Tag.objects.count()
    material_count = Material.objects.count()
    job_count = Job.objects.count()
    task_count = Task.objects.count()

    # Get recent items
    recent_users = User.objects.order_by('-created_at')[:5]
    recent_pellets = Pellet.objects.order_by('-created_at')[:5]
    recent_materials = Material.objects.order_by('-created_at')[:5]

    context = {
        'user_count': user_count,
        'pellet_count': pellet_count,
        'tag_count': tag_count,
        'material_count': material_count,
        'job_count': job_count,
        'task_count': task_count,
        'recent_users': recent_users,
        'recent_pellets': recent_pellets,
        'recent_materials': recent_materials,
    }

    return render(request, 'admin_panel/dashboard.html', context)

@staff_member_required
def user_management(request):
    """View for user management"""
    users = User.objects.all().order_by('-created_at')
    return render(request, 'admin_panel/user_management.html', {'users': users})

@staff_member_required
def pellet_management(request):
    """View for pellet management"""
    pellets = Pellet.objects.all().order_by('-created_at')
    return render(request, 'admin_panel/pellet_management.html', {'pellets': pellets})

@staff_member_required
def task_management(request):
    """View for task and job management"""
    jobs = Job.objects.all().order_by('-created_at')
    tasks = Task.objects.all().order_by('-created_at')
    return render(request, 'admin_panel/task_management.html', {'jobs': jobs, 'tasks': tasks})

@staff_member_required
def tag_management(request):
    """View for tag management"""
    tags = Tag.objects.all().order_by('-created_at')
    return render(request, 'admin_panel/tag_management.html', {'tags': tags})

@staff_member_required
def material_management(request):
    """View for material management"""
    materials = Material.objects.all().order_by('-created_at')
    return render(request, 'admin_panel/material_management.html', {'materials': materials})

@staff_member_required
def tag_edit(request, tag_id):
    """Edit a tag"""
    tag = get_object_or_404(Tag, id=tag_id)

    if request.method == 'POST':
        # Get the data from the request
        name = request.POST.get('name')
        color = request.POST.get('color')
        description = request.POST.get('description')

        # Update the tag
        tag.name = name
        tag.color = color
        tag.description = description
        tag.save()

        messages.success(request, f'Tag "{tag.name}" has been updated successfully.')
        return redirect('admin_panel:tag_management')

    return render(request, 'admin_panel/tag_management.html', {'tags': Tag.objects.all().order_by('-created_at')})

@staff_member_required
def tag_delete(request, tag_id):
    """Delete a tag"""
    tag = get_object_or_404(Tag, id=tag_id)

    if request.method == 'POST':
        tag_name = tag.name
        tag.delete()
        messages.success(request, f'Tag "{tag_name}" has been deleted successfully.')
        return redirect('admin_panel:tag_management')

    return render(request, 'admin_panel/tag_management.html', {'tags': Tag.objects.all().order_by('-created_at')})

@staff_member_required
def pellet_edit(request, pellet_id):
    """Edit a pellet"""
    pellet = get_object_or_404(Pellet, id=pellet_id)

    if request.method == 'POST':
        # Get the data from the request
        title = request.POST.get('title')
        content = request.POST.get('content')
        status = request.POST.get('status')
        ai_score = request.POST.get('ai_score')
        pellet_type = request.POST.get('pellet_type')
        visibility = request.POST.get('visibility')

        # Update the pellet
        pellet.title = title
        pellet.content = content
        pellet.status = status
        pellet.ai_score = ai_score
        pellet.pellet_type = pellet_type
        pellet.visibility = visibility
        pellet.save()

        messages.success(request, f'Pellet "{pellet.title}" has been updated successfully.')
        return redirect('admin_panel:pellet_management')

    return render(request, 'admin_panel/pellet_management.html', {'pellets': Pellet.objects.all().order_by('-created_at')})

@staff_member_required
def pellet_delete(request, pellet_id):
    """Delete a pellet"""
    pellet = get_object_or_404(Pellet, id=pellet_id)

    if request.method == 'POST':
        pellet_title = pellet.title
        pellet.delete()
        messages.success(request, f'Pellet "{pellet_title}" has been deleted successfully.')
        return redirect('admin_panel:pellet_management')

    return render(request, 'admin_panel/pellet_management.html', {'pellets': Pellet.objects.all().order_by('-created_at')})

@staff_member_required
def user_edit(request, user_id):
    """Edit a user"""
    user = get_object_or_404(User, id=user_id)

    if request.method == 'POST':
        # Get the data from the request
        username = request.POST.get('username')
        email = request.POST.get('email')
        phone_number = request.POST.get('phone_number')
        exp_level = request.POST.get('exp_level')

        # Update the user
        user.username = username
        user.email = email
        user.phone_number = phone_number
        user.exp_level = exp_level
        user.save()

        messages.success(request, f'User "{user.username}" has been updated successfully.')
        return redirect('admin_panel:user_management')

    return render(request, 'admin_panel/user_management.html', {'users': User.objects.all().order_by('-created_at')})

@staff_member_required
def user_delete(request, user_id):
    """Delete a user"""
    user = get_object_or_404(User, id=user_id)

    if request.method == 'POST':
        user_name = user.username
        user.delete()
        messages.success(request, f'User "{user_name}" has been deleted successfully.')
        return redirect('admin_panel:user_management')

    return render(request, 'admin_panel/user_management.html', {'users': User.objects.all().order_by('-created_at')})

@staff_member_required
def material_edit(request, material_id):
    """Edit a material"""
    material = get_object_or_404(Material, id=material_id)

    if request.method == 'POST':
        # Get the data from the request
        title = request.POST.get('title')
        content_type = request.POST.get('content_type')

        # Update the material
        material.title = title
        material.content_type = content_type
        material.save()

        messages.success(request, f'Material "{material.title}" has been updated successfully.')
        return redirect('admin_panel:material_management')

    return render(request, 'admin_panel/material_management.html', {'materials': Material.objects.all().order_by('-created_at')})

@staff_member_required
def material_delete(request, material_id):
    """Delete a material"""
    material = get_object_or_404(Material, id=material_id)

    if request.method == 'POST':
        material_title = material.title
        material.delete()
        messages.success(request, f'Material "{material_title}" has been deleted successfully.')
        return redirect('admin_panel:material_management')

    return render(request, 'admin_panel/material_management.html', {'materials': Material.objects.all().order_by('-created_at')})
