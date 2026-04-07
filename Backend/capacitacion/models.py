from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils import timezone


class CursoCapacitacion(models.Model):
    """
    Curso de capacitacion hibrido:
    - Global Aegis: empresa null y creado_por_admin true.
    - Privado tenant: empresa != null y creado_por_admin false.
    """

    titulo = models.CharField(max_length=220)
    descripcion = models.TextField(blank=True)
    empresa = models.ForeignKey(
        'implementacion.Empresa',
        on_delete=models.CASCADE,
        related_name='cursos_capacitacion',
        null=True,
        blank=True,
    )
    creado_por_admin = models.BooleanField(
        default=False,
        help_text='True cuando el curso es oficial y global de Aegis.',
    )
    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='cursos_creados_capacitacion',
        null=True,
        blank=True,
    )
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Curso de Capacitacion'
        verbose_name_plural = 'Cursos de Capacitacion'
        ordering = ['-fecha_creacion']
        constraints = [
            models.CheckConstraint(
                condition=(
                    Q(creado_por_admin=True, empresa__isnull=True)
                    | Q(creado_por_admin=False, empresa__isnull=False)
                ),
                name='curso_capacitacion_visibilidad_valida',
            ),
        ]

    def __str__(self):
        if self.creado_por_admin:
            return f'[Aegis] {self.titulo}'
        return f'[{self.empresa}] {self.titulo}'


class ModuloContenido(models.Model):
    TIPO_VIDEO = 'VIDEO'
    TIPO_PDF = 'PDF'
    TIPO_CUESTIONARIO = 'CUESTIONARIO'

    TIPO_CHOICES = [
        (TIPO_VIDEO, 'Video'),
        (TIPO_PDF, 'PDF / Lectura'),
        (TIPO_CUESTIONARIO, 'Cuestionario'),
    ]

    curso = models.ForeignKey(
        CursoCapacitacion,
        on_delete=models.CASCADE,
        related_name='modulos',
    )
    titulo = models.CharField(max_length=220)
    descripcion = models.TextField(blank=True)
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    url_recurso = models.URLField(max_length=700)
    orden = models.PositiveIntegerField(default=1)
    duracion_minutos = models.PositiveIntegerField(default=10)
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Modulo de Contenido'
        verbose_name_plural = 'Modulos de Contenido'
        ordering = ['orden', 'id']
        constraints = [
            models.UniqueConstraint(
                fields=['curso', 'orden'],
                name='modulo_orden_unico_por_curso',
            ),
        ]

    def __str__(self):
        return f'{self.curso.titulo} - M{self.orden}: {self.titulo}'


class ProgresoUsuario(models.Model):
    """
    Traza progreso por curso y modulos completados para cada usuario.
    """

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='progresos_capacitacion',
    )
    curso = models.ForeignKey(
        CursoCapacitacion,
        on_delete=models.CASCADE,
        related_name='progresos',
    )
    modulos_completados = models.ManyToManyField(
        ModuloContenido,
        related_name='progresos_usuarios',
        blank=True,
    )
    porcentaje_completado = models.PositiveIntegerField(default=0)
    curso_completado = models.BooleanField(default=False)
    fecha_ultima_actividad = models.DateTimeField(auto_now=True)
    fecha_completado = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Progreso de Usuario'
        verbose_name_plural = 'Progresos de Usuarios'
        ordering = ['-fecha_ultima_actividad']
        constraints = [
            models.UniqueConstraint(
                fields=['usuario', 'curso'],
                name='progreso_unico_usuario_curso',
            ),
        ]

    def __str__(self):
        usuario_display = self.usuario.username if self.usuario else 'Usuario eliminado'
        return f'{usuario_display} - {self.curso.titulo} ({self.porcentaje_completado}%)'

    def recalcular_estado(self):
        total_modulos = self.curso.modulos.filter(activo=True).count()
        completados = self.modulos_completados.filter(curso=self.curso, activo=True).count()

        if total_modulos == 0:
            porcentaje = 0
            completado = False
        else:
            porcentaje = int((completados / total_modulos) * 100)
            completado = completados == total_modulos

        self.porcentaje_completado = porcentaje
        self.curso_completado = completado
        self.fecha_completado = timezone.now() if completado else None
        self.save(
            update_fields=[
                'porcentaje_completado',
                'curso_completado',
                'fecha_completado',
                'fecha_ultima_actividad',
            ]
        )
