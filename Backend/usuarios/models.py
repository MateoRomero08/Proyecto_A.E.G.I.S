from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.contrib.auth.models import AbstractUser
from .managers import UsuarioCustomManager


class UsuarioCustom(AbstractUser):
    """
    Modelo de usuario personalizado para sistema multi-inquilino con RBAC.
    Permite gestionar usuarios con diferentes roles y asociarlos a empresas.
    """
    
    ROL_EMPLEADO = 'EMPLEADO'
    ROL_IMPLEMENTADOR = 'IMPLEMENTADOR'
    ROL_AUDITOR = 'AUDITOR'
    ROL_LIDER_EQUIPO = 'LIDER_EQUIPO'
    ROL_CAPACITADOR = 'CAPACITADOR'

    # Compatibilidad temporal para datos históricos previos al refactor.
    ROL_AUDITOR_LEGACY = 'AUDITOR_INTERNO'

    ROL_CHOICES = [
        (ROL_EMPLEADO, 'Empleado'),
        (ROL_IMPLEMENTADOR, 'Implementador'),
        (ROL_AUDITOR, 'Auditor'),
        (ROL_LIDER_EQUIPO, 'Líder de Equipo'),
        (ROL_CAPACITADOR, 'Capacitador'),
    ]

    email = models.EmailField(
        max_length=254,
        unique=True,
        blank=True,
        verbose_name='Correo electrónico'
    )
    
    rol = models.CharField(
        max_length=20,
        choices=ROL_CHOICES,
        default=ROL_EMPLEADO,
        verbose_name='Rol',
        help_text='Rol del usuario en el sistema'
    )
    
    empresa = models.ForeignKey(
        'implementacion.Empresa',
        on_delete=models.PROTECT,
        related_name='empleados',
        null=True,
        blank=True,
        verbose_name='Empresa',
        help_text='Empresa a la que pertenece el usuario'
    )

    is_approved = models.BooleanField(
        default=False,
        verbose_name='Aprobado',
        help_text='Indica si el usuario fue aprobado por el administrador de su empresa.'
    )

    es_administrador_empresa = models.BooleanField(
        default=False,
        verbose_name='Administrador de Empresa',
        help_text='Indica si el usuario administra su equipo dentro de la empresa.'
    )
    
    foto_perfil = models.ImageField(
        upload_to='perfiles/',
        null=True,
        blank=True,
        verbose_name='Foto de Perfil',
        help_text='Imagen de perfil del usuario'
    )
    
    # Manager personalizado
    objects = UsuarioCustomManager()
    
    class Meta:
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'
        ordering = ['-date_joined']
    
    def __str__(self):
        return f"{self.get_full_name() or self.username} - {self.get_rol_display()}"

    def save(self, *args, **kwargs):
        """
        Fuerza privilegios operativos para superusuarios antes de persistir.
        Evita bloqueos en flujos de aprobación o espera.
        """
        if self.rol == self.ROL_AUDITOR_LEGACY:
            self.rol = self.ROL_AUDITOR

        if self.is_superuser:
            self.is_approved = True
            self.es_administrador_empresa = True
        else:
            # Renombrado funcional: el liderazgo de equipo se modela como rol explícito.
            if self.es_administrador_empresa and self.rol != self.ROL_LIDER_EQUIPO:
                self.rol = self.ROL_LIDER_EQUIPO

            if self.rol == self.ROL_LIDER_EQUIPO:
                self.es_administrador_empresa = True

        super().save(*args, **kwargs)
    
    def es_implementador(self):
        """Verifica si el usuario es un implementador"""
        return self.rol == self.ROL_IMPLEMENTADOR

    def es_empleado(self):
        """Verifica si el usuario tiene rol base de empleado."""
        return self.rol == self.ROL_EMPLEADO
    
    def es_auditor(self):
        """Verifica si el usuario es un auditor"""
        return self.rol in {self.ROL_AUDITOR, self.ROL_AUDITOR_LEGACY}

    def es_lider_equipo(self):
        """Verifica si el usuario lidera la gestión operativa del equipo."""
        return self.rol == self.ROL_LIDER_EQUIPO

    def es_capacitador(self):
        """Verifica si el usuario está orientado al módulo de capacitación."""
        return self.rol == self.ROL_CAPACITADOR
    
    def tiene_empresa(self):
        """Verifica si el usuario está asociado a una empresa"""
        return self.empresa is not None


class BitacoraSeguridadUsuarioQuerySet(models.QuerySet):
    """QuerySet WORM: bloquea modificaciones masivas de registros históricos."""

    def delete(self):
        raise ValidationError('La bitácora es inmutable: no se permite eliminar registros.')

    def update(self, **kwargs):
        raise ValidationError('La bitácora es inmutable: no se permite actualizar registros.')


class BitacoraSeguridadUsuarioManager(models.Manager):
    """Manager WORM: usa QuerySet protegido y bloquea bulk_update."""

    def get_queryset(self):
        return BitacoraSeguridadUsuarioQuerySet(self.model, using=self._db)

    def bulk_update(self, objs, fields, batch_size=None):
        raise ValidationError('La bitácora es inmutable: no se permite bulk_update.')


class BitacoraSeguridadUsuario(models.Model):
    """
    Registro inmutable de eventos críticos sobre gestión de usuarios.
    Diseñado para trazabilidad ISO 27001 en operaciones administrativas.
    """

    ACCION_CHOICES = [
        ('CREACION_USUARIO', 'Creación de Usuario'),
        ('ACTUALIZACION_USUARIO', 'Actualización de Usuario'),
        ('CAMBIO_ROL', 'Cambio de Rol'),
        ('INACTIVACION_USUARIO', 'Inactivación de Usuario'),
        ('RESET_PASSWORD_FORZADO', 'Reseteo Forzado de Contraseña'),
        ('APROBACION_USUARIO', 'Aprobación de Usuario'),
        ('RECHAZO_USUARIO', 'Rechazo de Usuario'),
        ('LOGIN_EXITOSO', 'Login Exitoso'),
        ('LOGIN_FALLIDO', 'Login Fallido'),
        ('LOGOUT', 'Cierre de Sesión'),
    ]

    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='eventos_bitacora_realizados',
        verbose_name='Actor'
    )
    usuario_objetivo = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='eventos_bitacora_recibidos',
        verbose_name='Usuario Objetivo'
    )
    empresa = models.ForeignKey(
        'implementacion.Empresa',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='eventos_bitacora_usuarios',
        verbose_name='Empresa Relacionada'
    )
    accion = models.CharField(
        max_length=40,
        choices=ACCION_CHOICES,
        verbose_name='Acción'
    )
    detalle = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='Detalle Técnico'
    )
    ip_origen = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name='IP de Origen'
    )
    user_agent = models.CharField(
        max_length=512,
        blank=True,
        verbose_name='User Agent'
    )
    fecha_evento = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha del Evento'
    )

    objects = BitacoraSeguridadUsuarioManager()

    class Meta:
        verbose_name = 'Bitácora de Seguridad de Usuario'
        verbose_name_plural = 'Bitácoras de Seguridad de Usuarios'
        ordering = ['-fecha_evento']
        indexes = [
            models.Index(fields=['accion', 'fecha_evento']),
            models.Index(fields=['empresa', 'fecha_evento']),
            models.Index(fields=['actor', 'fecha_evento']),
        ]

    def __str__(self):
        actor = (
            self.actor.get_full_name() or self.actor.username
            if self.actor
            else 'Sistema/Anónimo'
        )
        return f"{self.get_accion_display()} por {actor} ({self.fecha_evento:%Y-%m-%d %H:%M:%S})"

    def save(self, *args, **kwargs):
        """
        WORM: solo permite CREATE. Cualquier UPDATE queda bloqueado.
        """
        if self.pk and BitacoraSeguridadUsuario._base_manager.filter(pk=self.pk).exists():
            raise ValidationError('La bitácora es inmutable: no se permite modificar registros existentes.')
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """
        WORM: bloquea eliminación directa de registros.
        """
        raise ValidationError('La bitácora es inmutable: no se permite eliminar registros.')


class Notificacion(models.Model):
    """
    Notificaciones in-app para eventos operativos dirigidos al usuario.
    """

    usuario_destino = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notificaciones',
        verbose_name='Usuario Destino'
    )
    titulo = models.CharField(
        max_length=200,
        verbose_name='Título'
    )
    mensaje = models.TextField(
        verbose_name='Mensaje'
    )
    leida = models.BooleanField(
        default=False,
        verbose_name='Leída'
    )
    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de Creación'
    )

    class Meta:
        verbose_name = 'Notificación'
        verbose_name_plural = 'Notificaciones'
        ordering = ['-fecha_creacion']
        indexes = [
            models.Index(fields=['usuario_destino', 'leida', 'fecha_creacion']),
        ]

    def __str__(self):
        return f"{self.titulo} -> {self.usuario_destino.username}"
