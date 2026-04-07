"""
Script para poblar la base de datos con datos de prueba
Ejecutar: python manage.py shell < poblar_datos.py
"""

from django.contrib.auth import get_user_model
from implementacion.models import Empresa

User = get_user_model()

print("=" * 50)
print("POBLANDO BASE DE DATOS CON DATOS DE PRUEBA")
print("=" * 50)

# Crear Empresas
print("\n1. Creando empresas...")
empresa1, created = Empresa.objects.get_or_create(
    nombre="TechCorp Solutions",
    defaults={'tipo': 'MEDIANA'}
)
if created:
    print(f"   ✓ Empresa creada: {empresa1.nombre}")
else:
    print(f"   → Empresa ya existe: {empresa1.nombre}")

empresa2, created = Empresa.objects.get_or_create(
    nombre="Innovación Digital",
    defaults={'tipo': 'PEQUENA'}
)
if created:
    print(f"   ✓ Empresa creada: {empresa2.nombre}")
else:
    print(f"   → Empresa ya existe: {empresa2.nombre}")

# Crear Usuarios
print("\n2. Creando usuarios...")

# Superusuario (si no existe)
if not User.objects.filter(username='admin').exists():
    admin = User.objects.create_superuser(
        username='admin',
        email='admin@aegis.com',
        password='admin123',
        first_name='Administrador',
        last_name='Sistema'
    )
    print(f"   ✓ Superusuario creado: {admin.username}")
else:
    print(f"   → Superusuario ya existe: admin")

# Implementadores
usuarios_implementadores = [
    {
        'username': 'carlos.impl',
        'email': 'carlos.impl@techcorp.com',
        'password': 'carlos123',
        'first_name': 'Carlos',
        'last_name': 'Rodríguez',
        'rol': 'IMPLEMENTADOR',
        'empresa': empresa1
    },
    {
        'username': 'maria.impl',
        'email': 'maria.impl@innovacion.com',
        'password': 'maria123',
        'first_name': 'María',
        'last_name': 'González',
        'rol': 'IMPLEMENTADOR',
        'empresa': empresa2
    },
]

for user_data in usuarios_implementadores:
    if not User.objects.filter(username=user_data['username']).exists():
        user = User.objects.create_user(**user_data)
        print(f"   ✓ Implementador creado: {user.username} ({user.empresa.nombre})")
    else:
        print(f"   → Usuario ya existe: {user_data['username']}")

# Auditores
usuarios_auditores = [
    {
        'username': 'juan.audit',
        'email': 'juan.audit@techcorp.com',
        'password': 'juan123',
        'first_name': 'Juan',
        'last_name': 'Pérez',
        'rol': 'AUDITOR_INTERNO',
        'empresa': empresa1
    },
    {
        'username': 'ana.audit',
        'email': 'ana.audit@innovacion.com',
        'password': 'ana123',
        'first_name': 'Ana',
        'last_name': 'Martínez',
        'rol': 'AUDITOR_INTERNO',
        'empresa': empresa2
    },
]

for user_data in usuarios_auditores:
    if not User.objects.filter(username=user_data['username']).exists():
        user = User.objects.create_user(**user_data)
        print(f"   ✓ Auditor creado: {user.username} ({user.empresa.nombre})")
    else:
        print(f"   → Usuario ya existe: {user_data['username']}")

# Resumen
print("\n" + "=" * 50)
print("RESUMEN")
print("=" * 50)
print(f"Total empresas: {Empresa.objects.count()}")
print(f"Total usuarios: {User.objects.count()}")
print(f"  - Superusuarios: {User.objects.filter(is_superuser=True).count()}")
print(f"  - Implementadores: {User.objects.filter(rol='IMPLEMENTADOR').count()}")
print(f"  - Auditores: {User.objects.filter(rol='AUDITOR_INTERNO').count()}")

print("\n" + "=" * 50)
print("CREDENCIALES DE ACCESO")
print("=" * 50)
print("\nSuperusuario:")
print("  Username: admin")
print("  Password: admin123")

print("\nImplementadores:")
print("  TechCorp Solutions:")
print("    Username: carlos.impl")
print("    Password: carlos123")
print("\n  Innovación Digital:")
print("    Username: maria.impl")
print("    Password: maria123")

print("\nAuditores:")
print("  TechCorp Solutions:")
print("    Username: juan.audit")
print("    Password: juan123")
print("\n  Innovación Digital:")
print("    Username: ana.audit")
print("    Password: ana123")

print("\n" + "=" * 50)
print("¡DATOS CARGADOS EXITOSAMENTE!")
print("=" * 50)
