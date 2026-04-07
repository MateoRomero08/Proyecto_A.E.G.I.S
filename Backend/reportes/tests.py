from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from auditoria.models import ProcesoAuditoria, RevisionAuditoria
from capacitacion.models import CursoCapacitacion, ModuloContenido, ProgresoUsuario
from implementacion.models import ControlISO, Empresa, EvaluacionControl
from usuarios.models import BitacoraSeguridadUsuario

User = get_user_model()


class ReportesPDFEndpointsTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.empresa_1 = Empresa.objects.create(nombre='Empresa Uno', tipo='PEQUENA')
        self.empresa_2 = Empresa.objects.create(nombre='Empresa Dos', tipo='MEDIANA')

        self.control_1 = ControlISO.objects.create(
            identificador='5.1',
            nombre='Politica de seguridad',
            dominio='ORGANIZACIONAL',
            descripcion_guia='Control base',
        )
        self.control_2 = ControlISO.objects.create(
            identificador='5.2',
            nombre='Gestion de accesos',
            dominio='TECNOLOGICO',
            descripcion_guia='Control de accesos',
        )

        EvaluacionControl.objects.create(
            empresa=self.empresa_1,
            control=self.control_1,
            estado='IMPLEMENTADO',
        )
        EvaluacionControl.objects.create(
            empresa=self.empresa_1,
            control=self.control_2,
            estado='NO_IMPLEMENTADO',
        )

        self.superuser = User.objects.create_superuser(
            username='root',
            email='root@aegis.com',
            password='Password123!',
        )
        self.lider = User.objects.create_user(
            username='lider_empresa_uno',
            email='lider@empresauno.com',
            password='Password123!',
            rol='LIDER_EQUIPO',
            empresa=self.empresa_1,
            is_approved=True,
            es_administrador_empresa=True,
        )
        self.empleado = User.objects.create_user(
            username='empleado_uno',
            email='empleado@empresauno.com',
            password='Password123!',
            rol='EMPLEADO',
            empresa=self.empresa_1,
            is_approved=True,
        )
        self.auditor = User.objects.create_user(
            username='auditor_uno',
            email='auditor@empresauno.com',
            password='Password123!',
            rol='AUDITOR',
            empresa=self.empresa_1,
            is_approved=True,
        )

        self.curso_tenant = CursoCapacitacion.objects.create(
            titulo='Curso Interno Empresa Uno',
            descripcion='Capacitacion interna',
            empresa=self.empresa_1,
            creado_por_admin=False,
            activo=True,
        )
        self.modulo_tenant = ModuloContenido.objects.create(
            curso=self.curso_tenant,
            titulo='Modulo 1',
            descripcion='Modulo inicial',
            tipo='VIDEO',
            url_recurso='https://example.com/modulo-1',
            orden=1,
        )

        self.progreso_empleado = ProgresoUsuario.objects.create(
            usuario=self.empleado,
            curso=self.curso_tenant,
        )
        self.progreso_empleado.modulos_completados.add(self.modulo_tenant)
        self.progreso_empleado.recalcular_estado()

        self.proceso = ProcesoAuditoria.objects.create(
            nombre='Auditoria Q2',
            empresa=self.empresa_1,
            auditor=self.auditor,
        )

        evaluacion_proceso = EvaluacionControl.objects.get(
            empresa=self.empresa_1,
            control=self.control_1,
        )
        RevisionAuditoria.objects.create(
            proceso=self.proceso,
            evaluacion_control=evaluacion_proceso,
            auditor=self.auditor,
            veredicto='CONFORME',
            observaciones='Correcto',
        )

        BitacoraSeguridadUsuario.objects.create(
            actor=self.superuser,
            usuario_objetivo=self.empleado,
            empresa=self.empresa_1,
            accion='CREACION_USUARIO',
            detalle={'origen': 'test'},
            ip_origen='127.0.0.1',
            user_agent='pytest-agent',
        )

    def _assert_pdf_response(self, response):
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('application/pdf', response['Content-Type'])
        self.assertTrue(response.content.startswith(b'%PDF'))

    def test_lider_cumplimiento_ignora_empresa_id_query(self):
        self.client.force_authenticate(user=self.lider)

        response = self.client.get(f'/api/reportes/cumplimiento/?empresa_id={self.empresa_2.id}')

        self._assert_pdf_response(response)
        self.assertIn('empresa-uno', response['Content-Disposition'])

    def test_superadmin_cumplimiento_requiere_empresa_id(self):
        self.client.force_authenticate(user=self.superuser)

        response = self.client.get('/api/reportes/cumplimiento/')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('empresa_id', response.data)

    def test_superadmin_cumplimiento_con_empresa_id(self):
        self.client.force_authenticate(user=self.superuser)

        response = self.client.get(f'/api/reportes/cumplimiento/?empresa_id={self.empresa_2.id}')

        self._assert_pdf_response(response)
        self.assertIn('empresa-dos', response['Content-Disposition'])

    def test_accesos_restringido_para_empleado(self):
        self.client.force_authenticate(user=self.empleado)

        response = self.client.get('/api/reportes/accesos/')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_forense_solo_superadmin(self):
        self.client.force_authenticate(user=self.lider)
        response_lider = self.client.get('/api/reportes/forense/')
        self.assertEqual(response_lider.status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_authenticate(user=self.superuser)
        response_root = self.client.get('/api/reportes/forense/?limit=25')
        self._assert_pdf_response(response_root)

    def test_certificado_solo_propietario_o_superadmin(self):
        self.client.force_authenticate(user=self.empleado)
        own_response = self.client.get(f'/api/reportes/certificado/{self.progreso_empleado.id}/')
        self._assert_pdf_response(own_response)

        self.client.force_authenticate(user=self.lider)
        forbidden_response = self.client.get(f'/api/reportes/certificado/{self.progreso_empleado.id}/')
        self.assertEqual(forbidden_response.status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_authenticate(user=self.superuser)
        root_response = self.client.get(f'/api/reportes/certificado/{self.progreso_empleado.id}/')
        self._assert_pdf_response(root_response)

    def test_reporte_auditoria_respeta_empresa_resuelta(self):
        self.client.force_authenticate(user=self.lider)
        response_lider = self.client.get(
            f'/api/reportes/auditoria/{self.proceso.id}/?empresa_id={self.empresa_2.id}'
        )
        self._assert_pdf_response(response_lider)

        self.client.force_authenticate(user=self.superuser)
        response_forbidden = self.client.get(
            f'/api/reportes/auditoria/{self.proceso.id}/?empresa_id={self.empresa_2.id}'
        )
        self.assertEqual(response_forbidden.status_code, status.HTTP_404_NOT_FOUND)

    def test_listados_para_front_reportes(self):
        self.client.force_authenticate(user=self.superuser)
        empresas = self.client.get('/api/reportes/empresas/')
        self.assertEqual(empresas.status_code, status.HTTP_200_OK)
        self.assertEqual(len(empresas.data), 2)

        self.client.force_authenticate(user=self.lider)
        empresas_lider = self.client.get('/api/reportes/empresas/')
        self.assertEqual(empresas_lider.status_code, status.HTTP_200_OK)
        self.assertEqual(len(empresas_lider.data), 1)
        self.assertEqual(empresas_lider.data[0]['id'], self.empresa_1.id)

        auditorias_lider = self.client.get('/api/reportes/auditorias/')
        self.assertEqual(auditorias_lider.status_code, status.HTTP_200_OK)
        self.assertEqual(len(auditorias_lider.data), 1)
        self.assertEqual(auditorias_lider.data[0]['id'], self.proceso.id)
