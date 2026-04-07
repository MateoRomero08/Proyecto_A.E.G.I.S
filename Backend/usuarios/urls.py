from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    RegistroView,
    LogoutView,
    PerfilView,
    ActualizarPerfilView,
    CambiarPasswordView,
    ListarUsuariosPorEmpresaView,
    GestionEquipoView,
    AprobarMiembroEquipoView,
    RechazarMiembroEquipoView,
    GlobalUserViewSet,
    BitacoraSeguridadUsuarioListView,
    AegisTokenObtainPairView,
    NotificacionViewSet,
)

app_name = 'usuarios'

router = DefaultRouter()
router.register(r'global', GlobalUserViewSet, basename='usuarios-global')
router.register(r'notificaciones', NotificacionViewSet, basename='usuarios-notificaciones')

urlpatterns = [
    # Autenticación
    path('registro/', RegistroView.as_view(), name='registro'),
    path('login/', AegisTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'), # <-- Nueva para renovar token
    path('logout/', LogoutView.as_view(), name='logout'),
    
    # Perfil
    path('perfil/', PerfilView.as_view(), name='perfil'),
    path('perfil/actualizar/', ActualizarPerfilView.as_view(), name='actualizar_perfil'),
    path('cambiar-password/', CambiarPasswordView.as_view(), name='cambiar_password'),
    
    # Usuarios de la empresa
    path('empresa/', ListarUsuariosPorEmpresaView.as_view(), name='usuarios_empresa'),
    path('equipo/', GestionEquipoView.as_view(), name='gestion_equipo'),
    path('equipo/<int:user_id>/aprobar/', AprobarMiembroEquipoView.as_view(), name='aprobar_miembro_equipo'),
    path('equipo/<int:user_id>/rechazar/', RechazarMiembroEquipoView.as_view(), name='rechazar_miembro_equipo'),
    path('bitacora/', BitacoraSeguridadUsuarioListView.as_view(), name='bitacora_usuarios'),
    path('', include(router.urls)),
]
