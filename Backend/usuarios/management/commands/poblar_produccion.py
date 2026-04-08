from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from implementacion.models import Empresa


User = get_user_model()

EMPRESAS_PRODUCCION = [
    {
        "nombre": "Nexora",
        "tipo": "MEDIANA",
        "slug": "nx",
        "dominio": "nexora.aegis",
    },
    {
        "nombre": "Ciphera",
        "tipo": "PEQUENA",
        "slug": "cf",
        "dominio": "ciphera.aegis",
    },
]

PLANTILLA_USUARIOS_EMPRESA = [
    {
        "rol": "LIDER_EQUIPO",
        "sufijo": "lider",
        "first_name": "Lia",
        "last_name": "Core",
        "es_admin_empresa": True,
    },
    {
        "rol": "IMPLEMENTADOR",
        "sufijo": "impl",
        "first_name": "Iker",
        "last_name": "Build",
        "es_admin_empresa": False,
    },
    {
        "rol": "AUDITOR",
        "sufijo": "aud",
        "first_name": "Ari",
        "last_name": "Trace",
        "es_admin_empresa": False,
    },
    {
        "rol": "CAPACITADOR",
        "sufijo": "cap",
        "first_name": "Cami",
        "last_name": "Train",
        "es_admin_empresa": False,
    },
    {
        "rol": "EMPLEADO",
        "sufijo": "emp",
        "first_name": "Leo",
        "last_name": "Flow",
        "es_admin_empresa": False,
    },
]


def _email_disponible(email_base, user_id=None):
    email_candidato = email_base
    consecutivo = 1

    while User.objects.filter(email__iexact=email_candidato).exclude(pk=user_id).exists():
        local, domain = email_base.split("@", 1)
        email_candidato = f"{local}+{consecutivo}@{domain}"
        consecutivo += 1

    return email_candidato


class Command(BaseCommand):
    help = (
        "Puebla datos operativos de produccion para pruebas controladas: "
        "2 empresas y usuarios por rol (sin crear superusuario ni ADMIN_SISTEMA)."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--password",
            default="Aegis2026!",
            help="Password comun para los usuarios creados/actualizados. Default: Aegis2026!",
        )
        parser.add_argument(
            "--keep-passwords",
            action="store_true",
            help="No sobreescribe passwords existentes; solo aplica al crear usuarios nuevos.",
        )
        parser.add_argument(
            "--skip-setup-roles",
            action="store_true",
            help="Omite la ejecucion automatica de setup_roles al final.",
        )

    def handle(self, *args, **options):
        password = options["password"].strip()
        keep_passwords = bool(options.get("keep_passwords"))
        skip_setup_roles = bool(options.get("skip_setup_roles"))

        if len(password) < 8:
            raise CommandError("La password debe tener minimo 8 caracteres.")

        empresas_creadas = []
        empresas_actualizadas = []
        usuarios_creados = []
        usuarios_actualizados = []
        usuarios_omitidos = []
        credenciales = []

        with transaction.atomic():
            for empresa_cfg in EMPRESAS_PRODUCCION:
                empresa, empresa_creada = Empresa.objects.get_or_create(
                    nombre=empresa_cfg["nombre"],
                    defaults={"tipo": empresa_cfg["tipo"]},
                )

                if empresa_creada:
                    empresas_creadas.append(empresa.nombre)
                elif empresa.tipo != empresa_cfg["tipo"]:
                    empresa.tipo = empresa_cfg["tipo"]
                    empresa.save(update_fields=["tipo"])
                    empresas_actualizadas.append(empresa.nombre)

                for plantilla_usuario in PLANTILLA_USUARIOS_EMPRESA:
                    username = f"{empresa_cfg['slug']}_{plantilla_usuario['sufijo']}"
                    email_base = f"{username}@{empresa_cfg['dominio']}"

                    user, user_creado = User.objects.get_or_create(
                        username=username,
                        defaults={
                            "email": email_base,
                            "first_name": plantilla_usuario["first_name"],
                            "last_name": plantilla_usuario["last_name"],
                            "rol": plantilla_usuario["rol"],
                            "empresa": empresa,
                            "is_active": True,
                            "is_approved": True,
                            "es_administrador_empresa": plantilla_usuario["es_admin_empresa"],
                        },
                    )

                    if user.is_superuser:
                        usuarios_omitidos.append(username)
                        continue

                    email_final = _email_disponible(email_base, user.pk)

                    user.email = email_final
                    user.first_name = plantilla_usuario["first_name"]
                    user.last_name = plantilla_usuario["last_name"]
                    user.rol = plantilla_usuario["rol"]
                    user.empresa = empresa
                    user.is_active = True
                    user.is_approved = True
                    user.is_staff = False
                    user.is_superuser = False
                    user.es_administrador_empresa = plantilla_usuario["es_admin_empresa"]

                    if user_creado or not keep_passwords:
                        user.set_password(password)

                    user.save()

                    if user_creado:
                        usuarios_creados.append(username)
                    else:
                        usuarios_actualizados.append(username)

                    credenciales.append(
                        {
                            "empresa": empresa.nombre,
                            "rol": plantilla_usuario["rol"],
                            "username": username,
                        }
                    )

        if not skip_setup_roles:
            self.stdout.write(self.style.NOTICE("Ejecutando setup_roles para sincronizar grupos/permisos..."))
            call_command("setup_roles")

        self.stdout.write(self.style.SUCCESS("Poblacion de produccion completada."))
        self.stdout.write(f"Empresas creadas: {len(empresas_creadas)}")
        self.stdout.write(f"Empresas actualizadas: {len(empresas_actualizadas)}")
        self.stdout.write(f"Usuarios creados: {len(usuarios_creados)}")
        self.stdout.write(f"Usuarios actualizados: {len(usuarios_actualizados)}")

        if usuarios_omitidos:
            self.stdout.write(
                self.style.WARNING(
                    "Usuarios omitidos por seguridad (superuser existente con mismo username): "
                    + ", ".join(sorted(usuarios_omitidos))
                )
            )

        self.stdout.write("\nCredenciales de prueba:")
        for item in credenciales:
            self.stdout.write(
                f"- {item['empresa']} | {item['rol']} | {item['username']} / {password if not keep_passwords else '[sin cambio]'}"
            )

        if skip_setup_roles:
            self.stdout.write(
                self.style.WARNING(
                    "setup_roles fue omitido (--skip-setup-roles). Ejecuta `python manage.py setup_roles` antes de probar RBAC."
                )
            )
