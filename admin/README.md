## danloo 管理员后台

This is a Django admin panel for managing the danloo system's various components including users, pellets, materials, tasks, and tags.

### Features

- User Management: View, edit, and delete users
- Pellet Management: Manage pellets created by users
- Material Management: Handle user uploaded materials
- Task & Job Management: Monitor processing tasks and jobs
- Tag Management: Organize and manage tags for pellets

### Installation

1. Install Django:
   ```
   pip install Django>=4.2.0,<5.0.0
   ```

2. Run migrations to set up the database:
   ```
   python manage.py migrate
   ```

3. Create a superuser account:
   ```
   python manage.py createsuperuser
   ```

### Usage

1. Start the development server:
   ```
   python manage.py runserver
   ```

2. Access the admin panel at http://localhost:8000/admin/

3. Access the custom admin views at:
   - Dashboard: http://localhost:8000/
   - User Management: http://localhost:8000/users/
   - Pellet Management: http://localhost:8000/pellets/
   - Task & Job Management: http://localhost:8000/tasks/
   - Tag Management: http://localhost:8000/tags/
   - Material Management: http://localhost:8000/materials/
