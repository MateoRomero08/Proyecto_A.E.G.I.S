import json
import urllib.parse
from rest_framework import serializers
from .models import RevisionAuditoria, ProcesoAuditoria
from implementacion.models import EvaluacionControl


def _nombre_auditor(auditor):
    if not auditor:
        return 'Sin auditor asignado'
    return auditor.get_full_name() or auditor.username


class ProcesoAuditoriaSerializer(serializers.ModelSerializer):
    """
    Serializer para Procesos de Auditoría con métricas calculadas.
    Incluye campos computados para progreso y estadísticas.
    """
    auditor_nombre = serializers.SerializerMethodField()
    empresa_nombre = serializers.CharField(
        source='empresa.nombre',
        read_only=True
    )
    total_controles = serializers.SerializerMethodField()
    controles_auditados = serializers.SerializerMethodField()
    progreso_porcentaje = serializers.SerializerMethodField()
    puede_finalizar = serializers.SerializerMethodField()
    
    class Meta:
        model = ProcesoAuditoria
        fields = [
            'id',
            'nombre',
            'empresa',
            'empresa_nombre',
            'auditor',
            'auditor_nombre',
            'fecha_creacion',
            'fecha_cierre',
            'estado',
            'visible_para_auditor',
            'total_controles',
            'controles_auditados',
            'progreso_porcentaje',
            'puede_finalizar'
        ]
        read_only_fields = ['id', 'fecha_creacion', 'fecha_cierre', 'auditor']
    
    def get_total_controles(self, obj):
        """
        Retorna el total de controles ISO disponibles en el sistema.
        """
        from implementacion.models import ControlISO

        return ControlISO.objects.count()

    def get_auditor_nombre(self, obj):
        return _nombre_auditor(obj.auditor)
    
    def get_controles_auditados(self, obj):
        """
        Retorna cuántas revisiones de auditoría se han realizado en este proceso.
        Usa la relación inversa 'revisiones' del ProcesoAuditoria.
        """
        return obj.revisiones.count()
    
    def get_progreso_porcentaje(self, obj):
        """
        Cálculo seguro del porcentaje de progreso.
        Formula: (controles_auditados / total_controles) * 100
        Maneja división por cero retornando 0.
        Retorna un número entero.
        """
        total = self.get_total_controles(obj)
        if total == 0:
            return 0

        auditados = self.get_controles_auditados(obj)
        return int((auditados / total) * 100)
    
    def get_puede_finalizar(self, obj):
        """
        Indica si el proceso puede ser finalizado.
        Retorna dict con 'puede' (bool) y 'mensaje' (str).
        """
        puede, mensaje = obj.puede_finalizar()
        return {
            'puede': puede,
            'mensaje': mensaje
        }


class RevisionAuditoriaSerializer(serializers.ModelSerializer):
    """
    Serializer para Revisiones de Auditoría.
    CRÍTICO: Devuelve datos snapshot si la auditoría está FINALIZADA,
    datos en vivo si está ACTIVA. Esto garantiza inmutabilidad histórica.
    """
    auditor_nombre = serializers.SerializerMethodField()
    control_identificador = serializers.CharField(
        source='evaluacion_control.control.identificador',
        read_only=True
    )
    control_nombre = serializers.CharField(
        source='evaluacion_control.control.nombre',
        read_only=True
    )
    proceso_nombre = serializers.CharField(
        source='proceso.nombre',
        read_only=True
    )
    proceso_estado = serializers.CharField(
        source='proceso.estado',
        read_only=True
    )
    evaluacion_control = serializers.PrimaryKeyRelatedField(
        queryset=EvaluacionControl.objects.all(),
        write_only=True
    )
    
    # Campos dinámicos: el serializer decide prioridad snapshot/en vivo.
    estado = serializers.SerializerMethodField(
        help_text='Estado del control: snapshot si FINALIZADA, en vivo si ACTIVA'
    )
    justificacion = serializers.SerializerMethodField(
        help_text='Justificación: snapshot si FINALIZADA, en vivo si ACTIVA'
    )
    evidencia = serializers.SerializerMethodField(
        help_text='URL de evidencia: snapshot si FINALIZADA, en vivo si ACTIVA'
    )
    
    # Exponer snapshots para transparencia (solo lectura)
    estado_implementacion_snapshot = serializers.CharField(read_only=True)
    justificacion_snapshot = serializers.CharField(read_only=True)
    implementador_snapshot = serializers.CharField(read_only=True)
    
    # Flag para indicar si los datos son históricos o en vivo
    es_historico = serializers.SerializerMethodField(
        help_text='True si los datos son snapshot congelado, False si son en vivo'
    )
    
    class Meta:
        model = RevisionAuditoria
        fields = [
            'id',
            'proceso',
            'proceso_nombre',
            'proceso_estado',
            'evaluacion_control',
            'control_identificador',
            'control_nombre',
            'auditor',
            'auditor_nombre',
            'veredicto',
            'observaciones',
            # Campos dinámicos (snapshot o en vivo)
            'estado',
            'justificacion',
            'evidencia',
            # Snapshots raw (solo lectura, para debugging/transparencia)
            'estado_implementacion_snapshot',
            'justificacion_snapshot',
            'evidencias_snapshot',
            'implementador_snapshot',
            # Metadatos
            'es_historico',
            'fecha_revision',
            'fecha_actualizacion'
        ]
        read_only_fields = [
            'id',
            'auditor',
            'estado_implementacion_snapshot',
            'justificacion_snapshot',
            'implementador_snapshot',
            'fecha_revision',
            'fecha_actualizacion'
        ]
    
    def validate(self, attrs):
        """
        Validación a nivel de serializer.
        CRÍTICO: Bloqueo de modificaciones en procesos finalizados.
        """
        # Para actualizaciones (instance existe)
        if self.instance:
            if self.instance.proceso.estado == 'FINALIZADA':
                raise serializers.ValidationError(
                    'Esta auditoría está cerrada y es de solo lectura. '
                    'No se pueden modificar revisiones en procesos finalizados.'
                )
        
        # Para creaciones (validar el proceso que viene en attrs)
        if 'proceso' in attrs:
            proceso = attrs['proceso']
            if proceso.estado == 'FINALIZADA':
                raise serializers.ValidationError({
                    'proceso': 'No se pueden agregar revisiones a un proceso finalizado.'
                })
        
        return attrs

    def get_auditor_nombre(self, obj):
        return _nombre_auditor(obj.auditor)

    def _is_proceso_finalizado(self, obj):
        return obj.proceso.estado == 'FINALIZADA'

    def _build_absolute_url(self, url):
        if not url:
            return None

        if not isinstance(url, str):
            return url

        # Decodifica rutas URL-encoded (%20, %C3%B3, etc.) para resolver archivos con caracteres especiales.
        decoded_url = urllib.parse.unquote(url).strip()
        if not decoded_url:
            return None

        if decoded_url.startswith(('http://', 'https://')):
            return decoded_url

        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(decoded_url)

        return decoded_url

    def _get_snapshot_evidencia_url(self, obj):
        """
        Obtiene la URL congelada de evidencia.
        Prioriza `evidencia_snapshot` (si existe) y usa `evidencias_snapshot`
        como fallback retrocompatible.
        Maneja JSON stringificado detectando y parseándolo.
        """
        evidencia_snapshot = getattr(obj, 'evidencia_snapshot', None)
        if evidencia_snapshot:
            return self._build_absolute_url(evidencia_snapshot)

        evidencias_snapshot = getattr(obj, 'evidencias_snapshot', None)
        if not evidencias_snapshot:
            return None

        # Si es string que parece JSON, parsearlo
        if isinstance(evidencias_snapshot, str):
            try:
                evidencias_snapshot = json.loads(evidencias_snapshot)
            except (json.JSONDecodeError, TypeError):
                # Si falla, asumir que es una URL directa
                return self._build_absolute_url(evidencias_snapshot)

        # Ahora trabajar con dict o list
        if isinstance(evidencias_snapshot, dict):
            return self._build_absolute_url(evidencias_snapshot.get('archivo'))

        if isinstance(evidencias_snapshot, list) and evidencias_snapshot:
            primera_evidencia = evidencias_snapshot[0]
            if isinstance(primera_evidencia, dict):
                return self._build_absolute_url(primera_evidencia.get('archivo'))
            if isinstance(primera_evidencia, str):
                return self._build_absolute_url(primera_evidencia)

        return None

    def get_estado(self, obj):
        """
        Prioriza siempre el snapshot de estado si existe.
        Si no hay snapshot, usa estado en vivo como fallback seguro.
        """
        if obj.estado_implementacion_snapshot not in (None, ''):
            return obj.estado_implementacion_snapshot

        if not obj.evaluacion_control:
            return None

        return obj.evaluacion_control.estado

    def get_justificacion(self, obj):
        """
        Prioriza siempre el snapshot de justificación si existe.
        Si no hay snapshot, usa justificación en vivo como fallback seguro.
        """
        if obj.justificacion_snapshot not in (None, ''):
            return obj.justificacion_snapshot

        if not obj.evaluacion_control:
            return None

        return obj.evaluacion_control.justificacion
    
    def get_es_historico(self, obj):
        """
        Indica si los datos devueltos son históricos (snapshot) o en vivo.
        True = datos congelados (auditoría FINALIZADA)
        False = datos en vivo (auditoría ACTIVA)
        """
        return self._is_proceso_finalizado(obj)
    
    def get_evidencia(self, obj):
        """
        Prioriza siempre la URL de evidencia congelada en snapshot.
        Si no hay snapshot, usa evidencia en vivo como fallback seguro.
        """
        evidencia_snapshot_url = self._get_snapshot_evidencia_url(obj)
        if evidencia_snapshot_url is not None:
            return evidencia_snapshot_url

        if not obj.evaluacion_control:
            return None

        primera_evidencia = (
            obj.evaluacion_control.evidencias
            .order_by('fecha_subida', 'id')
            .first()
        )
        if not primera_evidencia or not primera_evidencia.archivo:
            return None

        return self._build_absolute_url(primera_evidencia.archivo.url)


class ProcesoAuditoriaDetalleSerializer(serializers.ModelSerializer):
    """
    Serializer extendido para vista detallada de un proceso.
    Incluye todas las revisiones anidadas.
    """
    auditor_nombre = serializers.SerializerMethodField()
    empresa_nombre = serializers.CharField(
        source='empresa.nombre',
        read_only=True
    )
    total_controles = serializers.SerializerMethodField()
    controles_auditados = serializers.SerializerMethodField()
    progreso_porcentaje = serializers.SerializerMethodField()
    puede_finalizar = serializers.SerializerMethodField()
    revisiones = RevisionAuditoriaSerializer(many=True, read_only=True)
    
    # Métricas por veredicto
    total_conformes = serializers.SerializerMethodField()
    total_no_conformes = serializers.SerializerMethodField()
    total_no_aplica = serializers.SerializerMethodField()
    
    class Meta:
        model = ProcesoAuditoria
        fields = [
            'id',
            'nombre',
            'empresa',
            'empresa_nombre',
            'auditor',
            'auditor_nombre',
            'fecha_creacion',
            'fecha_cierre',
            'estado',
            'total_controles',
            'controles_auditados',
            'progreso_porcentaje',
            'puede_finalizar',
            'total_conformes',
            'total_no_conformes',
            'total_no_aplica',
            'revisiones'
        ]
        read_only_fields = ['id', 'fecha_creacion', 'fecha_cierre', 'auditor']
    
    def get_total_controles(self, obj):
        """
        Retorna el total de controles ISO disponibles en el sistema.
        """
        from implementacion.models import ControlISO

        return ControlISO.objects.count()

    def get_auditor_nombre(self, obj):
        return _nombre_auditor(obj.auditor)
    
    def get_controles_auditados(self, obj):
        """
        Retorna cuántas revisiones se han realizado en este proceso.
        """
        return obj.revisiones.count()
    
    def get_progreso_porcentaje(self, obj):
        """
        Cálculo seguro del porcentaje de progreso.
        """
        total = self.get_total_controles(obj)
        if total == 0:
            return 0
        
        auditados = self.get_controles_auditados(obj)
        return int((auditados / total) * 100)
    
    def get_puede_finalizar(self, obj):
        puede, mensaje = obj.puede_finalizar()
        return {'puede': puede, 'mensaje': mensaje}
    
    def get_total_conformes(self, obj):
        """Cuenta revisiones con veredicto CONFORME"""
        return obj.revisiones.filter(veredicto='CONFORME').count()
    
    def get_total_no_conformes(self, obj):
        """Cuenta revisiones con veredicto NO_CONFORME"""
        return obj.revisiones.filter(veredicto='NO_CONFORME').count()
    
    def get_total_no_aplica(self, obj):
        """Cuenta revisiones con veredicto NO_APLICA"""
        return obj.revisiones.filter(veredicto='NO_APLICA').count()
