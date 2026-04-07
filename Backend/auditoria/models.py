from django.db import models
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from implementacion.models import EvaluacionControl, Empresa

User = get_user_model()


class ProcesoAuditoria(models.Model):
    """
    Representa un programa/ciclo de auditoría ISO 27001.
    Agrupa múltiples revisiones de controles bajo un mismo proceso auditivo.
    Implementa control de estado para garantizar inmutabilidad de auditorías cerradas.
    """
    ESTADO_CHOICES = [
        ('ACTIVA', 'Activa'),
        ('FINALIZADA', 'Finalizada'),
    ]
    
    nombre = models.CharField(
        max_length=200,
        verbose_name='Nombre del Proceso',
        help_text='Ej: Auditoría Anual 2026, Auditoría de Recertificación Q1'
    )
    empresa = models.ForeignKey(
        Empresa,
        on_delete=models.PROTECT,
        related_name='procesos_auditoria',
        verbose_name='Empresa Auditada'
    )
    auditor = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='procesos_auditoria_asignados',
        verbose_name='Auditor Responsable',
        help_text='Usuario con rol AUDITOR asignado al proceso'
    )
    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de Creación'
    )
    fecha_cierre = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Fecha de Cierre',
        help_text='Fecha en que el proceso fue finalizado'
    )
    estado = models.CharField(
        max_length=20,
        choices=ESTADO_CHOICES,
        default='ACTIVA',
        verbose_name='Estado del Proceso'
    )
    visible_para_auditor = models.BooleanField(
        default=True,
        verbose_name='Visible para Auditor',
        help_text='Permite ocultar el proceso del panel del auditor sin eliminar registros.'
    )
    
    class Meta:
        verbose_name = 'Proceso de Auditoría'
        verbose_name_plural = 'Procesos de Auditoría'
        ordering = ['-fecha_creacion']
        indexes = [
            models.Index(fields=['empresa', 'estado']),
            models.Index(fields=['auditor', 'estado']),
        ]
    
    def __str__(self):
        return f"{self.nombre} - {self.empresa.nombre} ({self.get_estado_display()})"
    
    def clean(self):
        """
        Validaciones de negocio a nivel de modelo.
        """
        super().clean()
        
        # Validar que el auditor tenga el rol correcto
        if self.auditor:
            if not hasattr(self.auditor, 'rol') or self.auditor.rol not in ['AUDITOR', 'AUDITOR_INTERNO']:
                raise ValidationError({
                    'auditor': 'El usuario asignado debe tener rol de AUDITOR.'
                })
        
        # Validar que si está finalizada, debe tener fecha de cierre
        if self.estado == 'FINALIZADA' and not self.fecha_cierre:
            raise ValidationError({
                'fecha_cierre': 'Un proceso finalizado debe tener fecha de cierre.'
            })
    
    def save(self, *args, **kwargs):
        """
        Sobrescribe save para ejecutar validaciones antes de guardar.
        Al cambiar a FINALIZADA, registra fecha_cierre automáticamente.
        No modifica snapshots de revisiones para preservar inmutabilidad histórica.
        """
        # Detectar transición a FINALIZADA para sellar la fecha de cierre
        if self.pk:
            original = ProcesoAuditoria.objects.get(pk=self.pk)
            if original.estado != 'FINALIZADA' and self.estado == 'FINALIZADA':
                if not self.fecha_cierre:
                    from django.utils import timezone
                    self.fecha_cierre = timezone.now()
        
        self.full_clean()
        super().save(*args, **kwargs)
    
    def total_controles_empresa(self):
        """
        Calcula el total de controles implementados por la empresa.
        Usado para medir el progreso del proceso de auditoría.
        """
        return EvaluacionControl.objects.filter(
            empresa=self.empresa,
            estado='IMPLEMENTADO'
        ).count()
    
    def controles_auditados(self):
        """
        Cuenta cuántos controles han sido auditados en este proceso.
        """
        return self.revisiones.count()
    
    def progreso_porcentaje(self):
        """
        Calcula el porcentaje de progreso del proceso de auditoría.
        División segura: retorna 0 si no hay controles implementados.
        """
        total = self.total_controles_empresa()
        if total == 0:
            return 0
        
        auditados = self.controles_auditados()
        return min(100, int((auditados / total) * 100))
    
    def puede_finalizar(self):
        """
        Verifica si el proceso puede ser finalizado.
        Retorna tupla (bool, mensaje)
        """
        if self.estado == 'FINALIZADA':
            return False, 'El proceso ya está finalizado.'
        
        progreso = self.progreso_porcentaje()
        if progreso < 100:
            return False, f'El proceso está al {progreso}%. Debe completar el 100% de los controles antes de finalizar.'
        
        return True, 'El proceso puede ser finalizado.'


class RevisionAuditoria(models.Model):
    """
    Modelo que representa una revisión individual dentro de un proceso de auditoría.
    Los snapshots de estado, justificación y evidencias se congelan al momento de registrar esta revisión individual, garantizando inmutabilidad y trazabilidad.
    """
    VEREDICTO_CHOICES = [
        ('CONFORME', 'Conforme'),
        ('NO_CONFORME', 'No Conforme'),
        ('NO_APLICA', 'No Aplica'),
    ]
    
    proceso = models.ForeignKey(
        ProcesoAuditoria,
        on_delete=models.CASCADE,
        related_name='revisiones',
        verbose_name='Proceso de Auditoría',
        help_text='Programa de auditoría al que pertenece esta revisión'
    )
    evaluacion_control = models.ForeignKey(
        EvaluacionControl,
        on_delete=models.PROTECT,
        related_name='revisiones_auditoria',
        verbose_name='Evaluación del Control',
        help_text='Control ISO que está siendo auditado'
    )
    auditor = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='revisiones_realizadas',
        verbose_name='Auditor'
    )
    veredicto = models.CharField(
        max_length=20,
        choices=VEREDICTO_CHOICES,
        verbose_name='Veredicto de Auditoría'
    )
    observaciones = models.TextField(
        blank=True,
        null=True,
        verbose_name='Observaciones del Auditor',
        help_text='Hallazgos, recomendaciones o comentarios'
    )
    estado_implementacion_snapshot = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name='Estado de Implementación (Snapshot)',
        help_text='Estado de implementación de los controles congelado(s) al momento de registrar esta revisión individual.'
    )
    justificacion_snapshot = models.TextField(
        blank=True,
        null=True,
        verbose_name='Justificación (Snapshot)',
        help_text='Justificación de los controles congelada(s) al momento de registrar esta revisión individual.'
    )
    evidencias_snapshot = models.JSONField(
        blank=True,
        null=True,
        verbose_name='Evidencias (Snapshot)',
        help_text='Evidencia(s) de los controles congelada(s) al momento de registrar esta revisión individual. Formato: [{"id": 1, "archivo": "/media/evidencias/file.pdf", "fecha_subida": "2026-04-05"}]'
    )
    implementador_snapshot = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name='Implementador (Snapshot)',
        help_text='Nombre del responsable de la implementación al momento de registrar la revisión individual.'
    )
    fecha_revision = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de Revisión'
    )
    fecha_actualizacion = models.DateTimeField(
        auto_now=True,
        verbose_name='Última Actualización'
    )
    
    class Meta:
        verbose_name = 'Revisión de Auditoría'
        verbose_name_plural = 'Revisiones de Auditorías'
        ordering = ['-fecha_revision']
        unique_together = ['proceso', 'evaluacion_control']
        indexes = [
            models.Index(fields=['proceso', 'veredicto']),
            models.Index(fields=['auditor', 'fecha_revision']),
        ]
    
    def __str__(self):
        auditor_nombre = 'Sin auditor asignado'
        if self.auditor:
            auditor_nombre = self.auditor.get_full_name() or self.auditor.username

        return (
            f"{self.proceso.nombre} - "
            f"{self.evaluacion_control.control.identificador} - "
            f"{self.veredicto} "
            f"({auditor_nombre})"
        )
    
    def clean(self):
        """
        Validaciones de negocio críticas.
        """
        super().clean()
        
        # VALIDACIÓN CRÍTICA: Bloqueo de auditorías finalizadas
        if self.proceso_id and self.proceso.estado == 'FINALIZADA':
            raise ValidationError(
                'Esta auditoría está cerrada y es de solo lectura. '
                'No se pueden agregar o modificar revisiones en procesos finalizados.'
            )
        
        # Validar que la evaluación pertenece a la empresa del proceso
        if self.proceso_id and self.evaluacion_control_id:
            if self.evaluacion_control.empresa != self.proceso.empresa:
                raise ValidationError({
                    'evaluacion_control': 
                    f'El control debe pertenecer a la empresa {self.proceso.empresa.nombre}.'
                })
        
        # Validar que el auditor coincide con el del proceso
        if self.proceso_id and self.auditor_id:
            if not self.proceso.auditor:
                raise ValidationError({
                    'proceso': 'El proceso no tiene auditor asignado. Reasigna un auditor para continuar.'
                })

            if self.auditor != self.proceso.auditor:
                auditor_esperado = self.proceso.auditor.get_full_name() or self.proceso.auditor.username
                raise ValidationError({
                    'auditor': 
                    f'El auditor debe ser {auditor_esperado}.'
                })
    
    def save(self, *args, **kwargs):
        """
        Guarda la revisión de auditoría.
        Captura snapshot SOLO al crear la revisión.
        NO permite modificaciones si el proceso está finalizado.
        """
        # CRÍTICO: Capturar snapshot solo en creación inicial
        if self._state.adding and self.evaluacion_control_id:
            self.estado_implementacion_snapshot = self.evaluacion_control.estado
            self.justificacion_snapshot = self.evaluacion_control.justificacion
        
        # Validar ANTES de guardar (incluye bloqueo de procesos finalizados)
        self.full_clean()
        super().save(*args, **kwargs)
