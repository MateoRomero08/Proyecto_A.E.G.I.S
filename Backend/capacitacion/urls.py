from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import CursoCapacitacionViewSet, ModuloContenidoViewSet, ProgresoUsuarioViewSet

router = DefaultRouter()
router.register(r'cursos', CursoCapacitacionViewSet, basename='curso-capacitacion')
router.register(r'modulos', ModuloContenidoViewSet, basename='modulo-contenido')
router.register(r'progresos', ProgresoUsuarioViewSet, basename='progreso-usuario')

urlpatterns = [
    path('', include(router.urls)),
]
