from .permission_seeder import PermissionSeeder
from .role_seeder import RoleSeeder
from .user_seeder import UserSeeder

# Order matters — roles depend on permissions, users depend on roles
SEEDERS: list = [
    PermissionSeeder,
    RoleSeeder,
    UserSeeder,
]
