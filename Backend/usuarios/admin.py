from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import UsuarioCustom, BitacoraSeguridadUsuario, Notificacion


@admin.register(UsuarioCustom)
class UsuarioCustomAdmin(UserAdmin):
    """
    Configuración del administrador para el modelo UsuarioCustom.
    Extiende UserAdmin para incluir los campos personalizados.
    """
    
    # Campos a mostrar en la lista de usuarios
    list_display = ('username', 'email', 'first_name', 'last_name', 'rol', 'empresa', 'is_staff', 'is_active')
    list_filter = ('rol', 'empresa', 'is_staff', 'is_active', 'is_superuser')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('-date_joined',)
    
    # Configuración de los fieldsets para el formulario de edición
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Información Personal', {'fields': ('first_name', 'last_name', 'email', 'foto_perfil')}),
        ('Permisos y Rol', {
            'fields': ('rol', 'empresa', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
            'description': 'Configure el rol y la empresa del usuario, así como los permisos básicos.'
        }),
        ('Fechas Importantes', {'fields': ('last_login', 'date_joined')}),
    )
    
    # Configuración de los fieldsets para el formulario de creación
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'rol', 'empresa', 'is_staff', 'is_active'),
        }),
    )
    
    # Campos de solo lectura
    readonly_fields = ('last_login', 'date_joined')
    
    # Filtros horizontales para grupos y permisos (mejor UX)
    filter_horizontal = ('groups', 'user_permissions')
    
    def get_queryset(self, request):
        """Optimiza las consultas incluyendo la relación con empresa"""
        qs = super().get_queryset(request)
        return qs.select_related('empresa')


@admin.register(BitacoraSeguridadUsuario)
class BitacoraSeguridadUsuarioAdmin(admin.ModelAdmin):
    """Vista de consulta para eventos críticos de seguridad de usuarios."""

    list_display = (
        'fecha_evento',
        'accion',
        'actor',
        'usuario_objetivo',
        'empresa',
        'ip_origen',
    )
    list_filter = ('accion', 'empresa', 'fecha_evento')
    search_fields = (
        'actor__username',
        'actor__email',
        'usuario_objetivo__username',
        'usuario_objetivo__email',
        'empresa__nombre',
        'ip_origen',
    )
    readonly_fields = (
        'actor',
        'usuario_objetivo',
        'empresa',
        'accion',
        'detalle',
        'ip_origen',
        'user_agent',
        'fecha_evento',
    )
    ordering = ('-fecha_evento',)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Notificacion)
class NotificacionAdmin(admin.ModelAdmin):
    list_display = ('fecha_creacion', 'usuario_destino', 'titulo', 'leida')
    list_filter = ('leida', 'fecha_creacion')
    search_fields = ('usuario_destino__username', 'usuario_destino__email', 'titulo', 'mensaje')
    readonly_fields = ('usuario_destino', 'titulo', 'mensaje', 'fecha_creacion')
    ordering = ('-fecha_creacion',)
