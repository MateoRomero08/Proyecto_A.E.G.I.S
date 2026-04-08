from django.urls import path

from .views import (
    EmpresasReportesView,
    AuditoriasDisponiblesReportesView,
    UsuariosCapacitacionReportesView,
    ReporteAccesosPDFView,
    ReporteAuditoriaPDFView,
    ReporteCapacitacionUsuarioPDFView,
    ReporteCertificadoCapacitacionPDFView,
    ReporteCumplimientoPDFView,
    ReporteForensePDFView,
)

app_name = 'reportes'

urlpatterns = [
    path('empresas/', EmpresasReportesView.as_view(), name='empresas'),
    path('auditorias/', AuditoriasDisponiblesReportesView.as_view(), name='auditorias'),
    path('cumplimiento/', ReporteCumplimientoPDFView.as_view(), name='cumplimiento'),
    path('auditoria/<int:id_auditoria>/', ReporteAuditoriaPDFView.as_view(), name='auditoria'),
    path('accesos/', ReporteAccesosPDFView.as_view(), name='accesos'),
    path('capacitacion/usuarios/', UsuariosCapacitacionReportesView.as_view(), name='capacitacion-usuarios'),
    path('capacitacion/usuario/<int:id_usuario>/', ReporteCapacitacionUsuarioPDFView.as_view(), name='capacitacion-usuario'),
    path('forense/', ReporteForensePDFView.as_view(), name='forense'),
    path('certificado/<int:id_progreso>/', ReporteCertificadoCapacitacionPDFView.as_view(), name='certificado'),
]
