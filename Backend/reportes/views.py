from io import BytesIO

from django.contrib.auth import get_user_model
from django.db.models import Count, Q
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
from capacitacion.models import CursoCapacitacion, ModuloContenido, ProgresoUsuario
from implementacion.models import ControlISO, Empresa, EvaluacionControl
from usuarios.models import BitacoraSeguridadUsuario
from usuarios.permissions import (
    IsApprovedUser,
    IsSuperAdminOrAdminSistema,
    es_acceso_global,
)

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

    def _validar_acceso_reportes(self, user):
        if es_acceso_global(user):
            return

        if self._es_lider_equipo(user):
            return

        raise PermissionDenied('Solo lideres de equipo y perfiles globales pueden generar reportes.')

    def _cursos_visibles_empresa_queryset(self, empresa):
        return (
            CursoCapacitacion.objects.filter(activo=True)
            .filter(
                Q(creado_por_admin=True, empresa__isnull=True)
                | Q(creado_por_admin=False, empresa=empresa)
            )
            .distinct()
        )

    def _resolver_empresa(self, request):
        user = request.user
        self._validar_acceso_reportes(user)

        if es_acceso_global(user):
            empresa_id = request.query_params.get('empresa_id', '').strip()
            if not empresa_id:
                raise ValidationError({'empresa_id': 'Debes enviar ?empresa_id=<id> para generar este reporte.'})

            if not empresa_id.isdigit():
                raise ValidationError({'empresa_id': 'El parametro empresa_id debe ser numerico.'})

            return get_object_or_404(Empresa, id=int(empresa_id))

        if not user.empresa_id:
            raise PermissionDenied('Tu cuenta no tiene empresa asociada para generar reportes.')

        return user.empresa

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

    def _es_lider_equipo(self, user):
        return bool(
            getattr(user, 'rol', None) == 'LIDER_EQUIPO'
            or getattr(user, 'es_administrador_empresa', False)
        )

    def get(self, request):
        user = request.user

        if es_acceso_global(user):
            queryset = Empresa.objects.all().order_by('nombre')
        else:
            if not self._es_lider_equipo(user):
                raise PermissionDenied('Solo lideres de equipo y perfiles globales pueden acceder a reportes.')

            if not user.empresa_id:
                return Response([], status=status.HTTP_200_OK)
            queryset = Empresa.objects.filter(id=user.empresa_id)

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


class UsuariosCapacitacionReportesView(TenantReportMixin, APIView):
    """
    Lista avance de capacitación por usuario para la empresa resuelta.
    """

    def get(self, request):
        empresa = self._resolver_empresa(request)
        cursos_visibles_qs = self._cursos_visibles_empresa_queryset(empresa)
        total_cursos_asignados = cursos_visibles_qs.count()
        total_modulos_disponibles = ModuloContenido.objects.filter(
            curso__in=cursos_visibles_qs,
            activo=True,
        ).count()

        usuarios = (
            User.objects.filter(empresa=empresa, is_active=True)
            .order_by('last_name', 'first_name', 'username')
        )

        agregados_progreso = {
            fila['usuario_id']: fila
            for fila in ProgresoUsuario.objects.filter(
                usuario__empresa=empresa,
                curso__in=cursos_visibles_qs,
            )
            .values('usuario_id')
            .annotate(
                cursos_completados=Count('curso_id', filter=Q(curso_completado=True), distinct=True),
                cursos_en_progreso=Count(
                    'curso_id',
                    filter=Q(porcentaje_completado__gt=0, curso_completado=False),
                    distinct=True,
                ),
                modulos_completados=Count('modulos_completados', distinct=True),
            )
        }

        data = []
        for usuario in usuarios:
            agregado = agregados_progreso.get(usuario.id, {})
            cursos_completados = int(agregado.get('cursos_completados', 0) or 0)
            cursos_en_progreso = int(agregado.get('cursos_en_progreso', 0) or 0)
            cursos_pendientes = max(total_cursos_asignados - cursos_completados - cursos_en_progreso, 0)
            porcentaje_global = (
                round((cursos_completados / total_cursos_asignados) * 100, 2)
                if total_cursos_asignados
                else 0
            )

            data.append(
                {
                    'id': usuario.id,
                    'username': usuario.username,
                    'nombre': _nombre_usuario(usuario),
                    'email': usuario.email,
                    'rol': usuario.get_rol_display() if hasattr(usuario, 'get_rol_display') else usuario.rol,
                    'cursos_asignados': total_cursos_asignados,
                    'cursos_completados': cursos_completados,
                    'cursos_en_progreso': cursos_en_progreso,
                    'cursos_pendientes': cursos_pendientes,
                    'porcentaje_global': porcentaje_global,
                    'modulos_completados': int(agregado.get('modulos_completados', 0) or 0),
                    'total_modulos_disponibles': total_modulos_disponibles,
                }
            )

        return Response(data, status=status.HTTP_200_OK)


class ReporteCapacitacionUsuarioPDFView(TenantReportMixin, APIView):
    """
    Genera PDF de avance de capacitación por usuario para la empresa resuelta.
    """

    def get(self, request, id_usuario):
        empresa = self._resolver_empresa(request)
        usuario_objetivo = get_object_or_404(
            User.objects.select_related('empresa'),
            id=id_usuario,
            empresa=empresa,
            is_active=True,
        )

        cursos_visibles_qs = self._cursos_visibles_empresa_queryset(empresa).prefetch_related('modulos')
        cursos_visibles = list(cursos_visibles_qs)

        progresos_qs = ProgresoUsuario.objects.filter(
            usuario=usuario_objetivo,
            curso__in=cursos_visibles_qs,
        ).prefetch_related('modulos_completados')
        progreso_por_curso_id = {progreso.curso_id: progreso for progreso in progresos_qs}

        filas = []
        cursos_completados = 0
        cursos_en_progreso = 0
        total_modulos = 0
        total_modulos_completados = 0

        for curso in cursos_visibles:
            progreso = progreso_por_curso_id.get(curso.id)
            total_modulos_curso = sum(1 for modulo in curso.modulos.all() if modulo.activo)
            total_modulos += total_modulos_curso

            if progreso:
                modulos_completados = progreso.modulos_completados.filter(curso=curso, activo=True).count()
                porcentaje = progreso.porcentaje_completado
                completado = progreso.curso_completado
                fecha_completado = progreso.fecha_completado
            else:
                modulos_completados = 0
                porcentaje = 0
                completado = False
                fecha_completado = None

            total_modulos_completados += modulos_completados

            if completado:
                estado = 'Completado'
                cursos_completados += 1
            elif porcentaje > 0:
                estado = 'En progreso'
                cursos_en_progreso += 1
            else:
                estado = 'Pendiente'

            filas.append(
                {
                    'curso_titulo': curso.titulo,
                    'alcance': 'Oficial Aegis' if curso.creado_por_admin else f'Interno {empresa.nombre}',
                    'estado': estado,
                    'porcentaje': porcentaje,
                    'modulos_completados': modulos_completados,
                    'total_modulos': total_modulos_curso,
                    'fecha_completado': timezone.localtime(fecha_completado) if fecha_completado else None,
                }
            )

        total_cursos = len(filas)
        cursos_pendientes = max(total_cursos - cursos_completados - cursos_en_progreso, 0)
        porcentaje_global = round((cursos_completados / total_cursos) * 100, 2) if total_cursos else 0

        context = {
            'empresa': empresa,
            'usuario_objetivo': usuario_objetivo,
            'fecha_corte': timezone.localtime(),
            'total_cursos': total_cursos,
            'cursos_completados': cursos_completados,
            'cursos_en_progreso': cursos_en_progreso,
            'cursos_pendientes': cursos_pendientes,
            'porcentaje_global': porcentaje_global,
            'total_modulos': total_modulos,
            'total_modulos_completados': total_modulos_completados,
            'filas': filas,
        }

        filename = self._filename(f'reporte-capacitacion-{slugify(usuario_objetivo.username)}', empresa)
        return _build_pdf_response('reportes/capacitacion_usuario.html', context, filename)


class ReporteForensePDFView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsSuperAdminOrAdminSistema]

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
