from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError, PermissionDenied
from rest_framework.decorators import action
from django.db import transaction
from django.contrib.auth import get_user_model
from django.utils import timezone
from usuarios.permissions import IsApprovedUser, es_acceso_global
from usuarios.models import Notificacion
from .models import Empresa, ControlISO, EvaluacionControl, Evidencia
from .serializers import (
    EmpresaSerializer, 
    ControlISOSerializer, 
    EvaluacionControlSerializer, 
    EvidenciaSerializer
)

User = get_user_model()


class EmpresaViewSet(viewsets.ModelViewSet):
    serializer_class = EmpresaSerializer
    permission_classes = [IsAuthenticated, IsApprovedUser]

    def get_queryset(self):
        user = self.request.user

        if es_acceso_global(user):
            return Empresa.objects.all().order_by('nombre')

        if user.empresa_id:
            return Empresa.objects.filter(id=user.empresa_id)

        return Empresa.objects.none()


class ControlISOViewSet(viewsets.ModelViewSet):
    serializer_class = ControlISOSerializer
    permission_classes = [IsAuthenticated, IsApprovedUser]
    filterset_fields = ['dominio', 'identificador']
    search_fields = ['identificador', 'nombre', 'descripcion_guia']
    ordering_fields = ['identificador', 'nombre', 'dominio']
    ordering = ['identificador']

    def get_queryset(self):
        user = self.request.user

        if es_acceso_global(user):
            return ControlISO.objects.all()

        if not user.empresa_id:
            return ControlISO.objects.none()

        # Catalogo normativo global compartido entre tenants.
        return ControlISO.objects.all()


class EvaluacionControlViewSet(viewsets.ModelViewSet):
    queryset = EvaluacionControl.objects.all().select_related('empresa', 'control', 'usuario')
    serializer_class = EvaluacionControlSerializer
    permission_classes = [IsAuthenticated, IsApprovedUser]
    filterset_fields = ['empresa', 'control', 'estado']
    search_fields = ['control__nombre', 'justificacion']
    ordering_fields = ['id', 'estado']

    def _validar_empresa_usuario(self, empresa):
        user = self.request.user

        if es_acceso_global(user):
            return

        if not user.empresa_id:
            raise PermissionDenied('Tu usuario no tiene una empresa asociada.')

        if empresa.id != user.empresa_id:
            raise PermissionDenied('No puedes operar evaluaciones de otra empresa.')

    def _invalidar_revision_empresa_si_corresponde(self, empresa):
        """
        Si la empresa ya había solicitado revisión, cualquier cambio posterior
        en controles invalida ese hito y exige una nueva solicitud.
        """
        if empresa and empresa.revision_solicitada:
            empresa.revision_solicitada = False
            empresa.fecha_solicitud_revision = None
            empresa.save(update_fields=['revision_solicitada', 'fecha_solicitud_revision'])
    
    def verificar_permisos_auditor(self, request):
        """
        Escudo de Segregación de Funciones (RBAC).
        
        Bloquea a los auditores de modificar implementaciones,
        garantizando separación de responsabilidades:
        - Auditores: Solo lectura y auditoría
        - Implementadores: Modificación de controles
        """
        user = request.user
        
        # Verificar si el usuario tiene rol de auditor
        if hasattr(user, 'rol') and user.rol in ['AUDITOR', 'AUDITOR_INTERNO']:
            raise PermissionDenied(
                'Segregación de funciones: Los auditores no pueden modificar implementaciones.'
            )
    
    def get_queryset(self):
        """
        Aislamiento de datos estricto Multi-Tenant.
        
        Garantiza que cada tenant solo acceda a sus propios datos,
        previniendo fugas de información entre organizaciones.
        """
        # 1. Obtener usuario de la request
        user = self.request.user
        
        # 2. Caso 1: Acceso global
        if es_acceso_global(user):
            return EvaluacionControl.objects.all().select_related('empresa', 'control', 'usuario')
        
        # 3. Caso 2: Tenant aislado - Solo sus datos
        if user.empresa:
            return EvaluacionControl.objects.filter(
                empresa=user.empresa
            ).select_related('empresa', 'control', 'usuario')
        
        # 4. Caso 3: Usuario huérfano - Sin acceso (seguridad)
        return EvaluacionControl.objects.none()

    def perform_create(self, serializer):
        """Asigna el usuario actual como implementador al crear una evaluación."""
        user = self.request.user
        serializer.save(usuario=user if user.is_authenticated else None)

    def create(self, request, *args, **kwargs):
        """
        Crea o actualiza una evaluación por empresa + código de control.
        Evita borrados/duplicados y mantiene integridad con auditoría.
        """
        # ESCUDO DE SEGURIDAD: Verificar segregación de funciones
        self.verificar_permisos_auditor(request)
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        validated_data = dict(serializer.validated_data)
        evidencia_file = validated_data.pop('evidencia', None)

        empresa = validated_data['empresa']
        control = validated_data['control']

        self._validar_empresa_usuario(empresa)

        user = request.user
        usuario_actual = user if getattr(user, 'is_authenticated', False) else None

        defaults = {
            'empresa': empresa,
            'control': control,
            'estado': validated_data.get('estado', 'NO_IMPLEMENTADO'),
            'justificacion': validated_data.get('justificacion'),
            'usuario': usuario_actual,
        }

        with transaction.atomic():
            evaluacion, created = EvaluacionControl.objects.update_or_create(
                empresa_id=empresa.id,
                control__identificador=control.identificador,
                defaults=defaults
            )

            # Si NO_APLICA, no conservar evidencia. Si IMPLEMENTADO y llega archivo, actualizar/crear.
            if evaluacion.estado != 'NO_APLICA' and evidencia_file:
                evidencia_existente = evaluacion.evidencias.first()
                if evidencia_existente:
                    evidencia_existente.archivo = evidencia_file
                    evidencia_existente.save(update_fields=['archivo'])
                else:
                    Evidencia.objects.create(
                        evaluacion=evaluacion,
                        archivo=evidencia_file
                    )

            self._invalidar_revision_empresa_si_corresponde(empresa)

        output_serializer = self.get_serializer(evaluacion)
        response_status = status.HTTP_201_CREATED if created else status.HTTP_200_OK
        return Response(output_serializer.data, status=response_status)

    def partial_update(self, request, *args, **kwargs):
        # ESCUDO DE SEGURIDAD: Verificar segregación de funciones
        self.verificar_permisos_auditor(request)
        
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        """
        Actualiza una evaluación existente por ID sin borrar registros.
        Preserva integridad referencial con auditoría.
        """
        # ESCUDO DE SEGURIDAD: Verificar segregación de funciones
        self.verificar_permisos_auditor(request)
        
        partial = kwargs.pop('partial', False)
        instance = self.get_object()

        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)

        validated_data = dict(serializer.validated_data)
        evidencia_file = validated_data.pop('evidencia', None)

        with transaction.atomic():
            if instance.empresa_id != request.user.empresa_id:
                raise PermissionDenied('No puedes modificar evaluaciones de otra empresa.')

            if 'estado' in validated_data:
                instance.estado = validated_data['estado']
            if 'justificacion' in validated_data:
                instance.justificacion = validated_data['justificacion']

            user = request.user
            if getattr(user, 'is_authenticated', False):
                instance.usuario = user

            instance.save()

            if instance.estado != 'NO_APLICA' and evidencia_file:
                evidencia_existente = instance.evidencias.first()
                if evidencia_existente:
                    evidencia_existente.archivo = evidencia_file
                    evidencia_existente.save(update_fields=['archivo'])
                else:
                    Evidencia.objects.create(
                        evaluacion=instance,
                        archivo=evidencia_file
                    )

            self._invalidar_revision_empresa_si_corresponde(instance.empresa)

        output_serializer = self.get_serializer(instance)
        return Response(output_serializer.data, status=status.HTTP_200_OK)

    def perform_destroy(self, instance):
        # Bloquea eliminación si existe cualquier revisión vinculada para preservar historial de auditoría.
        if instance.revisiones_auditoria.exists():
            raise ValidationError(
                'No se puede eliminar esta evaluación porque tiene revisiones de auditoría asociadas.'
            )

        instance.delete()

    @action(detail=False, methods=['post'], url_path='solicitar-revision')
    def solicitar_revision(self, request):
        """
        Marca el hito de implementación completa y notifica a auditores del mismo tenant.
        """
        user = request.user

        if user.is_superuser:
            raise PermissionDenied('Los superusuarios no operan datos de implementación por aislamiento multi-tenant.')

        if not user.empresa_id:
            raise PermissionDenied('Tu usuario no tiene una empresa asociada.')

        if getattr(user, 'rol', None) != 'IMPLEMENTADOR':
            raise PermissionDenied('Solo un implementador puede solicitar revisión de implementación.')

        empresa = user.empresa
        if not empresa:
            raise PermissionDenied('Tu usuario no tiene una empresa asociada.')

        total_controles = ControlISO.objects.count()
        total_completados = EvaluacionControl.objects.filter(
            empresa_id=user.empresa_id,
            estado__in=['IMPLEMENTADO', 'NO_APLICA'],
        ).count()

        if total_controles == 0:
            raise ValidationError('No existen controles configurados para evaluar.')

        progreso = int((total_completados / total_controles) * 100)
        if total_completados < total_controles:
            raise ValidationError(
                {
                    'detail': 'Debes completar el 100% de controles antes de solicitar revisión.',
                    'progreso': progreso,
                    'evaluados': total_completados,
                    'controles_completados': total_completados,
                    'total_controles': total_controles,
                }
            )

        if empresa.revision_solicitada:
            return Response(
                {
                    'detail': 'La solicitud de revisión ya fue enviada previamente.',
                    'progreso': progreso,
                    'notificaciones_creadas': 0,
                    'revision_solicitada': True,
                    'fecha_solicitud_revision': empresa.fecha_solicitud_revision,
                },
                status=status.HTTP_200_OK,
            )

        auditores = User.objects.filter(
            empresa_id=user.empresa_id,
            rol__in=['AUDITOR', 'AUDITOR_INTERNO'],
            is_active=True,
            is_approved=True,
        ).exclude(id=user.id)

        nombre_implementador = user.get_full_name() or user.username
        nombre_empresa = user.empresa.nombre if user.empresa else 'tu empresa'
        titulo = 'Implementación Lista para Revisión'
        mensaje = (
            f'{nombre_implementador} ha completado el 100% de la implementación ISO 27001 '
            f'en {nombre_empresa}. Hay una revisión pendiente.'
        )

        with transaction.atomic():
            notificaciones = [
                Notificacion(
                    usuario_destino=auditor,
                    titulo=titulo,
                    mensaje=mensaje,
                )
                for auditor in auditores
            ]
            Notificacion.objects.bulk_create(notificaciones)

            empresa.revision_solicitada = True
            empresa.fecha_solicitud_revision = timezone.now()
            empresa.save(update_fields=['revision_solicitada', 'fecha_solicitud_revision'])

        return Response(
            {
                'detail': 'Solicitud de revisión enviada a los auditores exitosamente.',
                'progreso': progreso,
                'notificaciones_creadas': len(notificaciones),
                'revision_solicitada': empresa.revision_solicitada,
                'fecha_solicitud_revision': empresa.fecha_solicitud_revision,
            },
            status=status.HTTP_200_OK,
        )

    @action(detail=False, methods=['get'], url_path='estado-solicitud-revision')
    def estado_solicitud_revision(self, request):
        """
        Retorna el estado persistido de la solicitud de revisión de implementación.
        """
        user = request.user

        if user.is_superuser:
            raise PermissionDenied('Los superusuarios no operan datos de implementación por aislamiento multi-tenant.')

        if not user.empresa:
            raise PermissionDenied('Tu usuario no tiene una empresa asociada.')

        return Response(
            {
                'empresa_id': user.empresa_id,
                'revision_solicitada': bool(user.empresa.revision_solicitada),
                'fecha_solicitud_revision': user.empresa.fecha_solicitud_revision,
            },
            status=status.HTTP_200_OK,
        )


class EvidenciaViewSet(viewsets.ModelViewSet):
    serializer_class = EvidenciaSerializer
    permission_classes = [IsAuthenticated, IsApprovedUser]
    filterset_fields = ['evaluacion']
    ordering_fields = ['fecha_subida']
    ordering = ['-fecha_subida']

    def get_queryset(self):
        user = self.request.user

        if es_acceso_global(user):
            return Evidencia.objects.all().select_related('evaluacion')

        if user.empresa_id:
            return Evidencia.objects.filter(
                evaluacion__empresa_id=user.empresa_id
            ).select_related('evaluacion')

        return Evidencia.objects.none()

