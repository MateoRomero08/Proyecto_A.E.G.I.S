from django.db import models
from django.conf import settings


class Empresa(models.Model):
    TIPO_CHOICES = [
        ('PEQUENA', 'Pequeña'),
        ('MEDIANA', 'Mediana'),
    ]
    
    nombre = models.CharField(max_length=200, unique=True)
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    revision_solicitada = models.BooleanField(
        default=False,
        verbose_name='Revisión Solicitada',
        help_text='Indica si la implementación se envió a auditoría y está pendiente de atención.'
    )
    fecha_solicitud_revision = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Fecha de Solicitud de Revisión'
    )
    
    class Meta:
        verbose_name = 'Empresa'
        verbose_name_plural = 'Empresas'
    
    def __str__(self):
        return self.nombre


class ControlISO(models.Model):
    DOMINIO_CHOICES = [
        ('ORGANIZACIONAL', 'Organizacional'),
        ('PERSONAS', 'Personas'),
        ('FISICO', 'Físico'),
        ('TECNOLOGICO', 'Tecnológico'),
    ]
    
    identificador = models.CharField(max_length=10, unique=True)
    nombre = models.CharField(max_length=300)
    dominio = models.CharField(max_length=20, choices=DOMINIO_CHOICES)
    descripcion_guia = models.TextField()
    
    class Meta:
        verbose_name = 'Control ISO'
        verbose_name_plural = 'Controles ISO'
        ordering = ['identificador']
    
    def __str__(self):
        return f"{self.identificador} - {self.nombre}"


class EvaluacionControl(models.Model):
    ESTADO_CHOICES = [
        ('IMPLEMENTADO', 'Implementado'),
        ('EN_PROCESO', 'En Proceso'),
        ('NO_IMPLEMENTADO', 'No Implementado'),
        ('NO_APLICA', 'No Aplica'),
    ]
    
    empresa = models.ForeignKey(Empresa, on_delete=models.PROTECT, related_name='evaluaciones')
    control = models.ForeignKey(ControlISO, on_delete=models.CASCADE, related_name='evaluaciones')
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='evaluaciones_controles'
    )
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='NO_IMPLEMENTADO')
    justificacion = models.TextField(blank=True, null=True)
    
    class Meta:
        verbose_name = 'Evaluación de Control'
        verbose_name_plural = 'Evaluaciones de Controles'
        unique_together = ['empresa', 'control']

    def save(self, *args, **kwargs):
        """
        Limpieza automática de evidencias cuando el estado es NO_APLICA.
        Cumplimiento ISO 27001: solo se eliminan registros relacionales,
        nunca se borra el archivo físico para no romper snapshots históricos.
        """
        super().save(*args, **kwargs)

        if self.estado == 'NO_APLICA' and self.pk:
            # Borrado lógico/relacional: elimina filas de Evidencia en BD.
            # Se omite explícitamente el borrado físico del archivo por trazabilidad ISO 27001.
            self.evidencias.all().delete()
    
    def __str__(self):
        return f"{self.empresa.nombre} - {self.control.identificador}"


class Evidencia(models.Model):
    evaluacion = models.ForeignKey(EvaluacionControl, on_delete=models.CASCADE, related_name='evidencias')
    archivo = models.FileField(upload_to='evidencias/')
    fecha_subida = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Evidencia'
        verbose_name_plural = 'Evidencias'
        ordering = ['-fecha_subida']
    
    def __str__(self):
        return f"Evidencia {self.id} - {self.evaluacion}"
