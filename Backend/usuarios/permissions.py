from rest_framework import permissions


def es_admin_sistema(user):
    """Determina si el usuario pertenece al grupo ADMIN_SISTEMA."""
    if not (user and user.is_authenticated and not user.is_superuser):
        return False

    if getattr(user, 'rol', None) == 'ADMIN_SISTEMA':
        return True

    return bool(
        user.groups.filter(name='ADMIN_SISTEMA').exists()
        or user.has_perm('usuarios.manage_global_users')
    )


def es_acceso_global(user):
    """Acceso global para SuperAdmin o ADMIN_SISTEMA."""
    return bool(user and user.is_authenticated and (user.is_superuser or es_admin_sistema(user)))


class IsSuperAdminOrAdminSistema(permissions.BasePermission):
    """
    Permiso global para endpoints compartidos entre SuperAdmin y ADMIN_SISTEMA.
    """
    message = 'Acceso restringido: requiere privilegios globales (SuperAdmin o ADMIN_SISTEMA).'

    def has_permission(self, request, view):
        return es_acceso_global(request.user)


class EsImplementador(permissions.BasePermission):
    """
    Permiso personalizado que solo permite acceso a usuarios con rol IMPLEMENTADOR.
    """
    message = 'Solo los implementadores tienen acceso a esta funcionalidad.'
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.rol == 'IMPLEMENTADOR'


class EsAuditor(permissions.BasePermission):
    """
    Permiso personalizado que solo permite acceso a usuarios con rol AUDITOR.
    """
    message = 'Solo los auditores tienen acceso a esta funcionalidad.'
    
    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.rol in ['AUDITOR', 'AUDITOR_INTERNO']
        )


class PerteneceAMismaEmpresa(permissions.BasePermission):
    """
    Permiso que verifica si el usuario pertenece a la misma empresa del objeto.
    """
    message = 'Solo puedes acceder a recursos de tu propia empresa.'
    
    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Si el usuario es superuser, tiene acceso total
        if request.user.is_superuser:
            return True
        
        # Verificar si el objeto tiene el atributo empresa
        if hasattr(obj, 'empresa'):
            return obj.empresa == request.user.empresa
        
        # Si el objeto es una empresa, verificar si es la empresa del usuario
        if obj.__class__.__name__ == 'Empresa':
            return obj == request.user.empresa
        
        return False


class PuedeEditarEvaluaciones(permissions.BasePermission):
    """
    Permiso que permite a los implementadores editar evaluaciones de su empresa
    y a los auditores solo visualizar.
    """
    message = 'No tienes permisos para editar esta evaluación.'
    
    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Superusers tienen acceso completo
        if request.user.is_superuser:
            return True
        
        # Los auditores solo pueden leer (GET, HEAD, OPTIONS)
        if request.user.rol in ['AUDITOR', 'AUDITOR_INTERNO']:
            return request.method in permissions.SAFE_METHODS
        
        # Los implementadores pueden editar solo de su empresa
        if request.user.rol == 'IMPLEMENTADOR':
            if hasattr(obj, 'empresa'):
                return obj.empresa == request.user.empresa
        
        return False


class IsApprovedUser(permissions.BasePermission):
    """
    Permiso global para bloquear acceso a usuarios pendientes de aprobación.
    """
    message = 'Tu cuenta está pendiente de aprobación por el administrador de tu empresa.'

    def has_permission(self, request, view):
        user = request.user

        if not user or not user.is_authenticated:
            return False

        if user.is_superuser:
            return True

        return bool(getattr(user, 'is_approved', False))


class IsSuperAdminOnly(permissions.BasePermission):
    """
    Permiso estricto para operaciones globales de infraestructura.
    Solo superusuarios pueden acceder.
    """
    message = 'Acceso restringido: solo superusuarios pueden usar este endpoint.'

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and user.is_superuser)
