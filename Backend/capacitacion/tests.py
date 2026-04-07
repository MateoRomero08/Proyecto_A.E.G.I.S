from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from implementacion.models import Empresa
from .models import CursoCapacitacion, ModuloContenido, ProgresoUsuario

User = get_user_model()


class CapacitacionHybridVisibilityTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.empresa_1 = Empresa.objects.create(nombre='cocoTECH', tipo='PEQUENA')
        self.empresa_2 = Empresa.objects.create(nombre='andesDATA', tipo='MEDIANA')

        self.superadmin = User.objects.create_superuser(
            username='superadmin',
            password='test1234',
            email='super@aegis.com',
        )

        self.capacitador_empresa_1 = User.objects.create_user(
            username='capacitador_coco',
            email='capacitador@cocotech.com',
            password='test1234',
            rol='CAPACITADOR',
            empresa=self.empresa_1,
            is_approved=True,
        )

        self.lider_empresa_1 = User.objects.create_user(
            username='lider_coco',
            email='lider@cocotech.com',
            password='test1234',
            rol='LIDER_EQUIPO',
            empresa=self.empresa_1,
            is_approved=True,
            es_administrador_empresa=True,
        )

        self.empleado_empresa_1 = User.objects.create_user(
            username='empleado_coco',
            email='empleado.coco@cocotech.com',
            password='test1234',
            rol='IMPLEMENTADOR',
            empresa=self.empresa_1,
            is_approved=True,
        )

        self.empleado_empresa_2 = User.objects.create_user(
            username='empleado_andes',
            email='empleado.andes@andesdata.com',
            password='test1234',
            rol='IMPLEMENTADOR',
            empresa=self.empresa_2,
            is_approved=True,
        )

        self.curso_global = CursoCapacitacion.objects.create(
            titulo='Introduccion ISO 27001',
            descripcion='Curso oficial Aegis',
            empresa=None,
            creado_por_admin=True,
            creado_por=self.superadmin,
        )

        self.curso_privado_empresa_1 = CursoCapacitacion.objects.create(
            titulo='Evacuacion oficina Bogota',
            descripcion='Curso interno cocoTECH',
            empresa=self.empresa_1,
            creado_por_admin=False,
            creado_por=self.capacitador_empresa_1,
        )

        content_type_curso = ContentType.objects.get_for_model(CursoCapacitacion)
        self.perm_add_curso, _ = Permission.objects.get_or_create(
            content_type=content_type_curso,
            codename='add_curso',
            defaults={'name': 'Puede crear cursos de capacitacion (alias Aegis)'},
        )
        self.perm_change_curso, _ = Permission.objects.get_or_create(
            content_type=content_type_curso,
            codename='change_curso',
            defaults={'name': 'Puede gestionar cursos de capacitacion (alias Aegis)'},
        )

        self.capacitador_empresa_1.user_permissions.add(self.perm_add_curso, self.perm_change_curso)
        self.lider_empresa_1.user_permissions.add(self.perm_add_curso, self.perm_change_curso)

    def test_usuario_empresa_recibe_cursos_globales_y_privados_de_su_tenant(self):
        self.client.force_authenticate(user=self.empleado_empresa_1)

        response = self.client.get('/api/capacitacion/cursos/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        titulos = {curso['titulo'] for curso in response.data}
        self.assertIn(self.curso_global.titulo, titulos)
        self.assertIn(self.curso_privado_empresa_1.titulo, titulos)

    def test_usuario_no_ve_cursos_privados_de_otro_tenant(self):
        self.client.force_authenticate(user=self.empleado_empresa_2)

        response = self.client.get('/api/capacitacion/cursos/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        titulos = {curso['titulo'] for curso in response.data}
        self.assertIn(self.curso_global.titulo, titulos)
        self.assertNotIn(self.curso_privado_empresa_1.titulo, titulos)

    def test_capacitador_crea_curso_privado_de_su_empresa(self):
        self.client.force_authenticate(user=self.capacitador_empresa_1)

        payload = {
            'titulo': 'Politicas internas de contrasenas',
            'descripcion': 'Normas internas de acceso',
            'activo': True,
        }

        response = self.client.post('/api/capacitacion/cursos/', payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        curso_creado = CursoCapacitacion.objects.get(titulo='Politicas internas de contrasenas')
        self.assertFalse(curso_creado.creado_por_admin)
        self.assertEqual(curso_creado.empresa, self.empresa_1)

    def test_lider_equipo_con_permiso_crea_curso_privado_de_su_empresa(self):
        self.client.force_authenticate(user=self.lider_empresa_1)

        payload = {
            'titulo': 'Concientizacion para lideres de equipo',
            'descripcion': 'Ruta de capacitacion para liderazgo',
            'activo': True,
        }

        response = self.client.post('/api/capacitacion/cursos/', payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        curso_creado = CursoCapacitacion.objects.get(titulo='Concientizacion para lideres de equipo')
        self.assertFalse(curso_creado.creado_por_admin)
        self.assertEqual(curso_creado.empresa, self.empresa_1)
        self.assertEqual(curso_creado.creado_por, self.lider_empresa_1)

    def test_usuario_sin_permiso_no_puede_crear_curso(self):
        self.client.force_authenticate(user=self.empleado_empresa_1)

        payload = {
            'titulo': 'Curso no autorizado',
            'descripcion': 'Intento sin permisos',
            'activo': True,
        }

        response = self.client.post('/api/capacitacion/cursos/', payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class ProgresoCursoTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.empresa = Empresa.objects.create(nombre='cocoTECH', tipo='PEQUENA')

        self.superadmin = User.objects.create_superuser(
            username='root',
            password='test1234',
            email='root@aegis.com',
        )

        self.usuario = User.objects.create_user(
            username='usuario_curso',
            email='usuario.curso@cocotech.com',
            password='test1234',
            rol='IMPLEMENTADOR',
            empresa=self.empresa,
            is_approved=True,
        )

        self.curso = CursoCapacitacion.objects.create(
            titulo='Curso Hibrido',
            descripcion='Curso para progreso',
            empresa=None,
            creado_por_admin=True,
            creado_por=self.superadmin,
        )

        self.modulo_1 = ModuloContenido.objects.create(
            curso=self.curso,
            titulo='Modulo 1',
            tipo='VIDEO',
            url_recurso='https://example.com/video-1',
            orden=1,
        )
        self.modulo_2 = ModuloContenido.objects.create(
            curso=self.curso,
            titulo='Modulo 2',
            tipo='PDF',
            url_recurso='https://example.com/manual.pdf',
            orden=2,
        )

    def test_actualizar_progreso_por_modulo(self):
        self.client.force_authenticate(user=self.usuario)

        response_1 = self.client.post(
            f'/api/capacitacion/cursos/{self.curso.id}/progreso/',
            {'modulo_id': self.modulo_1.id, 'completado': True},
            format='json',
        )
        self.assertEqual(response_1.status_code, status.HTTP_200_OK)
        self.assertEqual(response_1.data['progreso']['porcentaje_completado'], 50)
        self.assertFalse(response_1.data['progreso']['curso_completado'])

        response_2 = self.client.post(
            f'/api/capacitacion/cursos/{self.curso.id}/progreso/',
            {'modulo_id': self.modulo_2.id, 'completado': True},
            format='json',
        )
        self.assertEqual(response_2.status_code, status.HTTP_200_OK)
        self.assertEqual(response_2.data['progreso']['porcentaje_completado'], 100)
        self.assertTrue(response_2.data['progreso']['curso_completado'])

        progreso = ProgresoUsuario.objects.get(usuario=self.usuario, curso=self.curso)
        self.assertEqual(progreso.porcentaje_completado, 100)
        self.assertTrue(progreso.curso_completado)


class DeleteCapacitacionRBACTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.empresa_1 = Empresa.objects.create(nombre='TecnoBot', tipo='PEQUENA')
        self.empresa_2 = Empresa.objects.create(nombre='AeroData', tipo='MEDIANA')

        self.superadmin = User.objects.create_superuser(
            username='root_delete',
            password='test1234',
            email='root.delete@aegis.com',
        )

        self.capacitador_empresa_1 = User.objects.create_user(
            username='capacitador_tecno',
            email='capacitador@tecnobot.com',
            password='test1234',
            rol='CAPACITADOR',
            empresa=self.empresa_1,
            is_approved=True,
        )

        self.lider_empresa_1 = User.objects.create_user(
            username='lider_tecno',
            email='lider@tecnobot.com',
            password='test1234',
            rol='LIDER_EQUIPO',
            empresa=self.empresa_1,
            is_approved=True,
            es_administrador_empresa=True,
        )

        self.usuario_empresa_1 = User.objects.create_user(
            username='usuario_tecno',
            email='usuario@tecnobot.com',
            password='test1234',
            rol='IMPLEMENTADOR',
            empresa=self.empresa_1,
            is_approved=True,
        )

        self.curso_global = CursoCapacitacion.objects.create(
            titulo='Curso Oficial Aegis Delete',
            descripcion='Curso global para prueba de borrado',
            empresa=None,
            creado_por_admin=True,
            creado_por=self.superadmin,
        )
        self.modulo_global = ModuloContenido.objects.create(
            curso=self.curso_global,
            titulo='Modulo Global',
            tipo='VIDEO',
            url_recurso='https://example.com/global-video',
            orden=1,
        )

        self.curso_privado = CursoCapacitacion.objects.create(
            titulo='Curso Interno TecnoBot Delete',
            descripcion='Curso privado para prueba de borrado',
            empresa=self.empresa_1,
            creado_por_admin=False,
            creado_por=self.capacitador_empresa_1,
        )
        self.modulo_privado_1 = ModuloContenido.objects.create(
            curso=self.curso_privado,
            titulo='Modulo Interno 1',
            tipo='PDF',
            url_recurso='https://example.com/interno-1.pdf',
            orden=1,
        )
        self.modulo_privado_2 = ModuloContenido.objects.create(
            curso=self.curso_privado,
            titulo='Modulo Interno 2',
            tipo='CUESTIONARIO',
            url_recurso='https://example.com/interno-quiz',
            orden=2,
        )

        self.curso_privado_empresa_2 = CursoCapacitacion.objects.create(
            titulo='Curso Interno AeroData Delete',
            descripcion='Curso privado de otra empresa',
            empresa=self.empresa_2,
            creado_por_admin=False,
            creado_por=self.superadmin,
        )
        self.modulo_privado_empresa_2 = ModuloContenido.objects.create(
            curso=self.curso_privado_empresa_2,
            titulo='Modulo Externo',
            tipo='VIDEO',
            url_recurso='https://example.com/externo-video',
            orden=1,
        )

        content_type_curso = ContentType.objects.get_for_model(CursoCapacitacion)
        self.perm_change_curso, _ = Permission.objects.get_or_create(
            content_type=content_type_curso,
            codename='change_curso',
            defaults={'name': 'Puede editar cursos de capacitacion (alias Aegis)'},
        )
        self.perm_delete_curso, _ = Permission.objects.get_or_create(
            content_type=content_type_curso,
            codename='delete_curso',
            defaults={'name': 'Puede eliminar cursos de capacitacion (alias Aegis)'},
        )

        content_type_modulo = ContentType.objects.get_for_model(ModuloContenido)
        self.perm_change_modulo, _ = Permission.objects.get_or_create(
            content_type=content_type_modulo,
            codename='change_modulo',
            defaults={'name': 'Puede editar modulos de capacitacion (alias Aegis)'},
        )
        self.perm_delete_modulo, _ = Permission.objects.get_or_create(
            content_type=content_type_modulo,
            codename='delete_modulo',
            defaults={'name': 'Puede eliminar modulos de capacitacion (alias Aegis)'},
        )

        for gestor in [self.capacitador_empresa_1, self.lider_empresa_1]:
            gestor.user_permissions.add(
                self.perm_change_curso,
                self.perm_delete_curso,
                self.perm_change_modulo,
                self.perm_delete_modulo,
            )

        self.progreso_privado = ProgresoUsuario.objects.create(
            usuario=self.usuario_empresa_1,
            curso=self.curso_privado,
        )
        self.progreso_privado.modulos_completados.add(self.modulo_privado_1)
        self.progreso_privado.recalcular_estado()

    def test_capacitador_no_puede_borrar_curso_oficial_aegis(self):
        self.client.force_authenticate(user=self.capacitador_empresa_1)

        response = self.client.delete(f'/api/capacitacion/cursos/{self.curso_global.id}/')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(CursoCapacitacion.objects.filter(id=self.curso_global.id).exists())

    def test_capacitador_puede_borrar_curso_privado_de_su_empresa(self):
        self.client.force_authenticate(user=self.capacitador_empresa_1)

        response = self.client.delete(f'/api/capacitacion/cursos/{self.curso_privado.id}/')

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(CursoCapacitacion.objects.filter(id=self.curso_privado.id).exists())

    def test_superadmin_puede_borrar_curso_privado(self):
        self.client.force_authenticate(user=self.superadmin)

        response = self.client.delete(f'/api/capacitacion/cursos/{self.curso_privado.id}/')

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(CursoCapacitacion.objects.filter(id=self.curso_privado.id).exists())

    def test_borrar_curso_hace_cascade_en_modulos_y_progreso(self):
        self.client.force_authenticate(user=self.capacitador_empresa_1)

        response = self.client.delete(f'/api/capacitacion/cursos/{self.curso_privado.id}/')

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(ModuloContenido.objects.filter(curso_id=self.curso_privado.id).exists())
        self.assertFalse(ProgresoUsuario.objects.filter(curso_id=self.curso_privado.id).exists())

    def test_capacitador_no_puede_borrar_modulo_oficial_aegis(self):
        self.client.force_authenticate(user=self.capacitador_empresa_1)

        response = self.client.delete(f'/api/capacitacion/modulos/{self.modulo_global.id}/')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(ModuloContenido.objects.filter(id=self.modulo_global.id).exists())

    def test_capacitador_puede_borrar_modulo_privado_y_recalcula_progreso(self):
        self.client.force_authenticate(user=self.capacitador_empresa_1)

        response = self.client.delete(f'/api/capacitacion/modulos/{self.modulo_privado_2.id}/')

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(ModuloContenido.objects.filter(id=self.modulo_privado_2.id).exists())

        progreso = ProgresoUsuario.objects.get(id=self.progreso_privado.id)
        self.assertEqual(progreso.porcentaje_completado, 100)
        self.assertTrue(progreso.curso_completado)

    def test_lider_con_permiso_puede_editar_curso_de_su_empresa(self):
        self.client.force_authenticate(user=self.lider_empresa_1)

        response = self.client.patch(
            f'/api/capacitacion/cursos/{self.curso_privado.id}/',
            {'titulo': 'Curso Interno TecnoBot Actualizado por Lider'},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.curso_privado.refresh_from_db()
        self.assertEqual(self.curso_privado.titulo, 'Curso Interno TecnoBot Actualizado por Lider')

    def test_lider_con_permiso_no_puede_editar_curso_de_otra_empresa(self):
        self.client.force_authenticate(user=self.lider_empresa_1)

        response = self.client.patch(
            f'/api/capacitacion/cursos/{self.curso_privado_empresa_2.id}/',
            {'titulo': 'Intento no autorizado'},
            format='json',
        )

        self.assertIn(response.status_code, [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND])

    def test_lider_con_permiso_puede_borrar_curso_de_su_empresa(self):
        self.client.force_authenticate(user=self.lider_empresa_1)

        response = self.client.delete(f'/api/capacitacion/cursos/{self.curso_privado.id}/')

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(CursoCapacitacion.objects.filter(id=self.curso_privado.id).exists())

    def test_lider_con_permiso_no_puede_borrar_curso_de_otra_empresa(self):
        self.client.force_authenticate(user=self.lider_empresa_1)

        response = self.client.delete(f'/api/capacitacion/cursos/{self.curso_privado_empresa_2.id}/')

        self.assertIn(response.status_code, [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND])
        self.assertTrue(CursoCapacitacion.objects.filter(id=self.curso_privado_empresa_2.id).exists())

    def test_lider_con_permiso_puede_editar_modulo_de_su_empresa(self):
        self.client.force_authenticate(user=self.lider_empresa_1)

        response = self.client.patch(
            f'/api/capacitacion/modulos/{self.modulo_privado_1.id}/',
            {'titulo': 'Modulo Interno 1 Actualizado por Lider'},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.modulo_privado_1.refresh_from_db()
        self.assertEqual(self.modulo_privado_1.titulo, 'Modulo Interno 1 Actualizado por Lider')

    def test_lider_con_permiso_no_puede_editar_modulo_de_otra_empresa(self):
        self.client.force_authenticate(user=self.lider_empresa_1)

        response = self.client.patch(
            f'/api/capacitacion/modulos/{self.modulo_privado_empresa_2.id}/',
            {'titulo': 'Intento modulo no autorizado'},
            format='json',
        )

        self.assertIn(response.status_code, [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND])

    def test_lider_con_permiso_puede_borrar_modulo_de_su_empresa(self):
        self.client.force_authenticate(user=self.lider_empresa_1)

        response = self.client.delete(f'/api/capacitacion/modulos/{self.modulo_privado_2.id}/')

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(ModuloContenido.objects.filter(id=self.modulo_privado_2.id).exists())

    def test_lider_con_permiso_no_puede_borrar_modulo_de_otra_empresa(self):
        self.client.force_authenticate(user=self.lider_empresa_1)

        response = self.client.delete(f'/api/capacitacion/modulos/{self.modulo_privado_empresa_2.id}/')

        self.assertIn(response.status_code, [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND])
        self.assertTrue(ModuloContenido.objects.filter(id=self.modulo_privado_empresa_2.id).exists())


class UserDeleteIntegrityCapacitacionTestCase(TestCase):
    """
    Verifica que eliminar un usuario preserve historico de progreso en capacitacion.
    """

    def setUp(self):
        self.empresa = Empresa.objects.create(nombre='Empresa Capacitacion', tipo='PEQUENA')

        self.superadmin = User.objects.create_superuser(
            username='root_integridad',
            password='test1234',
            email='root.integridad@aegis.com',
        )

        self.usuario = User.objects.create_user(
            username='usuario_integridad',
            email='usuario.integridad@empresa.com',
            password='test1234',
            rol='EMPLEADO',
            empresa=self.empresa,
            is_approved=True,
        )

        self.curso = CursoCapacitacion.objects.create(
            titulo='Curso Integridad',
            descripcion='Curso para validar retencion de progreso',
            empresa=None,
            creado_por_admin=True,
            creado_por=self.superadmin,
        )

        self.progreso = ProgresoUsuario.objects.create(
            usuario=self.usuario,
            curso=self.curso,
            porcentaje_completado=40,
            curso_completado=False,
        )

    def test_eliminar_usuario_preserva_progreso_con_usuario_null(self):
        progreso_id = self.progreso.id

        self.usuario.delete()

        self.assertTrue(ProgresoUsuario.objects.filter(id=progreso_id).exists())
        progreso = ProgresoUsuario.objects.get(id=progreso_id)
        self.assertIsNone(progreso.usuario)
        self.assertEqual(progreso.curso, self.curso)
