from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

from capacitacion.models import CursoCapacitacion, ModuloContenido


CURSOS_AEGIS = [
    {
        'titulo': 'Introduccion a ISO 27001 para equipos PyME',
        'descripcion': 'Fundamentos practicos del SGSI y su adopcion en organizaciones de tamano pequeno y mediano.',
        'modulos': [
            {
                'orden': 1,
                'titulo': 'Panorama general ISO 27001',
                'descripcion': 'Contexto de la norma, alcance y beneficios de negocio.',
                'tipo': ModuloContenido.TIPO_VIDEO,
                'url_recurso': 'https://www.youtube.com/watch?v=6t3N6D7nU6Q',
                'duracion_minutos': 18,
            },
            {
                'orden': 2,
                'titulo': 'Guia base SGSI para iniciar',
                'descripcion': 'Material de lectura con pasos iniciales de implementacion.',
                'tipo': ModuloContenido.TIPO_PDF,
                'url_recurso': 'https://www.iso.org/files/live/sites/isoorg/files/store/en/PUB100080.pdf',
                'duracion_minutos': 25,
            },
            {
                'orden': 3,
                'titulo': 'Cuestionario de conceptos SGSI',
                'descripcion': 'Evaluacion de conceptos esenciales del curso.',
                'tipo': ModuloContenido.TIPO_CUESTIONARIO,
                'url_recurso': 'https://example.com/aegis/quiz/sgsi-basico',
                'duracion_minutos': 12,
            },
        ],
    },
    {
        'titulo': 'Gestion de incidentes y respuesta temprana',
        'descripcion': 'Como detectar, clasificar, escalar y cerrar incidentes de seguridad con trazabilidad.',
        'modulos': [
            {
                'orden': 1,
                'titulo': 'Flujo operativo de incidente',
                'descripcion': 'Ciclo de vida del incidente y roles involucrados.',
                'tipo': ModuloContenido.TIPO_VIDEO,
                'url_recurso': 'https://www.youtube.com/watch?v=Kf2QfH2A2wA',
                'duracion_minutos': 16,
            },
            {
                'orden': 2,
                'titulo': 'Playbook de respuesta para PyME',
                'descripcion': 'Plantilla descargable para documentar y contener incidentes.',
                'tipo': ModuloContenido.TIPO_PDF,
                'url_recurso': 'https://www.cisa.gov/sites/default/files/publications/CISA_Incident-Response-Playbook_508C.pdf',
                'duracion_minutos': 22,
            },
            {
                'orden': 3,
                'titulo': 'Quiz de clasificacion y escalamiento',
                'descripcion': 'Escenarios reales de severidad y prioridad.',
                'tipo': ModuloContenido.TIPO_CUESTIONARIO,
                'url_recurso': 'https://example.com/aegis/quiz/incidentes',
                'duracion_minutos': 10,
            },
        ],
    },
    {
        'titulo': 'Concienciacion anti-phishing y uso seguro del correo',
        'descripcion': 'Entrenamiento para reducir riesgo humano en canales de correo y mensajeria.',
        'modulos': [
            {
                'orden': 1,
                'titulo': 'Senales de phishing en la practica',
                'descripcion': 'Patrones frecuentes, tecnicas de ingenieria social y verificacion.',
                'tipo': ModuloContenido.TIPO_VIDEO,
                'url_recurso': 'https://www.youtube.com/watch?v=XBkzBrXlle0',
                'duracion_minutos': 14,
            },
            {
                'orden': 2,
                'titulo': 'Checklist de validacion de correos',
                'descripcion': 'Documento rapido de comprobacion para equipos operativos.',
                'tipo': ModuloContenido.TIPO_PDF,
                'url_recurso': 'https://www.cisa.gov/sites/default/files/publications/Phishing_Guidance_508.pdf',
                'duracion_minutos': 15,
            },
            {
                'orden': 3,
                'titulo': 'Simulacion de correos fraudulentos',
                'descripcion': 'Cuestionario final para reforzar criterios de deteccion.',
                'tipo': ModuloContenido.TIPO_CUESTIONARIO,
                'url_recurso': 'https://example.com/aegis/quiz/phishing',
                'duracion_minutos': 10,
            },
        ],
    },
]


class Command(BaseCommand):
    help = 'Carga seed inicial de capacitacion oficial Aegis (cursos globales + modulos).'

    def handle(self, *args, **options):
        user_model = get_user_model()
        superadmin = user_model.objects.filter(is_superuser=True).order_by('id').first()

        cursos_creados = 0
        cursos_actualizados = 0
        modulos_creados = 0
        modulos_actualizados = 0

        with transaction.atomic():
            for curso_data in CURSOS_AEGIS:
                curso, curso_creado = CursoCapacitacion.objects.get_or_create(
                    titulo=curso_data['titulo'],
                    creado_por_admin=True,
                    empresa=None,
                    defaults={
                        'descripcion': curso_data['descripcion'],
                        'creado_por': superadmin,
                        'activo': True,
                    },
                )

                if curso_creado:
                    cursos_creados += 1
                else:
                    curso.descripcion = curso_data['descripcion']
                    curso.creado_por = superadmin
                    curso.activo = True
                    curso.save(update_fields=['descripcion', 'creado_por', 'activo', 'fecha_actualizacion'])
                    cursos_actualizados += 1

                for modulo_data in curso_data['modulos']:
                    modulo, modulo_creado = ModuloContenido.objects.update_or_create(
                        curso=curso,
                        orden=modulo_data['orden'],
                        defaults={
                            'titulo': modulo_data['titulo'],
                            'descripcion': modulo_data['descripcion'],
                            'tipo': modulo_data['tipo'],
                            'url_recurso': modulo_data['url_recurso'],
                            'duracion_minutos': modulo_data['duracion_minutos'],
                            'activo': True,
                        },
                    )

                    if modulo_creado:
                        modulos_creados += 1
                    else:
                        modulos_actualizados += 1

        if superadmin:
            self.stdout.write(self.style.SUCCESS(f'Seed asociado a SuperAdmin: {superadmin.username}'))
        else:
            self.stdout.write(
                self.style.WARNING(
                    'No existe SuperAdmin. Los cursos globales fueron creados con creado_por=NULL.'
                )
            )

        self.stdout.write(self.style.SUCCESS('Seed de capacitacion inicial completado.'))
        self.stdout.write(f'Cursos creados: {cursos_creados}')
        self.stdout.write(f'Cursos actualizados: {cursos_actualizados}')
        self.stdout.write(f'Modulos creados: {modulos_creados}')
        self.stdout.write(f'Modulos actualizados: {modulos_actualizados}')
