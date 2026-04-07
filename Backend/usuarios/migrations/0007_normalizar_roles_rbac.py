from django.db import migrations


def normalizar_roles(apps, schema_editor):
    UsuarioCustom = apps.get_model('usuarios', 'UsuarioCustom')

    # Migración de valor legacy de auditor.
    UsuarioCustom.objects.filter(rol='AUDITOR_INTERNO').update(rol='AUDITOR')

    # Renombrado funcional: administrador de empresa => rol LIDER_EQUIPO.
    UsuarioCustom.objects.filter(
        is_superuser=False,
        es_administrador_empresa=True,
    ).exclude(rol='LIDER_EQUIPO').update(rol='LIDER_EQUIPO')

    # Coherencia del flag legado con el nuevo rol.
    UsuarioCustom.objects.filter(
        is_superuser=False,
        rol='LIDER_EQUIPO',
    ).update(es_administrador_empresa=True)

    UsuarioCustom.objects.filter(
        is_superuser=False,
        es_administrador_empresa=True,
    ).exclude(rol='LIDER_EQUIPO').update(es_administrador_empresa=False)


def revertir_normalizacion_roles(apps, schema_editor):
    UsuarioCustom = apps.get_model('usuarios', 'UsuarioCustom')

    # Rollback parcial de compatibilidad.
    UsuarioCustom.objects.filter(rol='AUDITOR').update(rol='AUDITOR_INTERNO')


class Migration(migrations.Migration):

    dependencies = [
        ('usuarios', '0006_alter_usuariocustom_rol'),
    ]

    operations = [
        migrations.RunPython(normalizar_roles, revertir_normalizacion_roles),
    ]
