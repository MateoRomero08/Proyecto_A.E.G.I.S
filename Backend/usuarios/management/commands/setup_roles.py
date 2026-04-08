from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand, CommandError
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
    ("manage_global_users", "Puede administrar aprobacion/rechazo global de usuarios"),
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
            "usuarios.view_usuariocustom",
            "usuarios.change_usuariocustom",
            "usuarios.view_bitacoraseguridadusuario",
            "implementacion.view_empresa",
            "implementacion.view_controliso",
            "implementacion.view_evaluacioncontrol",
            "implementacion.view_evidencia",
            "auditoria.view_procesoauditoria",
            "auditoria.view_revisionauditoria",
            "capacitacion.view_cursocapacitacion",
            "capacitacion.view_modulocontenido",
            "capacitacion.view_progresousuario",
        ],
    },
    "LIDER_EQUIPO": {
        "permisos": [
            "usuarios.view_dashboard",
            "usuarios.view_equipo",
            "usuarios.view_reportes",
            "usuarios.view_usuariocustom",
            "usuarios.change_usuariocustom",
        ],
    },
    "CAPACITADOR": {
        "permisos": [
            "usuarios.view_dashboard",
            "usuarios.view_capacitacion",
            "capacitacion.view_cursocapacitacion",
            "capacitacion.add_cursocapacitacion",
            "capacitacion.change_cursocapacitacion",
            "capacitacion.view_modulocontenido",
            "capacitacion.add_modulocontenido",
            "capacitacion.change_modulocontenido",
            "capacitacion.view_progresousuario",
        ],
    },
    "AUDITOR": {
        "permisos": [
            "usuarios.view_dashboard",
            "usuarios.view_auditoria",
            "auditoria.view_procesoauditoria",
            "auditoria.add_procesoauditoria",
            "auditoria.change_procesoauditoria",
            "auditoria.view_revisionauditoria",
            "auditoria.add_revisionauditoria",
            "auditoria.change_revisionauditoria",
            "implementacion.view_controliso",
            "implementacion.view_evaluacioncontrol",
        ],
    },
    "IMPLEMENTADOR": {
        "permisos": [
            "usuarios.view_dashboard",
            "usuarios.view_implementacion",
            "implementacion.view_controliso",
            "implementacion.view_evaluacioncontrol",
            "implementacion.add_evaluacioncontrol",
            "implementacion.change_evaluacioncontrol",
            "implementacion.view_evidencia",
            "implementacion.add_evidencia",
            "implementacion.change_evidencia",
        ],
    },
    "EMPLEADO": {
        "permisos": [
            "usuarios.view_dashboard",
            "usuarios.view_capacitacion",
            "capacitacion.view_cursocapacitacion",
            "capacitacion.view_modulocontenido",
            "capacitacion.view_progresousuario",
        ],
    },
}


ROLES_SINCRONIZABLES = set(ROLES_GRUPOS.keys())
ROLES_AEGIS = tuple(ROLES_GRUPOS.keys())


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


def _aplicar_flags_operativos(usuario, rol_usuario):
    """
    Alinea banderas operativas mínimas por rol sin tocar superusuarios.
    """
    cambios = False

    if rol_usuario == "ADMIN_SISTEMA":
        if usuario.empresa_id is not None:
            usuario.empresa = None
            cambios = True
        if not usuario.is_approved:
            usuario.is_approved = True
            cambios = True
        if usuario.es_administrador_empresa:
            usuario.es_administrador_empresa = False
            cambios = True

    if rol_usuario == "LIDER_EQUIPO":
        if not usuario.es_administrador_empresa:
            usuario.es_administrador_empresa = True
            cambios = True
        if not usuario.is_approved:
            usuario.is_approved = True
            cambios = True

    return cambios


class Command(BaseCommand):
    help = "Provisiona RBAC de produccion para AEGIS: permisos, grupos y sincronizacion por rol."

    def add_arguments(self, parser):
        parser.add_argument(
            "--no-sync-users",
            action="store_true",
            help="No sincroniza usuarios existentes por rol hacia su grupo canónico.",
        )
        parser.add_argument(
            "--strict",
            action="store_true",
            help="Falla el comando si detecta permisos faltantes en lugar de continuar con warning.",
        )

    def handle(self, *args, **options):
        sync_users = not options["no_sync_users"]
        strict_mode = bool(options.get("strict"))

        permisos_custom_creados = 0
        permisos_custom_actualizados = 0
        grupos_creados = 0
        grupos_actualizados = 0
        usuarios_sincronizados = 0
        usuarios_flags_actualizados = 0
        permisos_faltantes = []

        with transaction.atomic():
            user_content_type = ContentType.objects.get_for_model(User)

            for codename, name in PERMISOS_FRONTEND_CUSTOM:
                permiso, created = Permission.objects.get_or_create(
                    content_type=user_content_type,
                    codename=codename,
                    defaults={"name": name},
                )

                if created:
                    permisos_custom_creados += 1
                elif permiso.name != name:
                    permiso.name = name
                    permiso.save(update_fields=["name"])
                    permisos_custom_actualizados += 1

            grupos_por_nombre = {}

            for nombre_grupo, config in ROLES_GRUPOS.items():
                grupo, created = Group.objects.get_or_create(name=nombre_grupo)

                if created:
                    grupos_creados += 1
                else:
                    grupos_actualizados += 1

                permisos_grupo = []
                for permiso_nombre in config["permisos"]:
                    permiso = _resolver_permiso(permiso_nombre)
                    if permiso is None:
                        permisos_faltantes.append(permiso_nombre)
                        continue

                    if permiso.codename.startswith("delete_"):
                        continue

                    permisos_grupo.append(permiso)

                grupo.permissions.set(permisos_grupo)
                grupos_por_nombre[nombre_grupo] = grupo

            if sync_users:
                for usuario in User.objects.filter(is_superuser=False):
                    rol_usuario = _normalizar_rol_usuario(getattr(usuario, "rol", None))
                    if rol_usuario not in ROLES_SINCRONIZABLES:
                        continue

                    grupo_objetivo = grupos_por_nombre.get(rol_usuario)
                    if grupo_objetivo is None:
                        continue

                    grupos_rbac_actuales = list(usuario.groups.filter(name__in=ROLES_AEGIS))
                    cambios = False

                    for grupo in grupos_rbac_actuales:
                        if grupo.id != grupo_objetivo.id:
                            usuario.groups.remove(grupo)
                            cambios = True

                    if not usuario.groups.filter(id=grupo_objetivo.id).exists():
                        usuario.groups.add(grupo_objetivo)
                        cambios = True

                    if _aplicar_flags_operativos(usuario, rol_usuario):
                        usuario.save(update_fields=["empresa", "is_approved", "es_administrador_empresa"])
                        usuarios_flags_actualizados += 1

                    if cambios:
                        usuarios_sincronizados += 1

        self.stdout.write(self.style.SUCCESS("RBAC definitivo provisionado correctamente."))
        self.stdout.write(f"Permisos frontend custom creados: {permisos_custom_creados}")
        self.stdout.write(f"Permisos frontend custom actualizados: {permisos_custom_actualizados}")
        self.stdout.write(f"Grupos creados: {grupos_creados}")
        self.stdout.write(f"Grupos actualizados: {grupos_actualizados}")

        if sync_users:
            self.stdout.write(f"Usuarios sincronizados por rol canónico: {usuarios_sincronizados}")
            self.stdout.write(f"Usuarios con flags operativos ajustados: {usuarios_flags_actualizados}")
        else:
            self.stdout.write("Sincronización de usuarios omitida (--no-sync-users).")

        if permisos_faltantes:
            faltantes_unicos = sorted(set(permisos_faltantes))
            mensaje_faltantes = (
                "Permisos no encontrados (verifica migraciones/apps instaladas): "
                + ", ".join(faltantes_unicos)
            )

            if strict_mode:
                raise CommandError(mensaje_faltantes)

            self.stdout.write(
                self.style.WARNING(mensaje_faltantes)
            )

        self.stdout.write(
            self.style.WARNING(
                "Verificación de seguridad: no se asignaron permisos delete_* a grupos no superadmin."
            )
        )
