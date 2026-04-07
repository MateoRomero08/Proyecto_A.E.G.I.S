from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ProcesoAuditoriaViewSet,
    RevisionAuditoriaViewSet,
    ListarEvaluacionesAuditoriaView
)

# Router para ViewSets
router = DefaultRouter()
router.register(r'procesos', ProcesoAuditoriaViewSet, basename='proceso-auditoria')
router.register(r'revisiones', RevisionAuditoriaViewSet, basename='revision-auditoria')

app_name = 'auditoria'

urlpatterns = [
    # Router endpoints
    path('', include(router.urls)),
    
    # Vista adicional para listar evaluaciones
    path(
        'evaluaciones/',
        ListarEvaluacionesAuditoriaView.as_view(),
        name='listar_evaluaciones'
    ),
]
