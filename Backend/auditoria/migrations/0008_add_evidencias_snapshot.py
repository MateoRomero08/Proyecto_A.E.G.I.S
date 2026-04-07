# Generated manually - Adding evidencias_snapshot field
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('auditoria', '0007_remove_estado_snapshot_field'),
    ]

    operations = [
        migrations.AddField(
            model_name='revisionauditoria',
            name='evidencias_snapshot',
            field=models.JSONField(
                blank=True,
                null=True,
                verbose_name='Evidencias (Snapshot)',
                help_text='Lista de evidencias (archivos) congeladas al momento de finalizar la auditoría. '
                          'Formato: [{"id": 1, "archivo": "/media/evidencias/file.pdf", "fecha_subida": "2026-04-05"}]'
            ),
        ),
    ]
