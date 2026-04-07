# Generated manually - Removing obsolete estado_snapshot field
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('auditoria', '0006_revisionauditoria_estado_snapshot'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='revisionauditoria',
            name='estado_snapshot',
        ),
    ]
