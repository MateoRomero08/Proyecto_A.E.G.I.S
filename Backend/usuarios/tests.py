from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management import call_command
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from capacitacion.models import CursoCapacitacion, ModuloContenido, ProgresoUsuario
from implementacion.models import ControlISO, Empresa, EvaluacionControl

User = get_user_model()


class RegistroInteligenteRolTestCase(TestCase):
	def setUp(self):
		self.client = APIClient()
		self.url = '/api/usuarios/registro/'

	def _payload(self, username, email, nombre_empresa, rol='IMPLEMENTADOR'):
		return {
			'username': username,
			'email': email,
			'first_name': 'Nombre',
			'last_name': 'Apellido',
			'password': 'Password123!',
			'password_confirm': 'Password123!',
			'nombre_empresa': nombre_empresa,
			'rol': rol,
		}

	def test_primer_usuario_empresa_nueva_es_lider_equipo(self):
		response = self.client.post(
			self.url,
			self._payload('juan_lider', 'juan@tecnobot.com', 'TecnoBot'),
			format='json',
		)

		self.assertEqual(response.status_code, status.HTTP_201_CREATED)

		usuario = User.objects.get(username='juan_lider')
		self.assertEqual(usuario.rol, 'LIDER_EQUIPO')
		self.assertTrue(usuario.is_approved)
		self.assertTrue(usuario.es_administrador_empresa)
		self.assertEqual(Empresa.objects.filter(nombre='TecnoBot').count(), 1)

	def test_usuario_en_empresa_existente_queda_empleado_pendiente(self):
		# Primer registro crea empresa y liderazgo.
		self.client.post(
			self.url,
			self._payload('juan_lider', 'juan@tecnobot.com', 'TecnoBot'),
			format='json',
		)

		response = self.client.post(
			self.url,
			self._payload('maria_emp', 'maria@tecnobot.com', 'TecnoBot', rol='AUDITOR'),
			format='json',
		)

		self.assertEqual(response.status_code, status.HTTP_201_CREATED)

		maria = User.objects.get(username='maria_emp')
		self.assertEqual(maria.rol, 'EMPLEADO')
		self.assertFalse(maria.is_approved)
		self.assertFalse(maria.es_administrador_empresa)
		self.assertTrue(maria.is_active)

	def test_rol_enviado_por_cliente_se_ignora_en_empresa_existente(self):
		self.client.post(
			self.url,
			self._payload('primer_lider', 'lider@empresa.com', 'EmpresaX'),
			format='json',
		)

		# Intenta autoasignarse un rol privilegiado en empresa existente.
		response = self.client.post(
			self.url,
			self._payload('intruso', 'intruso@empresa.com', 'EmpresaX', rol='LIDER_EQUIPO'),
			format='json',
		)

		self.assertEqual(response.status_code, status.HTTP_201_CREATED)

		usuario = User.objects.get(username='intruso')
		self.assertEqual(usuario.rol, 'EMPLEADO')
		self.assertFalse(usuario.is_approved)
		self.assertFalse(usuario.es_administrador_empresa)


class DashboardStatsViewTestCase(TestCase):
	def setUp(self):
		self.client = APIClient()
		self.url = '/api/dashboard/stats/'

		self.empresa = Empresa.objects.create(nombre='Empresa Uno', tipo='PEQUENA')
		self.otra_empresa = Empresa.objects.create(nombre='Empresa Dos', tipo='MEDIANA')

		self.control_1 = ControlISO.objects.create(
			identificador='5.1',
			nombre='Politica de seguridad',
			dominio='ORGANIZACIONAL',
			descripcion_guia='Control de politica',
		)
		self.control_2 = ControlISO.objects.create(
			identificador='5.2',
			nombre='Gestión de accesos',
			dominio='TECNOLOGICO',
			descripcion_guia='Control de accesos',
		)
		self.control_3 = ControlISO.objects.create(
			identificador='5.3',
			nombre='Continuidad',
			dominio='ORGANIZACIONAL',
			descripcion_guia='Control de continuidad',
		)

		EvaluacionControl.objects.create(
			empresa=self.empresa,
			control=self.control_1,
			estado='IMPLEMENTADO',
		)
		EvaluacionControl.objects.create(
			empresa=self.empresa,
			control=self.control_2,
			estado='EN_PROCESO',
		)
		EvaluacionControl.objects.create(
			empresa=self.empresa,
			control=self.control_3,
			estado='NO_APLICA',
		)

		self.curso_global_activo = CursoCapacitacion.objects.create(
			titulo='Curso Oficial Aegis',
			descripcion='Global activo',
			empresa=None,
			creado_por_admin=True,
			activo=True,
		)
		CursoCapacitacion.objects.create(
			titulo='Curso Global Inactivo',
			descripcion='No debe contar como activo',
			empresa=None,
			creado_por_admin=True,
			activo=False,
		)
		self.curso_empresa_activo = CursoCapacitacion.objects.create(
			titulo='Curso Interno Empresa Uno',
			descripcion='Tenant activo',
			empresa=self.empresa,
			creado_por_admin=False,
			activo=True,
		)
		CursoCapacitacion.objects.create(
			titulo='Curso Empresa Dos',
			descripcion='No debe ser visible para empresa uno',
			empresa=self.otra_empresa,
			creado_por_admin=False,
			activo=True,
		)

		self.modulo_global_1 = ModuloContenido.objects.create(
			curso=self.curso_global_activo,
			titulo='Modulo Global 1',
			tipo='VIDEO',
			url_recurso='https://example.com/global-1',
			orden=1,
		)
		self.modulo_global_2 = ModuloContenido.objects.create(
			curso=self.curso_global_activo,
			titulo='Modulo Global 2',
			tipo='PDF',
			url_recurso='https://example.com/global-2',
			orden=2,
		)
		self.modulo_empresa_1 = ModuloContenido.objects.create(
			curso=self.curso_empresa_activo,
			titulo='Modulo Tenant 1',
			tipo='VIDEO',
			url_recurso='https://example.com/tenant-1',
			orden=1,
		)
		self.modulo_empresa_2 = ModuloContenido.objects.create(
			curso=self.curso_empresa_activo,
			titulo='Modulo Tenant 2',
			tipo='CUESTIONARIO',
			url_recurso='https://example.com/tenant-2',
			orden=2,
		)

		self.superuser = User.objects.create_superuser(
			username='superadmin',
			email='superadmin@aegis.com',
			password='Password123!',
		)

		self.lider = User.objects.create_user(
			username='lider',
			email='lider@empresa1.com',
			password='Password123!',
			rol='LIDER_EQUIPO',
			empresa=self.empresa,
			is_approved=True,
			es_administrador_empresa=True,
		)
		self.implementador = User.objects.create_user(
			username='implementador',
			email='implementador@empresa1.com',
			password='Password123!',
			rol='IMPLEMENTADOR',
			empresa=self.empresa,
			is_approved=True,
		)
		self.auditor = User.objects.create_user(
			username='auditor',
			email='auditor@empresa1.com',
			password='Password123!',
			rol='AUDITOR',
			empresa=self.empresa,
			is_approved=True,
		)
		self.empleado = User.objects.create_user(
			username='empleado',
			email='empleado@empresa1.com',
			password='Password123!',
			rol='EMPLEADO',
			empresa=self.empresa,
			is_approved=True,
		)
		self.capacitador = User.objects.create_user(
			username='capacitador',
			email='capacitador@empresa1.com',
			password='Password123!',
			rol='CAPACITADOR',
			empresa=self.empresa,
			is_approved=True,
		)

		progreso_global = ProgresoUsuario.objects.create(
			usuario=self.empleado,
			curso=self.curso_global_activo,
		)
		progreso_global.modulos_completados.add(self.modulo_global_1, self.modulo_global_2)
		progreso_global.recalcular_estado()

		progreso_tenant = ProgresoUsuario.objects.create(
			usuario=self.empleado,
			curso=self.curso_empresa_activo,
		)
		progreso_tenant.modulos_completados.add(self.modulo_empresa_1)
		progreso_tenant.recalcular_estado()

	def test_superadmin_recibe_metricas_globales(self):
		self.client.force_authenticate(user=self.superuser)
		response = self.client.get(self.url)

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertEqual(response.data['scope'], 'SUPERADMIN')
		self.assertEqual(response.data['total_empresas'], 2)
		self.assertEqual(response.data['total_usuarios'], 6)
		self.assertEqual(response.data['total_cursos_globales'], 2)

	def test_roles_iso_reciben_metricas_empresa(self):
		for usuario in [self.lider, self.implementador, self.auditor]:
			with self.subTest(rol=usuario.rol):
				self.client.force_authenticate(user=usuario)
				response = self.client.get(self.url)

				self.assertEqual(response.status_code, status.HTTP_200_OK)
				self.assertEqual(response.data['scope'], 'EMPRESA_ISO')
				self.assertAlmostEqual(float(response.data['porcentaje_cumplimiento_iso']), 50.0, places=2)
				self.assertEqual(response.data['controles_en_proceso'], 1)
				self.assertEqual(response.data['controles_pendientes'], 0)
				self.assertEqual(response.data['cursos_activos'], 2)

	def test_roles_capacitacion_reciben_metricas_personales(self):
		expectativas = {
			self.empleado.username: {'pendientes': 1, 'modulos': 3},
			self.capacitador.username: {'pendientes': 2, 'modulos': 0},
		}

		for usuario in [self.empleado, self.capacitador]:
			with self.subTest(rol=usuario.rol):
				self.client.force_authenticate(user=usuario)
				response = self.client.get(self.url)

				esperado = expectativas[usuario.username]
				self.assertEqual(response.status_code, status.HTTP_200_OK)
				self.assertEqual(response.data['scope'], 'EMPRESA_ISO')
				self.assertEqual(response.data['mis_cursos_pendientes'], esperado['pendientes'])
				self.assertEqual(response.data['mis_modulos_completados'], esperado['modulos'])


class PermisosPayloadUsuarioTestCase(TestCase):
	def setUp(self):
		self.client = APIClient()
		self.empresa = Empresa.objects.create(nombre='Empresa Permisos', tipo='PEQUENA')

		self.auditor = User.objects.create_user(
			username='auditor.permisos',
			email='auditor.permisos@empresa.com',
			password='Password123!',
			rol='AUDITOR',
			empresa=self.empresa,
			is_approved=True,
		)

		self.lider = User.objects.create_user(
			username='lider.permisos',
			email='lider.permisos@empresa.com',
			password='Password123!',
			rol='LIDER_EQUIPO',
			empresa=self.empresa,
			is_approved=True,
			es_administrador_empresa=True,
		)

		self.admin_sistema = User.objects.create_user(
			username='admin.sistema',
			email='admin.sistema@aegis.com',
			password='Password123!',
			rol='ADMIN_SISTEMA',
			empresa=self.empresa,
		)

	def test_login_devuelve_permisos_en_payload_usuario(self):
		response = self.client.post(
			'/api/usuarios/login/',
			{
				'username': 'auditor.permisos',
				'password': 'Password123!',
			},
			format='json',
		)

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertIn('usuario', response.data)
		self.assertIn('permisos', response.data['usuario'])
		self.assertIn('frontend.view_dashboard', response.data['usuario']['permisos'])
		self.assertIn('frontend.view_auditoria', response.data['usuario']['permisos'])

	def test_perfil_devuelve_permisos_en_payload_usuario(self):
		self.client.force_authenticate(user=self.lider)
		response = self.client.get('/api/usuarios/perfil/')

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertIn('permisos', response.data)
		self.assertIn('frontend.view_dashboard', response.data['permisos'])
		self.assertIn('frontend.view_equipo', response.data['permisos'])
		self.assertIn('frontend.view_reportes', response.data['permisos'])

	def test_admin_sistema_queda_global_aprobado_y_con_capacitacion(self):
		self.admin_sistema.refresh_from_db()
		self.assertIsNone(self.admin_sistema.empresa_id)
		self.assertTrue(self.admin_sistema.is_approved)

		self.client.force_authenticate(user=self.admin_sistema)
		response = self.client.get('/api/usuarios/perfil/')

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertTrue(response.data['is_approved'])
		self.assertIsNone(response.data['empresa'])
		self.assertIn('frontend.view_capacitacion', response.data['permisos'])
		self.assertIn('frontend.view_reportes', response.data['permisos'])


class SeedGruposPermisosAegisCommandTestCase(TestCase):
	def setUp(self):
		self.empresa = Empresa.objects.create(nombre='Empresa Seed RBAC', tipo='PEQUENA')

		self.implementador = User.objects.create_user(
			username='implementador.seed',
			email='implementador.seed@empresa.com',
			password='Password123!',
			rol='IMPLEMENTADOR',
			empresa=self.empresa,
			is_approved=True,
		)

		self.auditor = User.objects.create_user(
			username='auditor.seed',
			email='auditor.seed@empresa.com',
			password='Password123!',
			rol='AUDITOR',
			empresa=self.empresa,
			is_approved=True,
		)

	def test_seed_crea_grupos_y_sincroniza_usuarios(self):
		call_command('seed_grupos_permisos_aegis')

		for rol in ['ADMIN_SISTEMA', 'EMPLEADO', 'IMPLEMENTADOR', 'AUDITOR', 'LIDER_EQUIPO', 'CAPACITADOR']:
			self.assertTrue(Group.objects.filter(name=rol).exists())

		grupo_implementador = Group.objects.get(name='IMPLEMENTADOR')
		grupo_auditor = Group.objects.get(name='AUDITOR')

		self.assertTrue(grupo_implementador.permissions.filter(codename='view_implementacion').exists())
		self.assertTrue(grupo_auditor.permissions.filter(codename='view_auditoria').exists())

		self.implementador.refresh_from_db()
		self.auditor.refresh_from_db()

		self.assertTrue(self.implementador.groups.filter(name='IMPLEMENTADOR').exists())
		self.assertTrue(self.auditor.groups.filter(name='AUDITOR').exists())
