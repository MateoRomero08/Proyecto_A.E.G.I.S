from django.db import transaction
from django.db.models import Prefetch, Q
from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from usuarios.permissions import IsApprovedUser, es_acceso_global

from .models import CursoCapacitacion, ModuloContenido, ProgresoUsuario
from .serializers import (
    CursoCapacitacionSerializer,
    CursoCapacitacionWriteSerializer,
    ModuloContenidoSerializer,
    ProgresoUsuarioSerializer,
)


PERMISOS_CURSO_CREAR = ('capacitacion.add_curso', 'capacitacion.add_cursocapacitacion')
PERMISOS_CURSO_GESTION = ('capacitacion.change_curso', 'capacitacion.change_cursocapacitacion')
PERMISOS_CURSO_BORRAR = ('capacitacion.delete_curso', 'capacitacion.delete_cursocapacitacion')

PERMISOS_MODULO_CREAR = ('capacitacion.add_modulo', 'capacitacion.add_modulocontenido')
PERMISOS_MODULO_GESTION = ('capacitacion.change_modulo', 'capacitacion.change_modulocontenido')
PERMISOS_MODULO_BORRAR = ('capacitacion.delete_modulo', 'capacitacion.delete_modulocontenido')


def _tiene_alguno_permiso(user, permisos):
    return any(user.has_perm(permiso) for permiso in permisos)


class CursoCapacitacionViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsApprovedUser]
    ordering_fields = ['fecha_creacion', 'fecha_actualizacion', 'titulo']
    ordering = ['-fecha_creacion']

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return CursoCapacitacionWriteSerializer
        return CursoCapacitacionSerializer

    def get_queryset(self):
        user = self.request.user

        modulos_activos_qs = ModuloContenido.objects.filter(activo=True).order_by('orden', 'id')
        queryset = CursoCapacitacion.objects.select_related('empresa', 'creado_por').prefetch_related(
            Prefetch('modulos', queryset=modulos_activos_qs)
        )

        if es_acceso_global(user):
            return queryset

        if not user.empresa_id:
            return CursoCapacitacion.objects.none()

        progreso_usuario_qs = ProgresoUsuario.objects.filter(usuario=user).prefetch_related('modulos_completados')
        return (
            queryset.filter(
                Q(empresa=user.empresa)
                | Q(empresa__isnull=True, creado_por_admin=True)
            )
            .distinct()
            .prefetch_related(Prefetch('progresos', queryset=progreso_usuario_qs, to_attr='progreso_usuario_actual'))
        )

    def _puede_gestionar_curso(self, user, curso, accion='update'):
        if user.is_superuser:
            if accion == 'destroy':
                return True
            return bool(curso.creado_por_admin and curso.empresa_id is None)

        if es_acceso_global(user):
            return bool(curso.creado_por_admin and curso.empresa_id is None)

        if not user.empresa_id:
            return False

        if curso.creado_por_admin or curso.empresa_id != user.empresa_id:
            return False

        if accion == 'destroy':
            return _tiene_alguno_permiso(user, PERMISOS_CURSO_BORRAR + PERMISOS_CURSO_GESTION)

        return bool(
            _tiene_alguno_permiso(user, PERMISOS_CURSO_GESTION)
        )

    def _validar_permiso_gestion(self, user, curso, accion='update'):
        if self._puede_gestionar_curso(user, curso, accion=accion):
            return

        raise PermissionDenied('No tienes permisos para gestionar este curso.')

    def perform_create(self, serializer):
        user = self.request.user

        if es_acceso_global(user):
            serializer.save(
                empresa=None,
                creado_por_admin=True,
                creado_por=user,
            )
            return

        # Control de capacidad por permiso (no por etiqueta de rol).
        if not _tiene_alguno_permiso(user, PERMISOS_CURSO_CREAR):
            raise PermissionDenied('No tienes permisos para crear cursos.')

        if not user.empresa_id:
            raise PermissionDenied('Tu usuario no tiene una empresa asociada para crear cursos internos.')

        serializer.save(
            empresa=user.empresa,
            creado_por_admin=False,
            creado_por=user,
        )

    def perform_update(self, serializer):
        curso = self.get_object()
        self._validar_permiso_gestion(self.request.user, curso, accion='update')
        serializer.save()

    def perform_destroy(self, instance):
        self._validar_permiso_gestion(self.request.user, instance, accion='destroy')
        instance.delete()

    def destroy(self, request, *args, **kwargs):
        user = request.user

        # Permite a SuperAdmin borrar cualquier curso incluso fuera del queryset visible del listado.
        if user.is_superuser:
            instance = get_object_or_404(CursoCapacitacion.objects.all(), pk=kwargs.get('pk'))
            self.perform_destroy(instance)
            return Response(status=status.HTTP_204_NO_CONTENT)

        return super().destroy(request, *args, **kwargs)

    @action(detail=True, methods=['post'], url_path='progreso')
    def actualizar_progreso(self, request, pk=None):
        user = request.user
        curso = self.get_object()

        if es_acceso_global(user):
            raise PermissionDenied('Los perfiles globales no registran progreso academico.')

        if not user.empresa_id:
            raise PermissionDenied('Tu usuario no tiene una empresa asociada.')

        if curso.empresa_id and curso.empresa_id != user.empresa_id:
            raise PermissionDenied('No puedes reportar progreso en cursos de otra empresa.')

        modulo_id = request.data.get('modulo_id')
        if not modulo_id:
            raise ValidationError({'modulo_id': 'Este campo es obligatorio.'})

        modulo = curso.modulos.filter(id=modulo_id, activo=True).first()
        if not modulo:
            raise ValidationError({'modulo_id': 'El modulo no existe o no pertenece a este curso.'})

        completado_raw = request.data.get('completado', True)
        if isinstance(completado_raw, str):
            completado = completado_raw.strip().lower() in {'1', 'true', 'si', 'yes'}
        else:
            completado = bool(completado_raw)

        progreso, _ = ProgresoUsuario.objects.get_or_create(usuario=user, curso=curso)

        if completado:
            progreso.modulos_completados.add(modulo)
        else:
            progreso.modulos_completados.remove(modulo)

        progreso.recalcular_estado()
        progreso_data = ProgresoUsuarioSerializer(progreso, context={'request': request}).data

        return Response(
            {
                'detail': 'Progreso actualizado correctamente.',
                'curso_id': curso.id,
                'progreso': progreso_data,
            },
            status=status.HTTP_200_OK,
        )


class ModuloContenidoViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsApprovedUser]
    serializer_class = ModuloContenidoSerializer
    ordering_fields = ['orden', 'id']
    ordering = ['orden', 'id']

    def get_queryset(self):
        user = self.request.user
        queryset = ModuloContenido.objects.select_related('curso', 'curso__empresa')

        curso_id = self.request.query_params.get('curso')

        if es_acceso_global(user):
            if curso_id:
                queryset = queryset.filter(curso_id=curso_id)
            return queryset

        if not user.empresa_id:
            return ModuloContenido.objects.none()

        queryset = queryset.filter(
            Q(curso__empresa=user.empresa)
            | Q(curso__empresa__isnull=True, curso__creado_por_admin=True)
        ).distinct()

        if curso_id:
            queryset = queryset.filter(curso_id=curso_id)

        return queryset

    def _validar_permiso_edicion_curso(self, user, curso, accion='update'):
        if user.is_superuser:
            if accion == 'destroy':
                return
            if curso.creado_por_admin and curso.empresa_id is None:
                return
            raise PermissionDenied('SuperAdmin solo gestiona el catalogo global Aegis.')

        if es_acceso_global(user):
            if curso.creado_por_admin and curso.empresa_id is None:
                return
            raise PermissionDenied('Los perfiles globales solo gestionan el catalogo oficial Aegis.')

        if not user.empresa_id or curso.creado_por_admin or curso.empresa_id != user.empresa_id:
            raise PermissionDenied('No tienes permisos para gestionar modulos de este curso.')

        if accion == 'create':
            if _tiene_alguno_permiso(user, PERMISOS_MODULO_CREAR + PERMISOS_CURSO_GESTION):
                return
        elif accion == 'destroy':
            if _tiene_alguno_permiso(user, PERMISOS_MODULO_BORRAR + PERMISOS_CURSO_GESTION):
                return
        else:
            if _tiene_alguno_permiso(user, PERMISOS_MODULO_GESTION + PERMISOS_CURSO_GESTION):
                return

        raise PermissionDenied('No tienes permisos para gestionar modulos de este curso.')

    def perform_create(self, serializer):
        curso = serializer.validated_data['curso']
        self._validar_permiso_edicion_curso(self.request.user, curso, accion='create')
        serializer.save()

    def perform_update(self, serializer):
        modulo = self.get_object()
        self._validar_permiso_edicion_curso(self.request.user, modulo.curso, accion='update')
        serializer.save()

    def perform_destroy(self, instance):
        self._validar_permiso_edicion_curso(self.request.user, instance.curso, accion='destroy')

        curso = instance.curso
        with transaction.atomic():
            instance.delete()

            # Al eliminar un modulo se recalcula progreso de todos los usuarios del curso.
            for progreso in ProgresoUsuario.objects.filter(curso=curso):
                progreso.recalcular_estado()

    def destroy(self, request, *args, **kwargs):
        user = request.user

        # Permite a SuperAdmin borrar modulos fuera del queryset visible del listado.
        if user.is_superuser:
            instance = get_object_or_404(ModuloContenido.objects.select_related('curso'), pk=kwargs.get('pk'))
            self.perform_destroy(instance)
            return Response(status=status.HTTP_204_NO_CONTENT)

        return super().destroy(request, *args, **kwargs)


class ProgresoUsuarioViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated, IsApprovedUser]
    serializer_class = ProgresoUsuarioSerializer

    def get_queryset(self):
        user = self.request.user
        queryset = ProgresoUsuario.objects.select_related('curso', 'curso__empresa').prefetch_related('modulos_completados')

        if es_acceso_global(user):
            usuario_id = self.request.query_params.get('usuario')
            if usuario_id:
                return queryset.filter(usuario_id=usuario_id)
            return queryset

        return queryset.filter(usuario=user)
