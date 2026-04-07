from django.contrib import admin
from .models import RevisionAuditoria, ProcesoAuditoria


@admin.register(ProcesoAuditoria)
class ProcesoAuditoriaAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'empresa', 'auditor', 'estado', 'progreso_porcentaje', 'fecha_creacion', 'fecha_cierre']
    list_filter = ['estado', 'empresa', 'fecha_creacion']
    search_fields = ['nombre', 'empresa__nombre', 'auditor__username']
    readonly_fields = ['fecha_creacion', 'fecha_cierre']
    
    fieldsets = (
        ('Información del Proceso', {
            'fields': ('nombre', 'empresa', 'auditor', 'estado')
        }),
        ('Fechas', {
            'fields': ('fecha_creacion', 'fecha_cierre')
        }),
    )
    
    def progreso_porcentaje(self, obj):
        return f"{obj.progreso_porcentaje()}%"
    progreso_porcentaje.short_description = 'Progreso'


@admin.register(RevisionAuditoria)
class RevisionAuditoriaAdmin(admin.ModelAdmin):
    list_display = ['id', 'proceso', 'get_control', 'auditor', 'veredicto', 'estado_implementacion_snapshot', 'fecha_revision']
    list_filter = ['veredicto', 'proceso__estado', 'fecha_revision']
    search_fields = [
        'proceso__nombre',
        'evaluacion_control__control__identificador',
        'evaluacion_control__control__nombre',
        'auditor__username'
    ]
    readonly_fields = [
        'fecha_revision',
        'fecha_actualizacion',
        'estado_implementacion_snapshot',
        'justificacion_snapshot',
        'evidencias_snapshot',
        'implementador_snapshot',
    ]
    
    fieldsets = (
        ('Relaciones', {
            'fields': ('proceso', 'evaluacion_control', 'auditor')
        }),
        ('Resultado de Auditoría', {
            'fields': ('veredicto', 'observaciones')
        }),
        ('Snapshot Inmutable (Solo Lectura)', {
            'fields': ('estado_implementacion_snapshot', 'justificacion_snapshot', 'evidencias_snapshot', 'implementador_snapshot'),
            'description': 'Estos campos se congelan automáticamente cuando se registra la auditoria para cada control no al finalizar la auditoria.'
        }),
        ('Metadata', {
            'fields': ('fecha_revision', 'fecha_actualizacion')
        }),
    )
    
    def get_control(self, obj):
        return f"{obj.evaluacion_control.control.identificador} - {obj.evaluacion_control.control.nombre}"
    get_control.short_description = 'Control'
    get_control.admin_order_field = 'evaluacion_control__control__identificador'
