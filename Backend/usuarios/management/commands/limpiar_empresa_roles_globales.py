from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Q


User = get_user_model()


class Command(BaseCommand):
    help = (
        "Limpia asignaciones de empresa para roles globales "
        "(ADMIN_SISTEMA y superusuarios), dejandolas en NULL."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--username",
            dest="username",
            default="",
            help="Filtra por username exacto para limpieza puntual.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Solo muestra candidatos sin persistir cambios.",
        )

    def handle(self, *args, **options):
        username = (options.get("username") or "").strip()
        dry_run = bool(options.get("dry_run"))

        queryset = User.objects.filter(
            Q(is_superuser=True) | Q(rol="ADMIN_SISTEMA")
        ).exclude(empresa__isnull=True)

        if username:
            queryset = queryset.filter(username=username)

        candidatos = list(queryset.select_related("empresa").order_by("username"))

        if not candidatos:
            self.stdout.write(self.style.SUCCESS("No hay usuarios globales con empresa asignada."))
            return

        self.stdout.write(
            f"Usuarios globales con empresa asignada detectados: {len(candidatos)}"
        )
        for user in candidatos:
            nombre_empresa = user.empresa.nombre if user.empresa else "(sin empresa)"
            self.stdout.write(
                f" - {user.username} | rol={user.rol} | superuser={user.is_superuser} | empresa={nombre_empresa}"
            )

        if dry_run:
            self.stdout.write(self.style.WARNING("Ejecucion en modo dry-run. Sin cambios."))
            return

        actualizados = 0
        with transaction.atomic():
            for user in candidatos:
                user.empresa = None
                user.save()
                actualizados += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Limpieza completada. Usuarios globales actualizados: {actualizados}"
            )
        )
