from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    EmpresaViewSet,
    ControlISOViewSet,
    EvaluacionControlViewSet,
    EvidenciaViewSet
)

router = DefaultRouter()
router.register(r'empresas', EmpresaViewSet, basename='empresa')
router.register(r'controles', ControlISOViewSet, basename='controliso')
router.register(r'evaluaciones', EvaluacionControlViewSet, basename='evaluacioncontrol')
router.register(r'evidencias', EvidenciaViewSet, basename='evidencia')

urlpatterns = [
    path('', include(router.urls)),
]
