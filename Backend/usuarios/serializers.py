from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.utils.crypto import get_random_string
from implementacion.models import Empresa
from .models import BitacoraSeguridadUsuario, Notificacion

User = get_user_model()

PERMISOS_FRONTEND = {
    'VER_DASHBOARD': 'frontend.view_dashboard',
    'VER_IMPLEMENTACION': 'frontend.view_implementacion',
    'VER_AUDITORIA': 'frontend.view_auditoria',
    'VER_CAPACITACION': 'frontend.view_capacitacion',
    'VER_EQUIPO': 'frontend.view_equipo',
    'VER_REPORTES': 'frontend.view_reportes',
    'VER_USUARIOS_GLOBALES': 'frontend.view_usuarios_globales',
}


def _rol_normalizado(usuario):
    rol = getattr(usuario, 'rol', None)
    if rol == 'AUDITOR_INTERNO':
        return 'AUDITOR'
    return rol


def _permisos_frontend_por_rol(usuario):
    if getattr(usuario, 'is_superuser', False):
        return {
            PERMISOS_FRONTEND['VER_DASHBOARD'],
            PERMISOS_FRONTEND['VER_USUARIOS_GLOBALES'],
            PERMISOS_FRONTEND['VER_EQUIPO'],
            PERMISOS_FRONTEND['VER_REPORTES'],
            PERMISOS_FRONTEND['VER_CAPACITACION'],
        }

    rol = _rol_normalizado(usuario)

    if rol == 'ADMIN_SISTEMA':
        return {
            PERMISOS_FRONTEND['VER_DASHBOARD'],
            PERMISOS_FRONTEND['VER_USUARIOS_GLOBALES'],
            PERMISOS_FRONTEND['VER_EQUIPO'],
            PERMISOS_FRONTEND['VER_REPORTES'],
            PERMISOS_FRONTEND['VER_CAPACITACION'],
        }

    if rol == 'LIDER_EQUIPO':
        return {
            PERMISOS_FRONTEND['VER_DASHBOARD'],
            PERMISOS_FRONTEND['VER_EQUIPO'],
            PERMISOS_FRONTEND['VER_REPORTES'],
        }

    if rol == 'IMPLEMENTADOR':
        return {
            PERMISOS_FRONTEND['VER_DASHBOARD'],
            PERMISOS_FRONTEND['VER_IMPLEMENTACION'],
        }

    if rol == 'AUDITOR':
        return {
            PERMISOS_FRONTEND['VER_DASHBOARD'],
            PERMISOS_FRONTEND['VER_AUDITORIA'],
        }

    if rol in {'CAPACITADOR', 'EMPLEADO'}:
        return {
            PERMISOS_FRONTEND['VER_DASHBOARD'],
            PERMISOS_FRONTEND['VER_CAPACITACION'],
        }

    return {PERMISOS_FRONTEND['VER_DASHBOARD']}


def _permisos_frontend_desde_nativos(permisos_nativos):
    permisos_frontend = set()

    mapeo_directo = {
        'usuarios.view_dashboard': PERMISOS_FRONTEND['VER_DASHBOARD'],
        'usuarios.view_implementacion': PERMISOS_FRONTEND['VER_IMPLEMENTACION'],
        'usuarios.view_auditoria': PERMISOS_FRONTEND['VER_AUDITORIA'],
        'usuarios.view_capacitacion': PERMISOS_FRONTEND['VER_CAPACITACION'],
        'usuarios.view_equipo': PERMISOS_FRONTEND['VER_EQUIPO'],
        'usuarios.view_reportes': PERMISOS_FRONTEND['VER_REPORTES'],
        'usuarios.view_usuarios_globales': PERMISOS_FRONTEND['VER_USUARIOS_GLOBALES'],
        'usuarios.manage_global_users': PERMISOS_FRONTEND['VER_USUARIOS_GLOBALES'],
    }

    for permiso_nativo, permiso_frontend in mapeo_directo.items():
        if permiso_nativo in permisos_nativos:
            permisos_frontend.add(permiso_frontend)

    if permisos_frontend:
        permisos_frontend.add(PERMISOS_FRONTEND['VER_DASHBOARD'])

    return permisos_frontend


class EmpresaSerializer(serializers.ModelSerializer):
    """Serializer básico para la empresa"""
    class Meta:
        model = Empresa
        fields = ['id', 'nombre', 'tipo']


class UsuarioSerializer(serializers.ModelSerializer):
    """
    Serializer para el modelo UsuarioCustom con información completa.
    """
    empresa_info = EmpresaSerializer(source='empresa', read_only=True)
    rol_display = serializers.CharField(source='get_rol_display', read_only=True)
    is_approved = serializers.SerializerMethodField(read_only=True)
    es_administrador_empresa = serializers.SerializerMethodField(read_only=True)
    permisos = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'is_superuser', 'is_staff',
            'is_approved', 'es_administrador_empresa',
            'permisos',
            'rol', 'rol_display', 'empresa', 'empresa_info',
            'foto_perfil', 'is_active', 'date_joined'
        ]
        read_only_fields = ['id', 'date_joined', 'is_superuser', 'is_staff']

    def get_is_approved(self, obj):
        if obj.is_staff or obj.is_superuser or obj.rol == 'ADMIN_SISTEMA':
            return True
        return bool(getattr(obj, 'is_approved', False))

    def get_es_administrador_empresa(self, obj):
        if obj.is_staff or obj.is_superuser:
            return True
        return bool(
            getattr(obj, 'es_administrador_empresa', False)
            or getattr(obj, 'rol', None) == 'LIDER_EQUIPO'
        )

    def get_permisos(self, obj):
        permisos_nativos = set(obj.get_all_permissions())
        permisos_frontend = _permisos_frontend_desde_nativos(permisos_nativos)

        # Compatibilidad para flujos RBAC legacy hasta completar asignación por grupos/permisos.
        if not permisos_frontend:
            permisos_frontend = _permisos_frontend_por_rol(obj)

        return sorted(permisos_nativos | permisos_frontend)


class RegistroSerializer(serializers.ModelSerializer):
    """
    Serializer para el registro de nuevos usuarios.
    """
    password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'},
        min_length=8,
        help_text='Mínimo 8 caracteres'
    )
    password_confirm = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'},
        help_text='Debe coincidir con la contraseña'
    )
    nombre_empresa = serializers.CharField(
        write_only=True,
        required=True,
        help_text='Nombre de la empresa a crear'
    )
    
    class Meta:
        model = User
        fields = [
            'username', 'email', 'password', 'password_confirm',
            'first_name', 'last_name', 'rol', 'nombre_empresa', 'foto_perfil'
        ]
        extra_kwargs = {
            'email': {'required': True},
            'first_name': {'required': True},
            'last_name': {'required': True},
            'rol': {'required': False},
        }
    
    def validate_email(self, value):
        """Valida que el email no esté en uso"""
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("Este correo electrónico ya está en uso.")
        return value
    
    def validate_username(self, value):
        """Valida que el username no esté en uso"""
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Este nombre de usuario ya está en uso.")
        return value
    
    def validate(self, data):
        """Valida que las contraseñas coincidan"""
        if data.get('rol') == 'AUDITOR_INTERNO':
            data['rol'] = 'AUDITOR'

        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError({
                'password_confirm': 'Las contraseñas no coinciden.'
            })
        return data
    
    def create(self, validated_data):
        """Crea el usuario con la contraseña encriptada y su empresa"""
        # Extraer campos que no son del modelo User
        password = validated_data.pop('password')
        validated_data.pop('password_confirm')
        nombre_empresa_ingresado = validated_data.pop('nombre_empresa', '').strip()

        if not nombre_empresa_ingresado:
            raise serializers.ValidationError({
                'nombre_empresa': 'Debe indicar el nombre de la empresa.'
            })

        try:
            with transaction.atomic():
                empresa, created = Empresa.objects.get_or_create(
                    nombre=nombre_empresa_ingresado,
                    defaults={'tipo': 'PEQUENA'}
                )

                validated_data['empresa'] = empresa
                if created:
                    # Primer usuario de la empresa: liderazgo operativo automático.
                    validated_data['rol'] = 'LIDER_EQUIPO'
                    validated_data['is_approved'] = True
                    validated_data['es_administrador_empresa'] = True
                else:
                    # Empresa existente: mínimo privilegio por defecto y pendiente de aprobación.
                    validated_data['rol'] = 'EMPLEADO'
                    validated_data['is_approved'] = False
                    validated_data['es_administrador_empresa'] = False

                if validated_data.get('rol') == 'AUDITOR_INTERNO':
                    validated_data['rol'] = 'AUDITOR'

                user = User.objects.create_user(
                    password=password,
                    **validated_data
                )

                return user
        except IntegrityError as exc:
            error_text = str(exc).lower()
            if 'email' in error_text:
                raise serializers.ValidationError({
                    'email': 'Este correo electrónico ya está en uso.'
                })
            raise serializers.ValidationError(
                'No se pudo completar el registro por una restricción de unicidad.'
            )


class LoginSerializer(serializers.Serializer):
    """
    Serializer para el login de usuarios.
    """
    username = serializers.CharField(required=True)
    password = serializers.CharField(
        required=True,
        style={'input_type': 'password'},
        write_only=True
    )


class CambiarPasswordSerializer(serializers.Serializer):
    """
    Serializer para cambiar la contraseña del usuario autenticado.
    """
    password_actual = serializers.CharField(
        required=True,
        style={'input_type': 'password'},
        write_only=True
    )
    password_nueva = serializers.CharField(
        required=True,
        style={'input_type': 'password'},
        write_only=True,
        min_length=8
    )
    password_nueva_confirm = serializers.CharField(
        required=True,
        style={'input_type': 'password'},
        write_only=True
    )
    
    def validate(self, data):
        """Valida que las contraseñas nuevas coincidan"""
        if data['password_nueva'] != data['password_nueva_confirm']:
            raise serializers.ValidationError({
                'password_nueva_confirm': 'Las contraseñas no coinciden.'
            })
        return data
    
    def validate_password_actual(self, value):
        """Valida que la contraseña actual sea correcta"""
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('La contraseña actual es incorrecta.')
        return value


class ActualizarPerfilSerializer(serializers.ModelSerializer):
    """
    Serializer para actualizar el perfil del usuario autenticado.
    No permite cambiar rol ni empresa (solo administradores).
    """
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'foto_perfil']
        extra_kwargs = {
            'email': {'required': False},
        }
    
    def validate_email(self, value):
        """Valida que el email no esté en uso por otro usuario"""
        user = self.context['request'].user
        if User.objects.filter(email=value).exclude(id=user.id).exists():
            raise serializers.ValidationError("Este correo electrónico ya está en uso.")
        return value


class GlobalUserAdminSerializer(serializers.ModelSerializer):
    """
    Serializer de administración global de usuarios.
    Uso exclusivo para superusuarios (infraestructura).
    """
    empresa_info = EmpresaSerializer(source='empresa', read_only=True)
    rol_display = serializers.CharField(source='get_rol_display', read_only=True)
    full_name = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'full_name',
            'rol',
            'rol_display',
            'empresa',
            'empresa_info',
            'is_active',
            'is_approved',
            'es_administrador_empresa',
            'is_staff',
            'is_superuser',
            'date_joined',
            'last_login',
            'password',
        ]
        read_only_fields = ['id', 'is_staff', 'is_superuser', 'date_joined', 'last_login']
        extra_kwargs = {
            'password': {
                'write_only': True,
                'required': False,
                'allow_blank': False,
                'min_length': 8,
            },
            'email': {'required': True},
        }

    def get_full_name(self, obj):
        return obj.get_full_name() or obj.username

    def validate_email(self, value):
        queryset = User.objects.filter(email__iexact=value)
        if self.instance:
            queryset = queryset.exclude(id=self.instance.id)
        if queryset.exists():
            raise serializers.ValidationError('Este correo electrónico ya está en uso.')
        return value

    def validate(self, attrs):
        role_actual = attrs.get('rol')
        if role_actual is None and self.instance is not None:
            role_actual = self.instance.rol

        if role_actual == 'AUDITOR_INTERNO':
            role_actual = 'AUDITOR'
            attrs['rol'] = role_actual

        if role_actual == 'ADMIN_SISTEMA':
            attrs['empresa'] = None
            attrs['is_approved'] = True
            attrs['es_administrador_empresa'] = False
            return attrs

        flag_admin = attrs.get('es_administrador_empresa')
        if flag_admin is None and self.instance is not None:
            flag_admin = self.instance.es_administrador_empresa

        if role_actual == 'LIDER_EQUIPO':
            attrs['es_administrador_empresa'] = True
            flag_admin = True

        # Compatibilidad: si se marca el flag legado, forzar rol líder.
        if flag_admin is True and role_actual != 'LIDER_EQUIPO':
            attrs['rol'] = 'LIDER_EQUIPO'
            role_actual = 'LIDER_EQUIPO'

        # Si el rol explícito no es líder, apagar flag legado.
        if role_actual in ['EMPLEADO', 'IMPLEMENTADOR', 'AUDITOR', 'CAPACITADOR']:
            attrs['es_administrador_empresa'] = False

        # Un líder de equipo siempre debe estar aprobado.
        if attrs.get('es_administrador_empresa'):
            if attrs.get('is_approved') is False:
                attrs['is_approved'] = True
            elif self.instance is not None and 'is_approved' not in attrs and not self.instance.is_approved:
                attrs['is_approved'] = True
        return attrs

    def create(self, validated_data):
        raw_password = validated_data.pop('password', None) or get_random_string(12)
        user = User.objects.create_user(password=raw_password, **validated_data)
        user._generated_password = raw_password
        return user

    def update(self, instance, validated_data):
        raw_password = validated_data.pop('password', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if raw_password:
            instance.set_password(raw_password)

        instance.save()
        return instance


class UsuarioBitacoraResumenSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'full_name']
        read_only_fields = fields

    def get_full_name(self, obj):
        return obj.get_full_name() or obj.username


class BitacoraSeguridadUsuarioSerializer(serializers.ModelSerializer):
    actor_info = UsuarioBitacoraResumenSerializer(source='actor', read_only=True)
    usuario_objetivo_info = UsuarioBitacoraResumenSerializer(source='usuario_objetivo', read_only=True)
    empresa_info = EmpresaSerializer(source='empresa', read_only=True)
    accion_display = serializers.CharField(source='get_accion_display', read_only=True)

    class Meta:
        model = BitacoraSeguridadUsuario
        fields = [
            'id',
            'accion',
            'accion_display',
            'actor',
            'actor_info',
            'usuario_objetivo',
            'usuario_objetivo_info',
            'empresa',
            'empresa_info',
            'detalle',
            'ip_origen',
            'user_agent',
            'fecha_evento',
        ]
        read_only_fields = fields


class NotificacionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notificacion
        fields = [
            'id',
            'usuario_destino',
            'titulo',
            'mensaje',
            'leida',
            'fecha_creacion',
        ]
        read_only_fields = ['id', 'usuario_destino', 'titulo', 'mensaje', 'fecha_creacion']
