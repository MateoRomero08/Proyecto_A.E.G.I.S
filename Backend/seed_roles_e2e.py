from django.contrib.auth import get_user_model

from implementacion.models import Empresa


User = get_user_model()
PASSWORD = "Aegis2026!"

empresa, _ = Empresa.objects.get_or_create(
    nombre="Empresa Demo E2E",
    defaults={"tipo": "PEQUENA"},
)

created_users = []
updated_users = []


def upsert_user(username, email, first_name, last_name, rol, es_admin_empresa=False):
    user, created = User.objects.get_or_create(
        username=username,
        defaults={
            "email": email,
            "first_name": first_name,
            "last_name": last_name,
            "rol": rol,
            "empresa": empresa,
            "is_approved": True,
            "is_active": True,
            "es_administrador_empresa": es_admin_empresa,
        },
    )

    user.email = email
    user.first_name = first_name
    user.last_name = last_name
    user.rol = rol
    user.empresa = empresa
    user.is_active = True
    user.is_approved = True
    user.is_staff = False
    user.is_superuser = False
    user.es_administrador_empresa = es_admin_empresa
    user.set_password(PASSWORD)
    user.save()

    if created:
        created_users.append(username)
    else:
        updated_users.append(username)


upsert_user(
    username="lider.e2e",
    email="lider.e2e@empresa-demo.com",
    first_name="Lider",
    last_name="Equipo",
    rol="LIDER_EQUIPO",
    es_admin_empresa=True,
)
upsert_user(
    username="implementador.e2e",
    email="implementador.e2e@empresa-demo.com",
    first_name="Implementador",
    last_name="Demo",
    rol="IMPLEMENTADOR",
)
upsert_user(
    username="auditor.e2e",
    email="auditor.e2e@empresa-demo.com",
    first_name="Auditor",
    last_name="Demo",
    rol="AUDITOR",
)
upsert_user(
    username="capacitador.e2e",
    email="capacitador.e2e@empresa-demo.com",
    first_name="Capacitador",
    last_name="Demo",
    rol="CAPACITADOR",
)
upsert_user(
    username="empleado.e2e",
    email="empleado.e2e@empresa-demo.com",
    first_name="Empleado",
    last_name="Demo",
    rol="EMPLEADO",
)

print("=== Seed E2E completado ===")
print(f"Empresa: {empresa.nombre} (id={empresa.id})")
print(f"Creados: {len(created_users)} -> {created_users}")
print(f"Actualizados: {len(updated_users)} -> {updated_users}")
print("Credenciales comunes:")
for username in [
    "lider.e2e",
    "implementador.e2e",
    "auditor.e2e",
    "capacitador.e2e",
    "empleado.e2e",
]:
    print(f"  - {username} / {PASSWORD}")
