from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand
from django.db import transaction


User = get_user_model()

PERMISOS_FRONTEND_CUSTOM = [
    ("view_dashboard", "Puede ver dashboard AEGIS"),
    ("view_implementacion", "Puede ver modulo de implementacion"),
    ("view_auditoria", "Puede ver modulo de auditoria"),
    ("view_capacitacion", "Puede ver modulo de capacitacion"),
    ("view_equipo", "Puede ver modulo de equipo"),
    ("view_reportes", "Puede ver modulo de reportes"),
    ("view_usuarios_globales", "Puede ver modulo global de usuarios"),
    ("manage_global_users", "Puede administrar usuarios globales"),
]

ROLES_GRUPOS = {
    "ADMIN_SISTEMA": {
        "permisos": [
            "usuarios.view_dashboard",
            "usuarios.view_equipo",
            "usuarios.view_reportes",
            "usuarios.view_usuarios_globales",
            "usuarios.view_capacitacion",
            "usuarios.manage_global_users",
            "usuarios.view_bitacoraseguridadusuario",
            "capacitacion.view_cursocapacitacion",
            "capacitacion.view_modulocontenido",
            "capacitacion.view_progresousuario",
        ]
    },
    "EMPLEADO": {
        "permisos": [
            "usuarios.view_dashboard",
            "usuarios.view_capacitacion",
            "capacitacion.view_cursocapacitacion",
            "capacitacion.view_modulocontenido",
            "capacitacion.view_progresousuario",
        ]
    },
    "IMPLEMENTADOR": {
        "permisos": [
            "usuarios.view_dashboard",
            "usuarios.view_implementacion",
            "usuarios.view_capacitacion",
            "implementacion.view_controliso",
            "implementacion.view_evaluacioncontrol",
            "implementacion.add_evaluacioncontrol",
            "implementacion.change_evaluacioncontrol",
            "capacitacion.view_cursocapacitacion",
            "capacitacion.view_modulocontenido",
            "capacitacion.view_progresousuario",
        ]
    },
    "AUDITOR": {
        "permisos": [
            "usuarios.view_dashboard",
            "usuarios.view_auditoria",
            "usuarios.view_capacitacion",
            "auditoria.view_procesoauditoria",
            "auditoria.add_procesoauditoria",
            "auditoria.change_procesoauditoria",
            "auditoria.view_revisionauditoria",
            "auditoria.add_revisionauditoria",
            "auditoria.change_revisionauditoria",
            "capacitacion.view_cursocapacitacion",
            "capacitacion.view_modulocontenido",
            "capacitacion.view_progresousuario",
        ]
    },
    "LIDER_EQUIPO": {
        "permisos": [
            "usuarios.view_dashboard",
            "usuarios.view_equipo",
            "usuarios.view_reportes",
            "usuarios.view_usuariocustom",
            "usuarios.change_usuariocustom",
        ]
    },
    "CAPACITADOR": {
        "permisos": [
            "usuarios.view_dashboard",
            "usuarios.view_capacitacion",
            "capacitacion.view_cursocapacitacion",
            "capacitacion.add_cursocapacitacion",
            "capacitacion.change_cursocapacitacion",
            "capacitacion.delete_cursocapacitacion",
            "capacitacion.view_modulocontenido",
            "capacitacion.add_modulocontenido",
            "capacitacion.change_modulocontenido",
            "capacitacion.delete_modulocontenido",
            "capacitacion.view_progresousuario",
        ]
    },
}


def _normalizar_rol_usuario(rol):
    if rol == "AUDITOR_INTERNO":
        return "AUDITOR"
    return rol


def _resolver_permiso(permiso_nombre):
    try:
        app_label, codename = permiso_nombre.split(".", 1)
    except ValueError:
        return None

    return Permission.objects.filter(content_type__app_label=app_label, codename=codename).first()


class Command(BaseCommand):
    help = "Crea y sincroniza grupos/permisos RBAC base de AEGIS de forma idempotente."

    def add_arguments(self, parser):
        parser.add_argument(
            "--no-sync-users",
            action="store_true",
            help="No sincroniza los usuarios existentes por rol hacia su grupo AEGIS.",
        )

    def handle(self, *args, **options):
        sync_users = not options["no_sync_users"]

        permisos_creados = 0
        permisos_actualizados = 0
        grupos_creados = 0
        grupos_actualizados = 0
        usuarios_sincronizados = 0
        permisos_faltantes = []

        with transaction.atomic():
            user_content_type = ContentType.objects.get_for_model(User)

            for codename, name in PERMISOS_FRONTEND_CUSTOM:
                permiso, creado = Permission.objects.get_or_create(
                    content_type=user_content_type,
                    codename=codename,
                    defaults={"name": name},
                )

                if creado:
                    permisos_creados += 1
                else:
                    if permiso.name != name:
                        permiso.name = name
                        permiso.save(update_fields=["name"])
                        permisos_actualizados += 1

            grupos_por_rol = {}

            for rol, config in ROLES_GRUPOS.items():
                grupo, creado = Group.objects.get_or_create(name=rol)

                if creado:
                    grupos_creados += 1
                else:
                    grupos_actualizados += 1

                permisos_grupo = []
                for permiso_nombre in config["permisos"]:
                    permiso = _resolver_permiso(permiso_nombre)
                    if permiso is None:
                        permisos_faltantes.append(permiso_nombre)
                        continue
                    permisos_grupo.append(permiso)

                grupo.permissions.set(permisos_grupo)
                grupos_por_rol[rol] = grupo

            if sync_users:
                roles_aegis = set(ROLES_GRUPOS.keys())

                for usuario in User.objects.filter(is_superuser=False):
                    rol_usuario = _normalizar_rol_usuario(getattr(usuario, "rol", None))
                    if rol_usuario not in grupos_por_rol:
                        continue

                    grupo_objetivo = grupos_por_rol[rol_usuario]
                    grupos_actuales_aegis = list(usuario.groups.filter(name__in=roles_aegis))

                    cambios = False
                    for grupo in grupos_actuales_aegis:
                        if grupo.id != grupo_objetivo.id:
                            usuario.groups.remove(grupo)
                            cambios = True

                    if not usuario.groups.filter(id=grupo_objetivo.id).exists():
                        usuario.groups.add(grupo_objetivo)
                        cambios = True

                    if cambios:
                        usuarios_sincronizados += 1

        self.stdout.write(self.style.SUCCESS("Seed RBAC AEGIS completado."))
        self.stdout.write(f"Permisos creados: {permisos_creados}")
        self.stdout.write(f"Permisos actualizados: {permisos_actualizados}")
        self.stdout.write(f"Grupos creados: {grupos_creados}")
        self.stdout.write(f"Grupos actualizados: {grupos_actualizados}")

        if sync_users:
            self.stdout.write(f"Usuarios sincronizados por rol: {usuarios_sincronizados}")
        else:
            self.stdout.write("Sincronizacion de usuarios omitida (--no-sync-users).")

        if permisos_faltantes:
            faltantes_unicos = sorted(set(permisos_faltantes))
            self.stdout.write(
                self.style.WARNING(
                    "Permisos no encontrados (verifica migrate/apps instaladas): "
                    + ", ".join(faltantes_unicos)
                )
            )
