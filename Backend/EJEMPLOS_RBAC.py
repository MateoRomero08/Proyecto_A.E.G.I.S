"""
EJEMPLOS DE INTEGRACIÓN RBAC
Cómo aplicar el sistema de permisos a las vistas de implementacion
"""

# ============================================================================
# EJEMPLO 1: Proteger vistas de evaluaciones con permisos RBAC
# ============================================================================

from rest_framework import generics, permissions, status
from rest_framework.response import Response
from usuarios.permissions import (
    EsImplementador,
    EsAuditor,
    PerteneceAMismaEmpresa,
    PuedeEditarEvaluaciones
)
from implementacion.models import EvaluacionControl
from implementacion.serializers import EvaluacionControlSerializer


# Vista para LISTAR evaluaciones (ambos roles)
class ListarEvaluacionesView(generics.ListAPIView):
    """
    Solo usuarios autenticados pueden listar evaluaciones de su empresa
    """
    serializer_class = EvaluacionControlSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        
        # Superusuarios ven todo
        if user.is_superuser:
            return EvaluacionControl.objects.all()
        
        # Usuarios con empresa solo ven de su empresa
        if user.empresa:
            return EvaluacionControl.objects.filter(empresa=user.empresa)
        
        # Sin empresa, no ve nada
        return EvaluacionControl.objects.none()


# Vista para CREAR evaluación (solo implementadores)
class CrearEvaluacionView(generics.CreateAPIView):
    """
    Solo implementadores pueden crear evaluaciones para su empresa
    """
    serializer_class = EvaluacionControlSerializer
    permission_classes = [permissions.IsAuthenticated, EsImplementador]
    
    def perform_create(self, serializer):
        # Forzar que la evaluación sea de la empresa del usuario
        serializer.save(empresa=self.request.user.empresa)


# Vista para EDITAR evaluación (solo implementadores de la misma empresa)
class EditarEvaluacionView(generics.UpdateAPIView):
    """
    Solo implementadores pueden editar evaluaciones de su propia empresa
    Auditores solo pueden ver (no editar)
    """
    serializer_class = EvaluacionControlSerializer
    permission_classes = [permissions.IsAuthenticated, PuedeEditarEvaluaciones]
    
    def get_queryset(self):
        user = self.request.user
        
        if user.is_superuser:
            return EvaluacionControl.objects.all()
        
        if user.empresa:
            return EvaluacionControl.objects.filter(empresa=user.empresa)
        
        return EvaluacionControl.objects.none()


# ============================================================================
# EJEMPLO 2: Vista mixta con lógica condicional por rol
# ============================================================================

from rest_framework.views import APIView

class DashboardEmpresaView(APIView):
    """
    Dashboard que muestra información diferente según el rol
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        user = request.user
        
        if not user.empresa:
            return Response({
                'error': 'Usuario sin empresa asignada'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Datos base para ambos roles
        data = {
            'empresa': user.empresa.nombre,
            'tipo_empresa': user.empresa.get_tipo_display(),
            'usuario': user.get_full_name() or user.username,
            'rol': user.get_rol_display(),
        }
        
        # Datos específicos según rol
        if user.es_implementador():
            # Implementadores ven estadísticas de implementación
            evaluaciones = EvaluacionControl.objects.filter(empresa=user.empresa)
            data.update({
                'total_controles': evaluaciones.count(),
                'implementados': evaluaciones.filter(estado='IMPLEMENTADO').count(),
                'pendientes': evaluaciones.filter(estado='NO_IMPLEMENTADO').count(),
                'no_aplica': evaluaciones.filter(estado='NO_APLICA').count(),
                'puede_editar': True,
            })
        
        elif user.es_auditor():
            # Auditores ven estadísticas de auditoría
            evaluaciones = EvaluacionControl.objects.filter(empresa=user.empresa)
            data.update({
                'total_evaluaciones': evaluaciones.count(),
                'para_auditar': evaluaciones.filter(estado='IMPLEMENTADO').count(),
                'puede_editar': False,
                'modo': 'solo_lectura',
            })
        
        return Response(data, status=status.HTTP_200_OK)


# ============================================================================
# EJEMPLO 3: Middleware personalizado para logging de acciones
# ============================================================================

from django.utils.deprecation import MiddlewareMixin
import logging

logger = logging.getLogger('usuarios')

class AuditMiddleware(MiddlewareMixin):
    """
    Middleware para auditar acciones de usuarios por rol
    """
    
    def process_request(self, request):
        if request.user.is_authenticated:
            # Log de acciones de usuarios autenticados
            logger.info(
                f"User: {request.user.username} | "
                f"Rol: {request.user.rol} | "
                f"Empresa: {request.user.empresa.nombre if request.user.empresa else 'N/A'} | "
                f"Method: {request.method} | "
                f"Path: {request.path}"
            )
        return None


# ============================================================================
# EJEMPLO 4: Decorador personalizado para verificar rol
# ============================================================================

from functools import wraps
from rest_framework.response import Response
from rest_framework import status

def solo_implementador(view_func):
    """
    Decorador que restringe el acceso solo a implementadores
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response({
                'error': 'Usuario no autenticado'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        if not request.user.es_implementador() and not request.user.is_superuser:
            return Response({
                'error': 'Solo implementadores tienen acceso a esta funcionalidad'
            }, status=status.HTTP_403_FORBIDDEN)
        
        return view_func(request, *args, **kwargs)
    
    return wrapper


def solo_auditor(view_func):
    """
    Decorador que restringe el acceso solo a auditores
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response({
                'error': 'Usuario no autenticado'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        if not request.user.es_auditor() and not request.user.is_superuser:
            return Response({
                'error': 'Solo auditores tienen acceso a esta funcionalidad'
            }, status=status.HTTP_403_FORBIDDEN)
        
        return view_func(request, *args, **kwargs)
    
    return wrapper


# Uso de decoradores
@solo_implementador
def funcion_solo_implementadores(request):
    return Response({'message': 'Solo implementadores pueden ver esto'})


# ============================================================================
# EJEMPLO 5: Filtros en el admin para separar por empresa
# ============================================================================

from django.contrib import admin
from implementacion.models import EvaluacionControl

class EvaluacionControlAdmin(admin.ModelAdmin):
    list_display = ('empresa', 'control', 'estado', 'fecha_creacion')
    list_filter = ('estado', 'empresa', 'control__dominio')
    search_fields = ('empresa__nombre', 'control__identificador', 'control__nombre')
    
    def get_queryset(self, request):
        """
        Los usuarios staff que no son superuser solo ven de su empresa
        """
        qs = super().get_queryset(request)
        
        if request.user.is_superuser:
            return qs
        
        if hasattr(request.user, 'empresa') and request.user.empresa:
            return qs.filter(empresa=request.user.empresa)
        
        return qs.none()
    
    def save_model(self, request, obj, form, change):
        """
        Auto-asignar empresa del usuario al crear evaluación
        """
        if not change and hasattr(request.user, 'empresa'):
            obj.empresa = request.user.empresa
        super().save_model(request, obj, form, change)


# ============================================================================
# EJEMPLO 6: Serializer con campos condicionales por rol
# ============================================================================

from rest_framework import serializers

class EvaluacionControlSerializer(serializers.ModelSerializer):
    puede_editar = serializers.SerializerMethodField()
    editado_por = serializers.SerializerMethodField()
    
    class Meta:
        model = EvaluacionControl
        fields = '__all__'
        read_only_fields = ['empresa']
    
    def get_puede_editar(self, obj):
        """
        Indica si el usuario actual puede editar esta evaluación
        """
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        
        user = request.user
        
        # Superusuarios pueden editar todo
        if user.is_superuser:
            return True
        
        # Auditores no pueden editar
        if user.es_auditor():
            return False
        
        # Implementadores solo de su empresa
        if user.es_implementador():
            return obj.empresa == user.empresa
        
        return False
    
    def get_editado_por(self, obj):
        """
        Información de quién editó por última vez
        """
        # Esto requeriría un campo adicional en el modelo
        # pero muestra cómo personalizar según el contexto
        request = self.context.get('request')
        if request and request.user.es_auditor():
            return "Información restringida para auditores"
        return obj.editado_por if hasattr(obj, 'editado_por') else None


# ============================================================================
# EJEMPLO 7: ViewSet completo con permisos granulares
# ============================================================================

from rest_framework import viewsets
from rest_framework.decorators import action

class EvaluacionControlViewSet(viewsets.ModelViewSet):
    """
    ViewSet completo con permisos diferenciados por acción
    """
    serializer_class = EvaluacionControlSerializer
    
    def get_permissions(self):
        """
        Permisos diferentes por acción
        """
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            # Solo implementadores pueden crear/editar/eliminar
            permission_classes = [permissions.IsAuthenticated, EsImplementador]
        elif self.action in ['list', 'retrieve']:
            # Todos los autenticados pueden ver
            permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = [permissions.IsAuthenticated]
        
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        """
        Filtrar por empresa del usuario
        """
        user = self.request.user
        
        if user.is_superuser:
            return EvaluacionControl.objects.all()
        
        if user.empresa:
            return EvaluacionControl.objects.filter(empresa=user.empresa)
        
        return EvaluacionControl.objects.none()
    
    def perform_create(self, serializer):
        """
        Auto-asignar empresa al crear
        """
        serializer.save(empresa=self.request.user.empresa)
    
    @action(detail=False, methods=['get'])
    def estadisticas(self, request):
        """
        Endpoint personalizado para estadísticas
        Accesible solo para implementadores
        """
        if not request.user.es_implementador() and not request.user.is_superuser:
            return Response({
                'error': 'Solo implementadores pueden ver estadísticas'
            }, status=status.HTTP_403_FORBIDDEN)
        
        evaluaciones = self.get_queryset()
        
        return Response({
            'total': evaluaciones.count(),
            'implementados': evaluaciones.filter(estado='IMPLEMENTADO').count(),
            'pendientes': evaluaciones.filter(estado='NO_IMPLEMENTADO').count(),
            'no_aplica': evaluaciones.filter(estado='NO_APLICA').count(),
        })
    
    @action(detail=True, methods=['post'])
    def auditar(self, request, pk=None):
        """
        Endpoint personalizado para auditar (solo auditores)
        """
        if not request.user.es_auditor() and not request.user.is_superuser:
            return Response({
                'error': 'Solo auditores pueden auditar evaluaciones'
            }, status=status.HTTP_403_FORBIDDEN)
        
        evaluacion = self.get_object()
        
        # Lógica de auditoría aquí
        # ...
        
        return Response({
            'message': f'Evaluación {evaluacion.id} auditada por {request.user.get_full_name()}'
        })


# ============================================================================
# CONFIGURAR EN implementacion/urls.py
# ============================================================================

"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import EvaluacionControlViewSet

router = DefaultRouter()
router.register(r'evaluaciones', EvaluacionControlViewSet, basename='evaluacion')

urlpatterns = [
    path('', include(router.urls)),
]
"""
