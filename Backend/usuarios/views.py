from rest_framework import status, generics, permissions, viewsets, mixins
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from django.db import transaction
from django.db.models import Q
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.utils.crypto import get_random_string
from django.utils.dateparse import parse_date, parse_datetime
from django.utils import timezone
from django.contrib.auth import authenticate, get_user_model
from django.shortcuts import get_object_or_404
from datetime import datetime, time
from implementacion.models import Empresa, ControlISO, EvaluacionControl
from capacitacion.models import CursoCapacitacion, ModuloContenido, ProgresoUsuario
from .models import BitacoraSeguridadUsuario, Notificacion
from .serializers import (
    RegistroSerializer,
    LoginSerializer,
    UsuarioSerializer,
    CambiarPasswordSerializer,
    ActualizarPerfilSerializer,
    GlobalUserAdminSerializer,
    BitacoraSeguridadUsuarioSerializer,
    NotificacionSerializer,
)
from .permissions import (
    IsApprovedUser,
    IsSuperAdminOrAdminSistema,
    es_acceso_global,
    es_admin_sistema,
)

User = get_user_model()


def _rol_normalizado(user):
    rol = getattr(user, 'rol', None)
    if rol == 'AUDITOR_INTERNO':
        return 'AUDITOR'
    return rol


def _es_lider_equipo(user):
    return bool(
        user
        and user.is_authenticated
        and (
            _rol_normalizado(user) == 'LIDER_EQUIPO'
            or getattr(user, 'es_administrador_empresa', False)
        )
    )


class AegisTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Token JWT con emisión explícita de señal de login exitoso para bitácora forense."""

    def validate(self, attrs):
        data = super().validate(attrs)
        user = self.user
        if user is not None:
            data['usuario'] = UsuarioSerializer(user).data
            user_logged_in.send(
                sender=user.__class__,
                request=self.context.get('request'),
                user=user,
            )
        return data


class AegisTokenObtainPairView(TokenObtainPairView):
    serializer_class = AegisTokenObtainPairSerializer


def _extract_client_ip(request):
    forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if forwarded_for:
        return forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


def _registrar_evento_bitacora(request, actor, usuario_objetivo, accion, detalle=None):
    empresa_relacionada = (
        getattr(usuario_objetivo, 'empresa', None)
        or getattr(actor, 'empresa', None)
    )

    BitacoraSeguridadUsuario.objects.create(
        actor=actor,
        usuario_objetivo=usuario_objetivo,
        empresa=empresa_relacionada,
        accion=accion,
        detalle=detalle or {},
        ip_origen=_extract_client_ip(request),
        user_agent=(request.META.get('HTTP_USER_AGENT') or '')[:512],
    )


def _parse_datetime_filter(value, end_of_day=False):
    if not value:
        return None

    dt_value = parse_datetime(value)
    if dt_value is not None:
        if timezone.is_naive(dt_value):
            return timezone.make_aware(dt_value)
        return dt_value

    date_value = parse_date(value)
    if date_value is None:
        return None

    time_value = time.max if end_of_day else time.min
    return timezone.make_aware(datetime.combine(date_value, time_value))


class GlobalUsersPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


class BitacoraSeguridadPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class BitacoraSeguridadUsuarioListView(generics.ListAPIView):
    """
    Endpoint global de bitácora forense (WORM).
    Solo perfiles globales (SuperAdmin o ADMIN_SISTEMA) pueden consultar.
    """

    serializer_class = BitacoraSeguridadUsuarioSerializer
    permission_classes = [permissions.IsAuthenticated, IsSuperAdminOrAdminSistema]
    pagination_class = BitacoraSeguridadPagination
    queryset = (
        BitacoraSeguridadUsuario.objects
        .select_related('actor', 'usuario_objetivo', 'empresa')
        .all()
        .order_by('-fecha_evento')
    )

    def get_queryset(self):
        queryset = super().get_queryset()

        search = self.request.query_params.get('search', '').strip()
        if search:
            queryset = queryset.filter(
                Q(actor__username__icontains=search)
                | Q(actor__first_name__icontains=search)
                | Q(actor__last_name__icontains=search)
                | Q(actor__email__icontains=search)
                | Q(usuario_objetivo__username__icontains=search)
                | Q(usuario_objetivo__first_name__icontains=search)
                | Q(usuario_objetivo__last_name__icontains=search)
                | Q(usuario_objetivo__email__icontains=search)
                | Q(empresa__nombre__icontains=search)
                | Q(ip_origen__icontains=search)
            )

        accion = self.request.query_params.get('accion', '').strip()
        if accion:
            queryset = queryset.filter(accion=accion)

        empresa_id = self.request.query_params.get('empresa_id', '').strip()
        if empresa_id.isdigit():
            queryset = queryset.filter(empresa_id=int(empresa_id))

        actor_id = self.request.query_params.get('actor_id', '').strip()
        if actor_id.isdigit():
            queryset = queryset.filter(actor_id=int(actor_id))

        fecha_desde = _parse_datetime_filter(
            self.request.query_params.get('fecha_desde', '').strip(),
            end_of_day=False,
        )
        if fecha_desde is not None:
            queryset = queryset.filter(fecha_evento__gte=fecha_desde)

        fecha_hasta = _parse_datetime_filter(
            self.request.query_params.get('fecha_hasta', '').strip(),
            end_of_day=True,
        )
        if fecha_hasta is not None:
            queryset = queryset.filter(fecha_evento__lte=fecha_hasta)

        return queryset


class NotificacionViewSet(mixins.ListModelMixin, mixins.UpdateModelMixin, viewsets.GenericViewSet):
    """
    API in-app para notificaciones del usuario autenticado.
    Permite listar y marcar como leídas (PATCH de campo `leida`).
    """

    serializer_class = NotificacionSerializer
    permission_classes = [permissions.IsAuthenticated, IsApprovedUser]
    queryset = Notificacion.objects.select_related('usuario_destino').all().order_by('-fecha_creacion')

    def get_queryset(self):
        queryset = super().get_queryset().filter(usuario_destino=self.request.user)

        leida = self.request.query_params.get('leida', '').strip().lower()
        if leida in ('true', '1', 'si', 'yes'):
            queryset = queryset.filter(leida=True)
        elif leida in ('false', '0', 'no'):
            queryset = queryset.filter(leida=False)

        return queryset

    def partial_update(self, request, *args, **kwargs):
        campos_permitidos = {'leida'}
        campos_recibidos = set(request.data.keys())

        if not campos_recibidos:
            raise ValidationError({'detail': 'Debe enviar al menos el campo `leida`.'})

        campos_invalidos = campos_recibidos - campos_permitidos
        if campos_invalidos:
            raise ValidationError(
                {'detail': f'Campos no permitidos en actualización: {", ".join(sorted(campos_invalidos))}'}
            )

        return super().partial_update(request, *args, **kwargs)

    @action(detail=False, methods=['post'], url_path='marcar-todas-leidas')
    def marcar_todas_leidas(self, request):
        actualizadas = self.get_queryset().filter(leida=False).update(leida=True)
        return Response(
            {'detail': 'Notificaciones marcadas como leídas.', 'actualizadas': actualizadas},
            status=status.HTTP_200_OK,
        )


class DashboardStatsView(APIView):
    """
    Endpoint maestro de estadísticas para dashboard.
    Responde métricas dinámicas según rol del usuario autenticado.
    """

    permission_classes = [permissions.IsAuthenticated, IsApprovedUser]

    def _cursos_visibles_queryset(self, user):
        if not user.empresa_id:
            return CursoCapacitacion.objects.none()

        return (
            CursoCapacitacion.objects.filter(activo=True)
            .filter(
                Q(creado_por_admin=True, empresa__isnull=True)
                | Q(creado_por_admin=False, empresa_id=user.empresa_id)
            )
            .distinct()
        )

    def _metricas_capacitacion(self, user, cursos_visibles_qs):
        total_cursos_visibles = cursos_visibles_qs.count()

        cursos_completados = (
            ProgresoUsuario.objects.filter(
                usuario=user,
                curso__in=cursos_visibles_qs,
                curso_completado=True,
            )
            .values('curso_id')
            .distinct()
            .count()
        )

        mis_cursos_pendientes = max(total_cursos_visibles - cursos_completados, 0)

        mis_modulos_completados = (
            ModuloContenido.objects.filter(
                curso__in=cursos_visibles_qs,
                activo=True,
                progresos_usuarios__usuario=user,
            )
            .distinct()
            .count()
        )

        total_modulos_activos = (
            ModuloContenido.objects.filter(curso__in=cursos_visibles_qs, activo=True)
            .count()
        )

        return {
            'mis_cursos_pendientes': mis_cursos_pendientes,
            'mis_modulos_completados': mis_modulos_completados,
            'total_modulos_activos': total_modulos_activos,
        }

    def get(self, request):
        user = request.user

        if es_acceso_global(user):
            return Response(
                {
                    'scope': 'SUPERADMIN',
                    'es_admin_sistema': es_admin_sistema(user),
                    'total_empresas': Empresa.objects.count(),
                    'total_usuarios': User.objects.count(),
                    'total_cursos_globales': CursoCapacitacion.objects.filter(
                        creado_por_admin=True,
                        empresa__isnull=True,
                    ).count(),
                },
                status=status.HTTP_200_OK,
            )

        cursos_visibles_qs = self._cursos_visibles_queryset(user)
        metricas_capacitacion = self._metricas_capacitacion(user, cursos_visibles_qs)

        if not user.empresa_id:
            return Response(
                {
                    'scope': 'CAPACITACION',
                    **metricas_capacitacion,
                },
                status=status.HTTP_200_OK,
            )

        total_controles = ControlISO.objects.count()
        evaluaciones_empresa_qs = EvaluacionControl.objects.filter(empresa_id=user.empresa_id)

        controles_evaluados = evaluaciones_empresa_qs.values('control_id').distinct().count()
        controles_implementados = evaluaciones_empresa_qs.filter(estado='IMPLEMENTADO').count()
        controles_en_proceso = evaluaciones_empresa_qs.filter(estado='EN_PROCESO').count()
        controles_no_aplica = evaluaciones_empresa_qs.filter(estado='NO_APLICA').count()

        controles_pendientes = max(total_controles - controles_evaluados, 0)
        total_controles_aplicables = max(total_controles - controles_no_aplica, 0)
        porcentaje_cumplimiento_iso = (
            round((controles_implementados / total_controles_aplicables) * 100, 2)
            if total_controles_aplicables
            else 0
        )

        return Response(
            {
                'scope': 'EMPRESA_ISO',
                'porcentaje_cumplimiento_iso': porcentaje_cumplimiento_iso,
                'controles_pendientes': controles_pendientes,
                'cursos_activos': cursos_visibles_qs.count(),
                'controles_implementados': controles_implementados,
                'controles_en_proceso': controles_en_proceso,
                'total_controles': total_controles,
                **metricas_capacitacion,
            },
            status=status.HTTP_200_OK,
        )


class GlobalUserViewSet(viewsets.ModelViewSet):
    """
    Centro de comando global de usuarios para infraestructura.
    - SuperAdmin: control total (create/update/inactivate/reset).
    - ADMIN_SISTEMA: lectura global + aprobación/rechazo global.
    - Resto de roles: visibilidad acotada a su empresa.
    """
    serializer_class = GlobalUserAdminSerializer
    permission_classes = [permissions.IsAuthenticated, IsApprovedUser]
    pagination_class = GlobalUsersPagination
    queryset = User.objects.all().select_related('empresa').order_by('-date_joined')

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user

        if not es_acceso_global(user):
            if not user.empresa_id:
                return User.objects.none()
            queryset = queryset.filter(empresa_id=user.empresa_id)

        search = self.request.query_params.get('search', '').strip()

        if search:
            queryset = queryset.filter(
                Q(username__icontains=search)
                | Q(first_name__icontains=search)
                | Q(last_name__icontains=search)
                | Q(email__icontains=search)
                | Q(empresa__nombre__icontains=search)
            )

        estado = self.request.query_params.get('estado')
        if estado == 'activo':
            queryset = queryset.filter(is_active=True)
        elif estado == 'inactivo':
            queryset = queryset.filter(is_active=False)

        rol = self.request.query_params.get('rol')
        if rol:
            queryset = queryset.filter(rol=rol)

        return queryset

    def create(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            raise PermissionDenied('Solo SuperAdmin puede crear usuarios globales.')

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            user = serializer.save()

            generated_password = getattr(user, '_generated_password', None)
            _registrar_evento_bitacora(
                request=request,
                actor=request.user,
                usuario_objetivo=user,
                accion='CREACION_USUARIO',
                detalle={
                    'rol': user.rol,
                    'empresa_id': user.empresa_id,
                    'is_active': user.is_active,
                    'is_approved': user.is_approved,
                    'es_administrador_empresa': user.es_administrador_empresa,
                    'password_generada_automaticamente': bool('password' not in request.data and generated_password),
                },
            )

        response_data = self.get_serializer(user).data

        # Si no se envió contraseña explícita, exponer temporal para flujo controlado.
        if 'password' not in request.data and generated_password:
            response_data['temporary_password'] = generated_password

        headers = self.get_success_headers(response_data)
        return Response(response_data, status=status.HTTP_201_CREATED, headers=headers)

    def update(self, request, *args, **kwargs):
        if not es_acceso_global(request.user):
            raise PermissionDenied('No tienes permisos para modificar usuarios globales.')

        if es_admin_sistema(request.user):
            campos_permitidos = {'is_approved', 'is_active', 'es_administrador_empresa'}
            campos_enviados = set(request.data.keys())
            campos_invalidos = campos_enviados - campos_permitidos

            if campos_invalidos:
                raise PermissionDenied(
                    'ADMIN_SISTEMA solo puede aprobar/rechazar usuarios '
                    f'(campos permitidos: {", ".join(sorted(campos_permitidos))}).'
                )

        partial = kwargs.pop('partial', False)
        instance = self.get_object()

        previo = {
            'rol': instance.rol,
            'empresa_id': instance.empresa_id,
            'is_active': instance.is_active,
            'is_approved': instance.is_approved,
            'es_administrador_empresa': instance.es_administrador_empresa,
            'email': instance.email,
        }

        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            usuario_actualizado = serializer.save()

            posterior = {
                'rol': usuario_actualizado.rol,
                'empresa_id': usuario_actualizado.empresa_id,
                'is_active': usuario_actualizado.is_active,
                'is_approved': usuario_actualizado.is_approved,
                'es_administrador_empresa': usuario_actualizado.es_administrador_empresa,
                'email': usuario_actualizado.email,
            }

            cambios = {
                key: {
                    'before': previo[key],
                    'after': posterior[key],
                }
                for key in previo
                if previo[key] != posterior[key]
            }

            accion = 'CAMBIO_ROL' if 'rol' in cambios else 'ACTUALIZACION_USUARIO'

            _registrar_evento_bitacora(
                request=request,
                actor=request.user,
                usuario_objetivo=usuario_actualizado,
                accion=accion,
                detalle={
                    'cambios': cambios,
                    'password_actualizada': 'password' in request.data,
                },
            )

        return Response(self.get_serializer(usuario_actualizado).data, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            raise PermissionDenied('Solo SuperAdmin puede inactivar usuarios globales.')

        instance = self.get_object()

        if instance.id == request.user.id:
            return Response(
                {'detail': 'No puedes inactivar tu propio usuario.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not instance.is_active:
            return Response(
                {'detail': 'El usuario ya se encuentra inactivo.'},
                status=status.HTTP_200_OK,
            )

        with transaction.atomic():
            estado_previo = instance.is_active
            instance.is_active = False
            instance.save(update_fields=['is_active'])

            _registrar_evento_bitacora(
                request=request,
                actor=request.user,
                usuario_objetivo=instance,
                accion='INACTIVACION_USUARIO',
                detalle={
                    'soft_delete': True,
                    'is_active_before': estado_previo,
                    'is_active_after': instance.is_active,
                },
            )

        return Response(
            {
                'detail': 'Usuario inactivado correctamente (soft delete).',
                'usuario': self.get_serializer(instance).data,
            },
            status=status.HTTP_200_OK,
        )

    @action(detail=False, methods=['get'], url_path='stats')
    def stats(self, request):
        if not es_acceso_global(request.user):
            raise PermissionDenied('No tienes permisos para consultar estadísticas globales de usuarios.')

        data = {
            'total_users': User.objects.count(),
            'active_users': User.objects.filter(is_active=True).count(),
            'global_admins': User.objects.filter(is_superuser=True).count(),
            'total_companies': Empresa.objects.count(),
        }
        return Response(data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], url_path='empresas')
    def empresas(self, request):
        if es_acceso_global(request.user):
            empresas = Empresa.objects.all().order_by('nombre')
        elif request.user.empresa_id:
            empresas = Empresa.objects.filter(id=request.user.empresa_id).order_by('nombre')
        else:
            empresas = Empresa.objects.none()

        data = [
            {
                'id': empresa.id,
                'nombre': empresa.nombre,
                'tipo': empresa.tipo,
            }
            for empresa in empresas
        ]
        return Response(data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['patch'], url_path='inactivar')
    def inactivar(self, request, pk=None):
        return self.destroy(request, pk=pk)

    @action(detail=True, methods=['post'], url_path='forzar-reset-password')
    def forzar_reset_password(self, request, pk=None):
        if not request.user.is_superuser:
            raise PermissionDenied('Solo SuperAdmin puede forzar reseteo de contraseña global.')

        user = self.get_object()

        if user.id == request.user.id:
            return Response(
                {'detail': 'No puedes forzar el reseteo de tu propia contraseña.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        temporary_password = get_random_string(12)

        with transaction.atomic():
            user.set_password(temporary_password)
            user.save(update_fields=['password'])

            reset_link = (
                f'https://aegis.local/reset-password?uid={user.id}&token={get_random_string(48)}'
            )

            _registrar_evento_bitacora(
                request=request,
                actor=request.user,
                usuario_objetivo=user,
                accion='RESET_PASSWORD_FORZADO',
                detalle={
                    'credencial_temporal_generada': True,
                    'reset_link_generado': True,
                },
            )

        return Response(
            {
                'detail': 'Reseteo forzado ejecutado. Se generó credencial temporal.',
                'temporary_password': temporary_password,
                'reset_link': reset_link,
            },
            status=status.HTTP_200_OK,
        )


class RegistroView(generics.CreateAPIView):
    """
    Vista para el registro de nuevos usuarios.
    POST /api/usuarios/registro/
    """
    serializer_class = RegistroSerializer
    permission_classes = [permissions.AllowAny]
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Generar tokens JWT para el usuario
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        
        # Serializar la información del usuario
        user_data = UsuarioSerializer(user).data
        
        return Response({
            'message': 'Usuario registrado exitosamente',
            'access': access_token,
            'refresh': str(refresh),
            'usuario': user_data
        }, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    """
    Vista para el login de usuarios.
    POST /api/usuarios/login/
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        username = serializer.validated_data['username']
        password = serializer.validated_data['password']
        
        # Autenticar usuario
        user = authenticate(username=username, password=password)
        
        if user is None:
            return Response({
                'error': 'Credenciales inválidas'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        if not user.is_active:
            return Response({
                'error': 'Usuario inactivo'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Generar tokens JWT para el usuario
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        
        # Serializar la información del usuario
        user_data = UsuarioSerializer(user).data
        
        return Response({
            'message': 'Login exitoso',
            'access': access_token,
            'refresh': str(refresh),
            'usuario': user_data
        }, status=status.HTTP_200_OK)


class LogoutView(APIView):
    """
    Vista para el logout de usuarios.
    POST /api/usuarios/logout/
    
    Nota: JWT es stateless, por lo que el logout se maneja en el frontend
    eliminando el token del localStorage. Esta vista solo confirma la acción.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        user_logged_out.send(
            sender=request.user.__class__,
            request=request,
            user=request.user,
        )
        return Response({
            'message': 'Logout exitoso'
        }, status=status.HTTP_200_OK)


class PerfilView(APIView):
    """
    Vista para obtener el perfil del usuario autenticado.
    GET /api/usuarios/perfil/
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        serializer = UsuarioSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ActualizarPerfilView(generics.UpdateAPIView):
    """
    Vista para actualizar el perfil del usuario autenticado.
    PUT/PATCH /api/usuarios/perfil/actualizar/
    """
    serializer_class = ActualizarPerfilSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        return self.request.user
    
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        return Response({
            'message': 'Perfil actualizado exitosamente',
            'usuario': UsuarioSerializer(instance).data
        }, status=status.HTTP_200_OK)


class CambiarPasswordView(APIView):
    """
    Vista para cambiar la contraseña del usuario autenticado.
    POST /api/usuarios/cambiar-password/
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        serializer = CambiarPasswordSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        
        # Cambiar la contraseña
        user = request.user
        user.set_password(serializer.validated_data['password_nueva'])
        user.save()
        
        # Generar nuevos tokens JWT
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        
        return Response({
            'message': 'Contraseña actualizada exitosamente',
            'access': access_token,
            'refresh': str(refresh)
        }, status=status.HTTP_200_OK)


class ListarUsuariosPorEmpresaView(generics.ListAPIView):
    """
    Vista para listar usuarios de la misma empresa del usuario autenticado.
    GET /api/usuarios/empresa/
    """
    serializer_class = UsuarioSerializer
    permission_classes = [permissions.IsAuthenticated, IsApprovedUser]
    
    def get_queryset(self):
        user = self.request.user
        
        # SuperAdmin y ADMIN_SISTEMA pueden ver todos.
        if es_acceso_global(user):
            return User.objects.all()
        
        # Si tiene empresa, mostrar solo usuarios de su empresa
        if user.empresa:
            return User.objects.filter(empresa=user.empresa)
        
        # Si no tiene empresa, solo puede ver su propio perfil
        return User.objects.filter(id=user.id)


class GestionEquipoView(APIView):
    """
    Lista los usuarios del equipo de la misma empresa.
    Solo accesible para administradores de empresa o superusuarios.
    """
    permission_classes = [permissions.IsAuthenticated, IsApprovedUser]

    def get(self, request):
        user = request.user
        empresa_id = request.query_params.get('empresa_id', '').strip()
        search = request.query_params.get('search', '').strip()
        rol = request.query_params.get('rol', '').strip()

        if es_acceso_global(user):
            queryset = User.objects.all().select_related('empresa').order_by('empresa__nombre', 'rol', 'username')

            if empresa_id.isdigit():
                queryset = queryset.filter(empresa_id=int(empresa_id))

            if search:
                queryset = queryset.filter(
                    Q(username__icontains=search)
                    | Q(first_name__icontains=search)
                    | Q(last_name__icontains=search)
                    | Q(email__icontains=search)
                    | Q(empresa__nombre__icontains=search)
                )

            if rol:
                queryset = queryset.filter(rol=rol)
        else:
            if not _es_lider_equipo(user):
                raise PermissionDenied('Solo el líder de equipo puede gestionar usuarios de su empresa.')
            if not user.empresa_id:
                raise PermissionDenied('Tu usuario no tiene una empresa asociada.')

            queryset = User.objects.filter(
                empresa=user.empresa
            ).select_related('empresa').order_by('rol', 'username')

            if search:
                queryset = queryset.filter(
                    Q(username__icontains=search)
                    | Q(first_name__icontains=search)
                    | Q(last_name__icontains=search)
                    | Q(email__icontains=search)
                )

            if rol:
                queryset = queryset.filter(rol=rol)

        serializer = UsuarioSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class AprobarMiembroEquipoView(APIView):
    """
    Aprueba a un usuario pendiente de la misma empresa.
    """
    permission_classes = [permissions.IsAuthenticated, IsApprovedUser]

    def post(self, request, user_id):
        admin_user = request.user

        if not es_acceso_global(admin_user):
            if not _es_lider_equipo(admin_user):
                raise PermissionDenied('Solo el líder de equipo puede aprobar usuarios.')
            if not admin_user.empresa_id:
                raise PermissionDenied('Tu usuario no tiene una empresa asociada.')

        objetivo = get_object_or_404(User, id=user_id)

        if not es_acceso_global(admin_user) and objetivo.empresa_id != admin_user.empresa_id:
            raise PermissionDenied('No puedes aprobar usuarios de otra empresa.')

        with transaction.atomic():
            objetivo.is_approved = True
            objetivo.is_active = True
            objetivo.save(update_fields=['is_approved', 'is_active'])

            _registrar_evento_bitacora(
                request=request,
                actor=admin_user,
                usuario_objetivo=objetivo,
                accion='APROBACION_USUARIO',
                detalle={
                    'is_approved_after': objetivo.is_approved,
                    'is_active_after': objetivo.is_active,
                },
            )

        return Response(
            {
                'message': 'Usuario aprobado correctamente.',
                'usuario': UsuarioSerializer(objetivo).data
            },
            status=status.HTTP_200_OK
        )


class RechazarMiembroEquipoView(APIView):
    """
    Rechaza a un usuario pendiente de la misma empresa.
    """
    permission_classes = [permissions.IsAuthenticated, IsApprovedUser]

    def post(self, request, user_id):
        admin_user = request.user

        if not es_acceso_global(admin_user):
            if not _es_lider_equipo(admin_user):
                raise PermissionDenied('Solo el líder de equipo puede rechazar usuarios.')
            if not admin_user.empresa_id:
                raise PermissionDenied('Tu usuario no tiene una empresa asociada.')

        objetivo = get_object_or_404(User, id=user_id)

        if objetivo.id == admin_user.id:
            return Response(
                {'error': 'No puedes rechazar tu propio usuario.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not es_acceso_global(admin_user) and objetivo.empresa_id != admin_user.empresa_id:
            raise PermissionDenied('No puedes rechazar usuarios de otra empresa.')

        with transaction.atomic():
            objetivo.is_approved = False
            objetivo.es_administrador_empresa = False
            objetivo.is_active = False
            objetivo.save(update_fields=['is_approved', 'es_administrador_empresa', 'is_active'])

            _registrar_evento_bitacora(
                request=request,
                actor=admin_user,
                usuario_objetivo=objetivo,
                accion='RECHAZO_USUARIO',
                detalle={
                    'is_approved_after': objetivo.is_approved,
                    'es_administrador_empresa_after': objetivo.es_administrador_empresa,
                    'is_active_after': objetivo.is_active,
                },
            )

        return Response(
            {
                'message': 'Usuario rechazado correctamente.',
                'usuario': UsuarioSerializer(objetivo).data
            },
            status=status.HTTP_200_OK
        )
