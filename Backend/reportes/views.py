from io import BytesIO

from django.contrib.auth import get_user_model
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.template.loader import get_template
from django.utils import timezone
from django.utils.text import slugify
from rest_framework import permissions, status
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView
from xhtml2pdf import pisa

from auditoria.models import ProcesoAuditoria
from capacitacion.models import ProgresoUsuario
from implementacion.models import ControlISO, Empresa, EvaluacionControl
from usuarios.models import BitacoraSeguridadUsuario
from usuarios.permissions import IsApprovedUser, IsSuperAdminOnly

User = get_user_model()


def _nombre_usuario(user):
    return (user.get_full_name() or user.username or '').strip() or 'Usuario'


def _build_pdf_response(template_name, context, filename):
    template = get_template(template_name)
    html = template.render(context)

    output = BytesIO()
    pdf_status = pisa.CreatePDF(html, dest=output, encoding='utf-8')
    if pdf_status.err:
        raise ValidationError({'detail': 'No fue posible generar el PDF solicitado.'})

    response = HttpResponse(output.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


class TenantReportMixin:
    permission_classes = [permissions.IsAuthenticated, IsApprovedUser]

    def _es_lider_equipo(self, user):
        return bool(
            getattr(user, 'rol', None) == 'LIDER_EQUIPO'
            or getattr(user, 'es_administrador_empresa', False)
        )

    def _resolver_empresa(self, request):
        user = request.user

        if user.is_superuser:
            empresa_id = request.query_params.get('empresa_id', '').strip()
            if not empresa_id:
                raise ValidationError({'empresa_id': 'Debes enviar ?empresa_id=<id> para generar este reporte.'})

            if not empresa_id.isdigit():
                raise ValidationError({'empresa_id': 'El parametro empresa_id debe ser numerico.'})

            return get_object_or_404(Empresa, id=int(empresa_id))

        if self._es_lider_equipo(user):
            if not user.empresa_id:
                raise PermissionDenied('Tu cuenta no tiene empresa asociada para generar reportes.')
            return user.empresa

        raise PermissionDenied('Solo SuperAdmin o Lider de Equipo pueden exportar este reporte.')

    def _filename(self, prefix, empresa=None):
        company_chunk = ''
        if empresa is not None:
            company_chunk = f"-{slugify(empresa.nombre) or empresa.id}"
        timestamp = timezone.localtime().strftime('%Y%m%d-%H%M')
        return f'{prefix}{company_chunk}-{timestamp}.pdf'


class EmpresasReportesView(APIView):
    """
    Lista de empresas para el modulo de reportes.
    - SuperAdmin: todas las empresas
    - Lider de equipo: solo su empresa
    """

    permission_classes = [permissions.IsAuthenticated, IsApprovedUser]

    def get(self, request):
        user = request.user

        if user.is_superuser:
            queryset = Empresa.objects.all().order_by('nombre')
        elif getattr(user, 'rol', None) == 'LIDER_EQUIPO' or getattr(user, 'es_administrador_empresa', False):
            if not user.empresa_id:
                return Response([], status=status.HTTP_200_OK)
            queryset = Empresa.objects.filter(id=user.empresa_id)
        else:
            raise PermissionDenied('No tienes permisos para consultar empresas de reportes.')

        data = [
            {
                'id': empresa.id,
                'nombre': empresa.nombre,
                'tipo': empresa.tipo,
            }
            for empresa in queryset
        ]
        return Response(data, status=status.HTTP_200_OK)


class AuditoriasDisponiblesReportesView(TenantReportMixin, APIView):
    """
    Lista de auditorias disponibles para descarga de PDF.
    Respeta aislamiento por empresa en base al rol.
    """

    def get(self, request):
        empresa = self._resolver_empresa(request)

        auditorias = (
            ProcesoAuditoria.objects.filter(empresa=empresa)
            .select_related('empresa', 'auditor')
            .order_by('-fecha_creacion')[:200]
        )

        data = [
            {
                'id': proceso.id,
                'nombre': proceso.nombre,
                'estado': proceso.estado,
                'fecha_creacion': proceso.fecha_creacion,
                'fecha_cierre': proceso.fecha_cierre,
                'auditor_nombre': _nombre_usuario(proceso.auditor),
                'empresa_nombre': proceso.empresa.nombre,
            }
            for proceso in auditorias
        ]
        return Response(data, status=status.HTTP_200_OK)


class ReporteCumplimientoPDFView(TenantReportMixin, APIView):
    def get(self, request):
        empresa = self._resolver_empresa(request)

        total_controles = ControlISO.objects.count()
        controles_implementados_ids = set(
            EvaluacionControl.objects.filter(
                empresa=empresa,
                estado='IMPLEMENTADO',
            ).values_list('control_id', flat=True)
        )
        controles_implementados = len(controles_implementados_ids)
        porcentaje = round((controles_implementados / total_controles) * 100, 2) if total_controles else 0

        controles_pendientes = list(
            ControlISO.objects.exclude(id__in=controles_implementados_ids)
            .order_by('identificador')
            .values('identificador', 'nombre', 'dominio')
        )

        context = {
            'empresa': empresa,
            'fecha_corte': timezone.localtime(),
            'total_controles': total_controles,
            'controles_implementados': controles_implementados,
            'controles_pendientes_total': len(controles_pendientes),
            'porcentaje_cumplimiento': porcentaje,
            'controles_pendientes': controles_pendientes,
        }

        filename = self._filename('reporte-cumplimiento-iso', empresa)
        return _build_pdf_response('reportes/cumplimiento_iso.html', context, filename)


class ReporteAccesosPDFView(TenantReportMixin, APIView):
    def get(self, request):
        empresa = self._resolver_empresa(request)

        usuarios = User.objects.filter(empresa=empresa).order_by('last_name', 'first_name', 'username')
        matriz = []
        activos = 0

        for usuario in usuarios:
            estado = 'Activo' if usuario.is_active and usuario.is_approved else 'Pendiente'
            if estado == 'Activo':
                activos += 1

            matriz.append(
                {
                    'nombre': _nombre_usuario(usuario),
                    'username': usuario.username,
                    'email': usuario.email,
                    'rol': usuario.get_rol_display() if hasattr(usuario, 'get_rol_display') else usuario.rol,
                    'estado': estado,
                }
            )

        context = {
            'empresa': empresa,
            'fecha_corte': timezone.localtime(),
            'filas': matriz,
            'total_usuarios': len(matriz),
            'usuarios_activos': activos,
            'usuarios_pendientes': max(len(matriz) - activos, 0),
        }

        filename = self._filename('reporte-matriz-accesos-a9', empresa)
        return _build_pdf_response('reportes/matriz_accesos.html', context, filename)


class ReporteAuditoriaPDFView(TenantReportMixin, APIView):
    def get(self, request, id_auditoria):
        empresa = self._resolver_empresa(request)

        proceso = get_object_or_404(
            ProcesoAuditoria.objects.select_related('empresa', 'auditor').prefetch_related(
                'revisiones__evaluacion_control__control'
            ),
            id=id_auditoria,
            empresa=empresa,
        )

        revisiones = (
            proceso.revisiones.select_related('evaluacion_control__control')
            .all()
            .order_by('evaluacion_control__control__identificador')
        )

        filas = [
            {
                'control': revision.evaluacion_control.control.identificador,
                'control_nombre': revision.evaluacion_control.control.nombre,
                'veredicto': revision.veredicto,
                'estado_snapshot': revision.estado_implementacion_snapshot or '-',
                'observaciones': (revision.observaciones or '-').strip() or '-',
                'fecha_revision': timezone.localtime(revision.fecha_revision),
            }
            for revision in revisiones
        ]

        context = {
            'empresa': empresa,
            'proceso': proceso,
            'auditor_nombre': _nombre_usuario(proceso.auditor),
            'fecha_corte': timezone.localtime(),
            'total_revisiones': len(filas),
            'progreso': proceso.progreso_porcentaje(),
            'filas': filas,
        }

        filename = self._filename(f'reporte-auditoria-{proceso.id}', empresa)
        return _build_pdf_response('reportes/auditoria_detalle.html', context, filename)


class ReporteForensePDFView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsSuperAdminOnly]

    def get(self, request):
        limit_raw = request.query_params.get('limit', '120').strip()
        if limit_raw and not limit_raw.isdigit():
            raise ValidationError({'limit': 'El parametro limit debe ser numerico.'})

        limit = int(limit_raw or 120)
        limit = max(10, min(limit, 500))

        eventos = (
            BitacoraSeguridadUsuario.objects.select_related('actor', 'usuario_objetivo', 'empresa')
            .all()
            .order_by('-fecha_evento')[:limit]
        )

        filas = []
        for evento in eventos:
            filas.append(
                {
                    'fecha_evento': timezone.localtime(evento.fecha_evento),
                    'accion': evento.get_accion_display(),
                    'actor': _nombre_usuario(evento.actor) if evento.actor else 'Sistema/Anonimo',
                    'usuario_objetivo': _nombre_usuario(evento.usuario_objetivo) if evento.usuario_objetivo else '-',
                    'empresa': evento.empresa.nombre if evento.empresa else '-',
                    'ip_origen': evento.ip_origen or '-',
                }
            )

        context = {
            'fecha_corte': timezone.localtime(),
            'limite': limit,
            'total_eventos': len(filas),
            'filas': filas,
        }

        timestamp = timezone.localtime().strftime('%Y%m%d-%H%M')
        filename = f'reporte-forense-worm-aegis-{timestamp}.pdf'
        return _build_pdf_response('reportes/forense_worm.html', context, filename)


class ReporteCertificadoCapacitacionPDFView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsApprovedUser]

    def get(self, request, id_progreso):
        progreso = get_object_or_404(
            ProgresoUsuario.objects.select_related('usuario', 'curso', 'usuario__empresa'),
            id=id_progreso,
        )

        user = request.user
        if not user.is_superuser and progreso.usuario_id != user.id:
            raise PermissionDenied('Solo puedes descargar certificados de tus propios cursos completados.')

        if not progreso.curso_completado:
            raise ValidationError({'detail': 'El curso todavia no esta completado al 100%.'})

        fecha_certificado = progreso.fecha_completado or progreso.fecha_ultima_actividad or timezone.now()
        usuario_certificado = progreso.usuario

        context = {
            'nombre_usuario': _nombre_usuario(usuario_certificado),
            'empresa_nombre': usuario_certificado.empresa.nombre if usuario_certificado.empresa else 'Sin empresa',
            'curso_titulo': progreso.curso.titulo,
            'fecha_certificado': timezone.localtime(fecha_certificado),
            'fecha_emision': timezone.localtime(),
            'progreso': progreso,
        }

        timestamp = timezone.localtime().strftime('%Y%m%d')
        filename = (
            f"certificado-{slugify(_nombre_usuario(usuario_certificado))}-"
            f"{slugify(progreso.curso.titulo)}-{timestamp}.pdf"
        )
        return _build_pdf_response('reportes/certificado_capacitacion.html', context, filename)
