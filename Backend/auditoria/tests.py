from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

from implementacion.models import Empresa, ControlISO, EvaluacionControl
from .models import ProcesoAuditoria, RevisionAuditoria

User = get_user_model()


class ListarEvaluacionesAuditoriaViewTestCase(TestCase):
    """
    Test para la vista de listar evaluaciones con acceso diferenciado
    para superusuarios y auditores.
    """
    
    def setUp(self):
        """Configuración inicial de datos de prueba"""
        self.client = APIClient()
        
        # Crear dos empresas
        self.empresa1 = Empresa.objects.create(nombre="Empresa 1", tipo="PEQUENA")
        self.empresa2 = Empresa.objects.create(nombre="Empresa 2", tipo="MEDIANA")
        
        # Crear controles ISO
        self.control1 = ControlISO.objects.create(
            identificador="5.1",
            nombre="Control 1",
            dominio="ORGANIZACIONAL",
            descripcion_guia="Descripción 1"
        )
        self.control2 = ControlISO.objects.create(
            identificador="5.2",
            nombre="Control 2",
            dominio="TECNOLOGICO",
            descripcion_guia="Descripción 2"
        )
        
        # Crear evaluaciones para empresa 1
        self.eval1_emp1 = EvaluacionControl.objects.create(
            empresa=self.empresa1,
            control=self.control1,
            estado="IMPLEMENTADO"
        )
        self.eval2_emp1 = EvaluacionControl.objects.create(
            empresa=self.empresa1,
            control=self.control2,
            estado="IMPLEMENTADO"
        )
        
        # Crear evaluaciones para empresa 2
        self.eval1_emp2 = EvaluacionControl.objects.create(
            empresa=self.empresa2,
            control=self.control1,
            estado="NO_IMPLEMENTADO"
        )
        
        # Crear usuarios
        self.auditor_emp1 = User.objects.create_user(
            username='auditor1',
            email='auditor1@test.com',
            password='testpass123',
            rol='AUDITOR_INTERNO',
            is_approved=True,
            empresa=self.empresa1
        )
        
        self.auditor_emp2 = User.objects.create_user(
            username='auditor2',
            email='auditor2@test.com',
            password='testpass123',
            rol='AUDITOR_INTERNO',
            is_approved=True,
            empresa=self.empresa2
        )
        
        self.implementador = User.objects.create_user(
            username='implementador',
            email='implementador@test.com',
            password='testpass123',
            rol='IMPLEMENTADOR',
            is_approved=True,
            empresa=self.empresa1
        )
        
        self.superuser = User.objects.create_superuser(
            username='admin',
            password='testpass123',
            email='admin@test.com'
        )
    
    def test_superuser_no_puede_ver_evaluaciones_por_aislamiento(self):
        """Test: Superusuario no accede a evaluaciones de negocio por aislamiento."""
        self.client.force_authenticate(user=self.superuser)
        
        response = self.client.get('/api/auditoria/evaluaciones/')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_auditor_solo_ve_evaluaciones_de_su_empresa(self):
        """Test: Auditor solo ve evaluaciones de su propia empresa"""
        self.client.force_authenticate(user=self.auditor_emp1)
        
        response = self.client.get('/api/auditoria/evaluaciones/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['tipo_acceso'], 'auditor')
        self.assertEqual(response.data['empresa'], 'Empresa 1')
        self.assertEqual(response.data['count'], 2)  # Solo las 2 de empresa 1
    
    def test_implementador_no_puede_listar(self):
        """Test: Implementador no puede acceder a la lista de auditorías"""
        self.client.force_authenticate(user=self.implementador)
        
        response = self.client.get('/api/auditoria/evaluaciones/')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class RealizarAuditoriaViewTestCase(TestCase):
    """
    Test de seguridad RBAC para la vista de auditoría.
    Valida que solo usuarios con rol AUDITOR_INTERNO puedan auditar.
    """
    
    def setUp(self):
        """Configuración inicial de datos de prueba"""
        self.client = APIClient()
        
        # Crear empresa
        self.empresa = Empresa.objects.create(
            nombre="Empresa Test",
            tipo="PEQUENA"
        )
        
        # Crear control ISO
        self.control = ControlISO.objects.create(
            identificador="5.1",
            nombre="Políticas de seguridad de la información",
            dominio="ORGANIZACIONAL",
            descripcion_guia="Descripción de prueba"
        )
        
        # Crear evaluación de control
        self.evaluacion = EvaluacionControl.objects.create(
            empresa=self.empresa,
            control=self.control,
            estado="IMPLEMENTADO",
            justificacion="Test justificación"
        )
        
        # Crear usuarios con diferentes roles
        self.implementador = User.objects.create_user(
            username='implementador_test',
            email='implementador_test@test.com',
            password='testpass123',
            rol='IMPLEMENTADOR',
            is_approved=True,
            empresa=self.empresa
        )
        
        self.auditor = User.objects.create_user(
            username='auditor_test',
            email='auditor_test@test.com',
            password='testpass123',
            rol='AUDITOR_INTERNO',
            is_approved=True,
            empresa=self.empresa
        )

        self.proceso = ProcesoAuditoria.objects.create(
            nombre='Auditoria Operativa',
            empresa=self.empresa,
            auditor=self.auditor,
        )
        
        self.superuser = User.objects.create_superuser(
            username='admin_test',
            password='testpass123',
            email='admin@test.com'
        )
    
    def test_implementador_no_puede_auditar(self):
        """Test: Implementador NO puede realizar auditorías (RBAC)"""
        self.client.force_authenticate(user=self.implementador)
        
        url = '/api/auditoria/revisiones/'
        data = {
            'proceso': self.proceso.id,
            'evaluacion_control': self.evaluacion.id,
            'veredicto': 'CONFORME',
            'observaciones': 'Todo correcto'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn('Solo los auditores pueden crear revisiones', str(response.data['detail']))
    
    def test_auditor_puede_auditar(self):
        """Test: Auditor PUEDE realizar auditorías (RBAC)"""
        self.client.force_authenticate(user=self.auditor)
        
        url = '/api/auditoria/revisiones/'
        data = {
            'proceso': self.proceso.id,
            'evaluacion_control': self.evaluacion.id,
            'veredicto': 'CONFORME',
            'observaciones': 'Control implementado correctamente'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['veredicto'], 'CONFORME')
        
        # Verificar que se creó la revisión
        revision = RevisionAuditoria.objects.get(evaluacion_control=self.evaluacion, proceso=self.proceso)
        self.assertEqual(revision.auditor, self.auditor)
        self.assertEqual(revision.veredicto, 'CONFORME')
    
    def test_superuser_no_puede_auditar_datos_negocio(self):
        """Test: Superusuario no puede crear revisiones de auditoría por RBAC."""
        self.client.force_authenticate(user=self.superuser)
        
        url = '/api/auditoria/revisiones/'
        data = {
            'proceso': self.proceso.id,
            'evaluacion_control': self.evaluacion.id,
            'veredicto': 'NO_CONFORME',
            'observaciones': 'Requiere mejoras'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_actualizar_auditoria_existente(self):
        """Test: Actualizar auditoría existente con update_or_create"""
        self.client.force_authenticate(user=self.auditor)
        
        url = '/api/auditoria/revisiones/'
        
        # Primera auditoría
        data1 = {
            'proceso': self.proceso.id,
            'evaluacion_control': self.evaluacion.id,
            'veredicto': 'CONFORME',
            'observaciones': 'Primera revisión'
        }
        response1 = self.client.post(url, data1, format='json')
        self.assertEqual(response1.status_code, status.HTTP_201_CREATED)
        
        # Segunda auditoría (debe actualizar)
        data2 = {
            'proceso': self.proceso.id,
            'evaluacion_control': self.evaluacion.id,
            'veredicto': 'NO_CONFORME',
            'observaciones': 'Revisión actualizada'
        }
        response2 = self.client.post(url, data2, format='json')
        self.assertEqual(response2.status_code, status.HTTP_200_OK)
        
        # Debe existir solo una revisión
        revisiones_count = RevisionAuditoria.objects.filter(evaluacion_control=self.evaluacion, proceso=self.proceso).count()
        self.assertEqual(revisiones_count, 1)
        
        # Debe tener los datos actualizados
        revision = RevisionAuditoria.objects.get(evaluacion_control=self.evaluacion, proceso=self.proceso)
        self.assertEqual(revision.veredicto, 'NO_CONFORME')
        self.assertEqual(revision.observaciones, 'Revisión actualizada')
    
    def test_veredicto_invalido(self):
        """Test: Validación de veredicto inválido"""
        self.client.force_authenticate(user=self.auditor)
        
        url = '/api/auditoria/revisiones/'
        data = {
            'proceso': self.proceso.id,
            'evaluacion_control': self.evaluacion.id,
            'veredicto': 'INVALIDO',
            'observaciones': 'Test'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('veredicto', response.data)
    
    def test_sin_autenticacion(self):
        """Test: Sin autenticación no puede auditar"""
        url = '/api/auditoria/revisiones/'
        data = {
            'proceso': self.proceso.id,
            'evaluacion_control': self.evaluacion.id,
            'veredicto': 'CONFORME',
            'observaciones': 'Test'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class UserDeleteIntegrityAuditoriaTestCase(TestCase):
    """
    Verifica que eliminar un usuario no borra en cascada procesos/revisiones.
    """

    def setUp(self):
        self.empresa = Empresa.objects.create(nombre='Empresa Auditoria', tipo='PEQUENA')
        self.control = ControlISO.objects.create(
            identificador='8.1',
            nombre='Control de prueba de auditoria',
            dominio='ORGANIZACIONAL',
            descripcion_guia='Control para validar integridad historica',
        )

        self.auditor = User.objects.create_user(
            username='auditor_integridad',
            email='auditor.integridad@test.com',
            password='testpass123',
            rol='AUDITOR_INTERNO',
            is_approved=True,
            empresa=self.empresa,
        )

        self.implementador = User.objects.create_user(
            username='implementador_integridad',
            email='implementador.integridad@test.com',
            password='testpass123',
            rol='IMPLEMENTADOR',
            is_approved=True,
            empresa=self.empresa,
        )

        self.evaluacion = EvaluacionControl.objects.create(
            empresa=self.empresa,
            control=self.control,
            usuario=self.implementador,
            estado='IMPLEMENTADO',
            justificacion='Implementado para prueba de retencion',
        )

        self.proceso = ProcesoAuditoria.objects.create(
            nombre='Proceso Integridad Historica',
            empresa=self.empresa,
            auditor=self.auditor,
        )

        self.revision = RevisionAuditoria.objects.create(
            proceso=self.proceso,
            evaluacion_control=self.evaluacion,
            auditor=self.auditor,
            veredicto='CONFORME',
            observaciones='Revision previa al borrado del auditor',
        )

    def test_eliminar_auditor_preserva_proceso_y_revision(self):
        proceso_id = self.proceso.id
        revision_id = self.revision.id

        self.auditor.delete()

        self.assertTrue(ProcesoAuditoria.objects.filter(id=proceso_id).exists())
        self.assertTrue(RevisionAuditoria.objects.filter(id=revision_id).exists())

        proceso = ProcesoAuditoria.objects.get(id=proceso_id)
        revision = RevisionAuditoria.objects.get(id=revision_id)
        self.assertIsNone(proceso.auditor)
        self.assertIsNone(revision.auditor)
