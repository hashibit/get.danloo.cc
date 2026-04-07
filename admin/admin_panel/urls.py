from django.urls import path
from . import views

app_name = 'admin_panel'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('users/', views.user_management, name='user_management'),
    path('pellets/', views.pellet_management, name='pellet_management'),
    path('tasks/', views.task_management, name='task_management'),
    path('tags/', views.tag_management, name='tag_management'),
    path('materials/', views.material_management, name='material_management'),

    # Tag edit and delete URLs
    path('tags/edit/<str:tag_id>/', views.tag_edit, name='tag_edit'),
    path('tags/delete/<str:tag_id>/', views.tag_delete, name='tag_delete'),

    # Pellet edit and delete URLs
    path('pellets/edit/<uuid:pellet_id>/', views.pellet_edit, name='pellet_edit'),
    path('pellets/delete/<uuid:pellet_id>/', views.pellet_delete, name='pellet_delete'),

    # User edit and delete URLs
    path('users/edit/<uuid:user_id>/', views.user_edit, name='user_edit'),
    path('users/delete/<uuid:user_id>/', views.user_delete, name='user_delete'),

    # Material edit and delete URLs
    path('materials/edit/<uuid:material_id>/', views.material_edit, name='material_edit'),
    path('materials/delete/<uuid:material_id>/', views.material_delete, name='material_delete'),
]
