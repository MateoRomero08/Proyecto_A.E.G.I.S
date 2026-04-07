from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db import transaction
from usuarios.permissions import IsApprovedUser

from implementacion.models import EvaluacionControl
from implementacion.serializers import EvaluacionControlSerializer
from .models import RevisionAuditoria, ProcesoAuditoria
from .serializers import (
    RevisionAuditoriaSerializer,
    ProcesoAuditoriaSerializer,
    ProcesoAuditoriaDetalleSerializer
)


def _nombre_auditor_asignado(proceso):
    if not proceso.auditor:
        return 'Sin auditor asignado'
    return proceso.auditor.get_full_name() or proceso.auditor.username


class ProcesoAuditoriaViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión de Procesos de Auditoría.
    Implementa RBAC estricto y acciones personalizadas.
    
    Permisos:
    - Auditor: Solo ve procesos donde él es el auditor
    - Superusuario: No accede a datos de negocio (aislamiento estricto)
    """
    permission_classes = [IsAuthenticated, IsApprovedUser]
    serializer_class = ProcesoAuditoriaSerializer
    
    def get_queryset(self):
        """
        Filtrado de datos basado en RBAC.
        Implementa aislamiento multi-tenant para auditores.
        """
        user = self.request.user
        
        # Superusuario: Sin acceso a datos de negocio
        if user.is_superuser:
            return ProcesoAuditoria.objects.none()
        
        # Auditor: Solo sus procesos asignados
        if hasattr(user, 'rol') and user.rol in ['AUDITOR', 'AUDITOR_INTERNO']:
            return ProcesoAuditoria.objects.filter(
                auditor=user,
                visible_para_auditor=True
            ).select_related('empresa', 'auditor').prefetch_related('revisiones')
        
        # Implementador u otro rol: Sin acceso
        return ProcesoAuditoria.objects.none()
    
    def get_serializer_class(self):
        """
        Usa serializer detallado para vistas de detalle.
        """
        if self.action == 'retrieve':
            return ProcesoAuditoriaDetalleSerializer
        return ProcesoAuditoriaSerializer
    
    def perform_create(self, serializer):
        """
        Asigna automáticamente el auditor al crear un proceso.
        Validación RBAC: Solo auditores pueden crear procesos.
        """
        user = self.request.user
        
        # Validar que sea auditor
        if not hasattr(user, 'rol') or user.rol not in ['AUDITOR', 'AUDITOR_INTERNO']:
            raise PermissionDenied(
                'Solo los auditores pueden crear procesos de auditoría.'
            )
        
        # Asignar auditor automáticamente
        serializer.save(auditor=user)

    def _get_proceso_para_visibilidad(self, pk, user):
        """
        Recupera procesos para acciones de archivar/restaurar,
        incluyendo registros ocultos para el auditor dueño.
        """
        if user.is_superuser:
            raise PermissionDenied('Los superusuarios no acceden a datos de negocio de auditoría.')

        return get_object_or_404(ProcesoAuditoria, pk=pk, auditor=user)
    
    @action(detail=True, methods=['post'], url_path='finalizar')
    def finalizar(self, request, pk=None):
        """
        Acción personalizada para finalizar un proceso de auditoría.
        
        Validaciones:
        1. El proceso debe estar en estado ACTIVA
        2. El progreso debe ser 100% (todos los controles auditados)
        3. Solo el auditor asignado puede finalizar
        
        Efectos:
        - Cambia estado a FINALIZADA
        - Registra fecha_cierre
        - Bloquea futuras modificaciones de revisiones
        """
        proceso = self.get_object()
        user = request.user
        
        # Validación RBAC: Solo el auditor asignado
        if proceso.auditor != user:
            auditor_asignado = _nombre_auditor_asignado(proceso)
            raise PermissionDenied(
                f'Solo el auditor asignado ({auditor_asignado}) '
                'puede finalizar este proceso.'
            )
        
        # Verificar si puede finalizar
        puede, mensaje = proceso.puede_finalizar()
        
        if not puede:
            return Response(
                {
                    'error': mensaje,
                    'progreso_actual': proceso.progreso_porcentaje(),
                    'controles_auditados': proceso.controles_auditados(),
                    'total_controles': proceso.total_controles_empresa()
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Finalizar proceso
        # NOTA: El modelo ProcesoAuditoria.save() se encarga automáticamente de:
        # 1. Congelar snapshots de todas las revisiones
        # 2. Establecer fecha_cierre
        # Solo necesitamos cambiar el estado aquí
        with transaction.atomic():
            proceso.estado = 'FINALIZADA'
            proceso.save()  # Los snapshots se congelan automáticamente en el modelo
        
        serializer = self.get_serializer(proceso)
        
        return Response(
            {
                'mensaje': f'Proceso "{proceso.nombre}" finalizado exitosamente',
                'data': serializer.data
            },
            status=status.HTTP_200_OK
        )
    
    @action(detail=True, methods=['post'], url_path='reabrir')
    def reabrir(self, request, pk=None):
        """
        Acción personalizada para reabrir un proceso finalizado.
        Solo el auditor asignado puede reabrir su proceso.
        """
        proceso = self.get_object()
        user = request.user
        
        if proceso.auditor != user:
            raise PermissionDenied('Solo el auditor asignado puede reabrir este proceso.')
        
        if proceso.estado != 'FINALIZADA':
            return Response(
                {'error': 'El proceso no está finalizado.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Reabrir proceso
        with transaction.atomic():
            proceso.estado = 'ACTIVA'
            proceso.fecha_cierre = None
            proceso.save()
        
        serializer = self.get_serializer(proceso)
        
        return Response(
            {
                'mensaje': f'Proceso "{proceso.nombre}" reabierto exitosamente',
                'data': serializer.data
            },
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['post'], url_path='archivar')
    def archivar(self, request, pk=None):
        """
        Oculta el proceso del panel del auditor sin eliminarlo de la base de datos.
        """
        proceso = self._get_proceso_para_visibilidad(pk, request.user)
        user = request.user

        if proceso.auditor != user:
            raise PermissionDenied(
                'Solo el auditor asignado puede archivar este proceso.'
            )

        proceso.visible_para_auditor = False
        proceso.save(update_fields=['visible_para_auditor'])

        return Response(
            {'mensaje': f'Proceso "{proceso.nombre}" archivado correctamente.'},
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['post'], url_path='restaurar')
    def restaurar(self, request, pk=None):
        """
        Restaura un proceso archivado para volver a mostrarlo al auditor.
        """
        proceso = self._get_proceso_para_visibilidad(pk, request.user)

        if proceso.visible_para_auditor:
            return Response(
                {'mensaje': f'Proceso "{proceso.nombre}" ya está visible.'},
                status=status.HTTP_200_OK
            )

        proceso.visible_para_auditor = True
        proceso.save(update_fields=['visible_para_auditor'])

        return Response(
            {'mensaje': f'Proceso "{proceso.nombre}" restaurado correctamente.'},
            status=status.HTTP_200_OK
        )

    @action(detail=False, methods=['get'], url_path='archivados')
    def archivados(self, request):
        """
        Lista los procesos archivados (ocultos) que el usuario puede restaurar.
        """
        user = request.user

        if user.is_superuser:
            queryset = ProcesoAuditoria.objects.none()
        elif hasattr(user, 'rol') and user.rol in ['AUDITOR', 'AUDITOR_INTERNO']:
            queryset = ProcesoAuditoria.objects.filter(
                auditor=user,
                visible_para_auditor=False
            ).select_related('empresa', 'auditor').prefetch_related('revisiones')
        else:
            queryset = ProcesoAuditoria.objects.none()

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['get'], url_path='estadisticas')
    def estadisticas(self, request, pk=None):
        """
        Retorna estadísticas detalladas del proceso de auditoría.
        """
        proceso = self.get_object()
        
        total_revisiones = proceso.revisiones.count()
        
        estadisticas = {
            'proceso_id': proceso.id,
            'proceso_nombre': proceso.nombre,
            'estado': proceso.estado,
            'progreso_porcentaje': proceso.progreso_porcentaje(),
            'metricas': {
                'total_controles': proceso.total_controles_empresa(),
                'controles_auditados': total_revisiones,
                'controles_pendientes': proceso.total_controles_empresa() - total_revisiones,
            },
            'veredictos': {
                'conforme': proceso.revisiones.filter(veredicto='CONFORME').count(),
                'no_conforme': proceso.revisiones.filter(veredicto='NO_CONFORME').count(),
                'no_aplica': proceso.revisiones.filter(veredicto='NO_APLICA').count(),
            },
            'fechas': {
                'creacion': proceso.fecha_creacion,
                'cierre': proceso.fecha_cierre,
            }
        }
        
        return Response(estadisticas, status=status.HTTP_200_OK)


class RevisionAuditoriaViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión de Revisiones de Auditoría.
    Implementa bloqueo de auditorías finalizadas.
    """
    permission_classes = [IsAuthenticated, IsApprovedUser]
    serializer_class = RevisionAuditoriaSerializer
    
    def get_queryset(self):
        """
        Filtrado basado en permisos del usuario.
        Soporta filtro por proceso mediante query parameter ?proceso=<id>
        """
        user = self.request.user
        
        # Superusuario: Sin acceso a datos de negocio
        if user.is_superuser:
            queryset = RevisionAuditoria.objects.none()
        # Auditor: Solo revisiones de sus procesos
        elif hasattr(user, 'rol') and user.rol in ['AUDITOR', 'AUDITOR_INTERNO']:
            queryset = RevisionAuditoria.objects.filter(
                proceso__auditor=user
            ).select_related(
                'proceso', 'evaluacion_control', 'auditor',
                'evaluacion_control__control', 'evaluacion_control__empresa'
            )
        else:
            # Otros: Sin acceso
            queryset = RevisionAuditoria.objects.none()
        
        # Filtrar por proceso si se proporciona el parámetro
        proceso_id = self.request.query_params.get('proceso', None)
        if proceso_id:
            queryset = queryset.filter(proceso_id=proceso_id)
        
        return queryset

    def create(self, request, *args, **kwargs):
        """
        Crea o actualiza una revisión por (proceso, evaluacion_control).
        Evita duplicados y permite edición desde el mismo endpoint POST.
        """
        proceso_id = request.data.get('proceso')
        evaluacion_control_id = request.data.get('evaluacion_control')

        revision_existente = None
        if proceso_id and evaluacion_control_id:
            revision_existente = RevisionAuditoria.objects.filter(
                proceso_id=proceso_id,
                evaluacion_control_id=evaluacion_control_id
            ).first()

        serializer = self.get_serializer(revision_existente, data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        status_code = status.HTTP_200_OK if revision_existente else status.HTTP_201_CREATED
        headers = self.get_success_headers(serializer.data) if status_code == status.HTTP_201_CREATED else {}
        return Response(serializer.data, status=status_code, headers=headers)
    
    def perform_create(self, serializer):
        """
        Crea o actualiza una revisión usando update_or_create.
        Esto permite al auditor corregir sus comentarios o veredictos sin crear duplicados.
        VALIDACIÓN CRÍTICA: Bloqueo de procesos finalizados.
        """
        user = self.request.user
        proceso = serializer.validated_data.get('proceso')
        evaluacion_control = serializer.validated_data.get('evaluacion_control')

        # Fallback defensivo para updates donde la instancia ya existe
        if evaluacion_control is None and serializer.instance is not None:
            evaluacion_control = serializer.instance.evaluacion_control

        if proceso is None:
            raise ValidationError('Debe indicar el proceso de auditoría.')

        if evaluacion_control is None:
            raise ValidationError({'evaluacion_control': 'This field cannot be null.'})
        
        # BLOQUEO: No permitir revisiones en procesos finalizados
        if proceso.estado == 'FINALIZADA':
            raise ValidationError(
                'Esta auditoría está cerrada y es de solo lectura. '
                'No se pueden agregar revisiones a procesos finalizados.'
            )
        
        # Validar RBAC: Solo auditores
        if not hasattr(user, 'rol') or user.rol not in ['AUDITOR', 'AUDITOR_INTERNO']:
            raise PermissionDenied(
                'Solo los auditores pueden crear revisiones.'
            )
        
        # Validar que el auditor coincide con el del proceso
        if not proceso.auditor:
            raise ValidationError(
                'El proceso no tiene auditor asignado. Reasigne un auditor antes de registrar revisiones.'
            )

        if proceso.auditor != user:
            auditor_asignado = _nombre_auditor_asignado(proceso)
            raise PermissionDenied(
                f'Solo el auditor asignado ({auditor_asignado}) '
                'puede crear revisiones en este proceso.'
            )

        # Captura robusta de evidencia snapshot desde la evaluación
        primera_evidencia = (
            evaluacion_control.evidencias
            .order_by('fecha_subida', 'id')
            .first()
        )

        evidencia_data = None
        if primera_evidencia and primera_evidencia.archivo:
            evidencia_data = [
                {
                    'id': primera_evidencia.id,
                    'archivo': primera_evidencia.archivo.url,
                    'archivo_nombre': primera_evidencia.archivo.name.split('/')[-1],
                    'fecha_subida': (
                        primera_evidencia.fecha_subida.isoformat()
                        if primera_evidencia.fecha_subida
                        else None
                    )
                }
            ]

        # Permite compatibilidad si el campo cambia de nombre en el modelo.
        snapshot_fields = {field.name for field in RevisionAuditoria._meta.get_fields()}
        evidencia_snapshot_kwargs = {}
        if 'evidencia_snapshot' in snapshot_fields:
            evidencia_snapshot_kwargs['evidencia_snapshot'] = evidencia_data
        if 'evidencias_snapshot' in snapshot_fields:
            evidencia_snapshot_kwargs['evidencias_snapshot'] = evidencia_data

        nombre_implementador = evaluacion_control.usuario.get_full_name() or evaluacion_control.usuario.username if evaluacion_control and evaluacion_control.usuario else 'Sin asignar'
        
        defaults = {
            'auditor': user,
            'veredicto': serializer.validated_data.get('veredicto'),
            'observaciones': serializer.validated_data.get('observaciones'),
            'estado_implementacion_snapshot': evaluacion_control.estado if evaluacion_control else 'N/A',
            'justificacion_snapshot': evaluacion_control.justificacion if evaluacion_control else '',
            'implementador_snapshot': nombre_implementador,
            **evidencia_snapshot_kwargs,
        }

        revision, created = RevisionAuditoria.objects.get_or_create(
            proceso=proceso,
            evaluacion_control=evaluacion_control,
            defaults=defaults
        )

        if not created:
            # Permite editar veredicto/observaciones sin alterar snapshots ya capturados.
            revision.auditor = user
            revision.veredicto = serializer.validated_data.get('veredicto', revision.veredicto)
            revision.observaciones = serializer.validated_data.get('observaciones', revision.observaciones)

            if not revision.estado_implementacion_snapshot:
                revision.estado_implementacion_snapshot = evaluacion_control.estado if evaluacion_control else 'N/A'
            if revision.justificacion_snapshot is None:
                revision.justificacion_snapshot = evaluacion_control.justificacion if evaluacion_control else ''
            if not revision.implementador_snapshot:
                revision.implementador_snapshot = nombre_implementador

            if evidencia_data:
                if hasattr(revision, 'evidencia_snapshot') and not getattr(revision, 'evidencia_snapshot'):
                    revision.evidencia_snapshot = evidencia_data
                if hasattr(revision, 'evidencias_snapshot') and not revision.evidencias_snapshot:
                    revision.evidencias_snapshot = evidencia_data

            update_fields = [
                'auditor',
                'veredicto',
                'observaciones',
                'estado_implementacion_snapshot',
                'justificacion_snapshot',
                'implementador_snapshot',
                'fecha_actualizacion',
            ]
            if hasattr(revision, 'evidencia_snapshot'):
                update_fields.append('evidencia_snapshot')
            if hasattr(revision, 'evidencias_snapshot'):
                update_fields.append('evidencias_snapshot')

            revision.save(
                update_fields=update_fields
            )
        
        # Actualizar el serializer con la instancia creada/actualizada
        serializer.instance = revision
    
    def perform_update(self, serializer):
        """
        Actualiza una revisión.
        VALIDACIÓN CRÍTICA: Bloqueo de procesos finalizados.
        """
        user = self.request.user
        revision = self.get_object()
        
        # BLOQUEO: No permitir modificaciones en procesos finalizados
        if revision.proceso.estado == 'FINALIZADA':
            raise ValidationError(
                'Esta auditoría está cerrada y es de solo lectura. '
                'No se pueden modificar revisiones en procesos finalizados.'
            )
        
        # Validar RBAC
        if revision.auditor != user:
            raise PermissionDenied(
                'Solo el auditor que creó esta revisión puede modificarla.'
            )

        serializer.save()
    
    def perform_destroy(self, instance):
        """
        Elimina una revisión.
        VALIDACIÓN CRÍTICA: Bloqueo de procesos finalizados.
        """
        user = self.request.user
        
        # BLOQUEO: No permitir eliminaciones en procesos finalizados
        if instance.proceso.estado == 'FINALIZADA':
            raise ValidationError(
                'Esta auditoría está cerrada y es de solo lectura. '
                'No se pueden eliminar revisiones en procesos finalizados.'
            )
        
        if instance.auditor != user:
            raise PermissionDenied(
                'Solo el auditor asignado puede eliminar revisiones activas.'
            )
        
        instance.delete()


class ListarEvaluacionesAuditoriaView(APIView):
    """
    Vista para listar evaluaciones disponibles para auditoría.
    Implementa acceso diferenciado para superusuarios y auditores.
    """
    permission_classes = [IsAuthenticated, IsApprovedUser]
    
    def get(self, request):
        """
        Lista evaluaciones según el tipo de usuario.
        """
        user = request.user

        # Superusuario: sin acceso a datos de negocio de auditoría.
        if user.is_superuser:
            raise PermissionDenied(
                'Los superusuarios no acceden a evaluaciones de auditoría por aislamiento multi-tenant.'
            )
        
        # Validar que sea auditor
        if not hasattr(user, 'rol') or user.rol not in ['AUDITOR', 'AUDITOR_INTERNO']:
            raise PermissionDenied(
                'Solo los auditores pueden acceder a esta vista.'
            )
        
        # Validar que tenga empresa asignada
        if not user.empresa:
            return Response(
                {'error': 'El usuario no tiene una empresa asignada.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Auditor: Solo evaluaciones de su empresa
        evaluaciones = EvaluacionControl.objects.filter(
            empresa=user.empresa
        ).select_related('empresa', 'control')
        
        serializer = EvaluacionControlSerializer(evaluaciones, many=True)
        
        return Response({
            'count': evaluaciones.count(),
            'tipo_acceso': 'auditor',
            'empresa': user.empresa.nombre,
            'results': serializer.data
        }, status=status.HTTP_200_OK)
