from django.core.management.base import BaseCommand
from implementacion.models import ControlISO


class Command(BaseCommand):
    help = 'Poblar la tabla ControlISO con los 93 controles de la ISO 27001:2022'

    def handle(self, *args, **kwargs):
        controles = [
            # ===== CONTROLES ORGANIZACIONALES (5.1 - 5.37) =====
            {
                'identificador': '5.1',
                'nombre': 'Políticas de seguridad de la información',
                'dominio': 'ORGANIZACIONAL',
                'descripcion_guia': 'Se debe definir un conjunto de políticas de seguridad de la información, aprobadas por la dirección, publicadas y comunicadas a los empleados y partes relevantes.'
            },
            {
                'identificador': '5.2',
                'nombre': 'Roles y responsabilidades de seguridad de la información',
                'dominio': 'ORGANIZACIONAL',
                'descripcion_guia': 'Las responsabilidades de seguridad de la información deben ser definidas y asignadas de acuerdo con las políticas de seguridad de la información de la organización.'
            },
            {
                'identificador': '5.3',
                'nombre': 'Segregación de funciones',
                'dominio': 'ORGANIZACIONAL',
                'descripcion_guia': 'Los deberes y áreas de responsabilidad en conflicto deben ser segregados para reducir las oportunidades de modificación no autorizada o no intencional o el uso indebido de los activos de la organización.'
            },
            {
                'identificador': '5.4',
                'nombre': 'Responsabilidades de la dirección',
                'dominio': 'ORGANIZACIONAL',
                'descripcion_guia': 'La dirección debe requerir que todo el personal aplique la seguridad de la información de acuerdo con las políticas, procedimientos y normas establecidos de la organización.'
            },
            {
                'identificador': '5.5',
                'nombre': 'Contacto con autoridades',
                'dominio': 'ORGANIZACIONAL',
                'descripcion_guia': 'La organización debe establecer y mantener contacto con las autoridades relevantes (policía, bomberos, reguladores).'
            },
            {
                'identificador': '5.6',
                'nombre': 'Contacto con grupos de interés especial',
                'dominio': 'ORGANIZACIONAL',
                'descripcion_guia': 'La organización debe establecer y mantener contacto con grupos de interés especial u otros foros de seguridad especializados y asociaciones profesionales.'
            },
            {
                'identificador': '5.7',
                'nombre': 'Inteligencia de amenazas',
                'dominio': 'ORGANIZACIONAL',
                'descripcion_guia': 'La información relacionada con las amenazas de seguridad de la información debe ser recopilada y analizada para producir inteligencia de amenazas.'
            },
            {
                'identificador': '5.8',
                'nombre': 'Seguridad de la información en la gestión de proyectos',
                'dominio': 'ORGANIZACIONAL',
                'descripcion_guia': 'La seguridad de la información debe integrarse en la gestión de proyectos.'
            },
            {
                'identificador': '5.9',
                'nombre': 'Inventario de información y otros activos asociados',
                'dominio': 'ORGANIZACIONAL',
                'descripcion_guia': 'Se debe elaborar y mantener un inventario de información y otros activos asociados, incluidos los propietarios.'
            },
            {
                'identificador': '5.10',
                'nombre': 'Uso aceptable de la información y otros activos asociados',
                'dominio': 'ORGANIZACIONAL',
                'descripcion_guia': 'Se deben identificar, documentar e implementar reglas para el uso aceptable de información y de activos asociados con información y facilidades de procesamiento de información.'
            },
            {
                'identificador': '5.11',
                'nombre': 'Devolución de activos',
                'dominio': 'ORGANIZACIONAL',
                'descripcion_guia': 'El personal y las partes externas deben devolver todos los activos de la organización que se encuentren en su posesión al finalizar su empleo, contrato o acuerdo.'
            },
            {
                'identificador': '5.12',
                'nombre': 'Clasificación de la información',
                'dominio': 'ORGANIZACIONAL',
                'descripcion_guia': 'La información debe ser clasificada de acuerdo con las necesidades de seguridad de la información de la organización basadas en confidencialidad, integridad, disponibilidad y requisitos de las partes interesadas relevantes.'
            },
            {
                'identificador': '5.13',
                'nombre': 'Etiquetado de la información',
                'dominio': 'ORGANIZACIONAL',
                'descripcion_guia': 'Se debe desarrollar e implementar un conjunto apropiado de procedimientos para el etiquetado de información de acuerdo con el esquema de clasificación de información adoptado por la organización.'
            },
            {
                'identificador': '5.14',
                'nombre': 'Transferencia de información',
                'dominio': 'ORGANIZACIONAL',
                'descripcion_guia': 'Las reglas, procedimientos o acuerdos de transferencia de información deben estar en vigencia para todos los tipos de instalaciones de transferencia dentro de la organización y entre la organización y otras partes.'
            },
            {
                'identificador': '5.15',
                'nombre': 'Control de acceso',
                'dominio': 'ORGANIZACIONAL',
                'descripcion_guia': 'Se deben establecer e implementar reglas para controlar el acceso físico y lógico a la información y otros activos asociados.'
            },
            {
                'identificador': '5.16',
                'nombre': 'Gestión de identidades',
                'dominio': 'ORGANIZACIONAL',
                'descripcion_guia': 'El ciclo de vida completo de las identidades debe ser gestionado.'
            },
            {
                'identificador': '5.17',
                'nombre': 'Información de autenticación',
                'dominio': 'ORGANIZACIONAL',
                'descripcion_guia': 'La asignación y gestión de información de autenticación debe ser controlada por un proceso de gestión, incluido el asesoramiento al personal sobre el manejo apropiado de la información de autenticación.'
            },
            {
                'identificador': '5.18',
                'nombre': 'Derechos de acceso',
                'dominio': 'ORGANIZACIONAL',
                'descripcion_guia': 'Los derechos de acceso a la información y otros activos asociados deben ser provisionados, revisados, modificados y removidos de acuerdo con la política de control de acceso de la organización.'
            },
            {
                'identificador': '5.19',
                'nombre': 'Seguridad de la información en las relaciones con proveedores',
                'dominio': 'ORGANIZACIONAL',
                'descripcion_guia': 'Los procesos y procedimientos deben ser definidos e implementados para gestionar los riesgos de seguridad de la información asociados con el uso de productos o servicios del proveedor.'
            },
            {
                'identificador': '5.20',
                'nombre': 'Abordar la seguridad de la información en los acuerdos con proveedores',
                'dominio': 'ORGANIZACIONAL',
                'descripcion_guia': 'Los requisitos de seguridad de la información relevantes deben ser establecidos y acordados con cada proveedor en función del tipo de relación con el proveedor.'
            },
            {
                'identificador': '5.21',
                'nombre': 'Gestión de la seguridad de la información en la cadena de suministro de TIC',
                'dominio': 'ORGANIZACIONAL',
                'descripcion_guia': 'Los procesos y procedimientos deben ser definidos e implementados para gestionar los riesgos de seguridad de la información asociados con la cadena de suministro de productos y servicios de TIC.'
            },
            {
                'identificador': '5.22',
                'nombre': 'Monitoreo, revisión y gestión de cambios de servicios de proveedores',
                'dominio': 'ORGANIZACIONAL',
                'descripcion_guia': 'La organización debe monitorear, revisar, evaluar y gestionar regularmente los cambios en las prácticas de seguridad de la información del proveedor y la prestación de servicios.'
            },
            {
                'identificador': '5.23',
                'nombre': 'Seguridad de la información para el uso de servicios en la nube',
                'dominio': 'ORGANIZACIONAL',
                'descripcion_guia': 'Los procesos de adquisición, uso, gestión y salida de servicios en la nube deben ser establecidos de acuerdo con los requisitos de seguridad de la información de la organización.'
            },
            {
                'identificador': '5.24',
                'nombre': 'Planificación y preparación de la gestión de incidentes de seguridad de la información',
                'dominio': 'ORGANIZACIONAL',
                'descripcion_guia': 'La organización debe planificar y prepararse para la gestión de incidentes de seguridad de la información definiendo, estableciendo y comunicando procesos, roles y responsabilidades.'
            },
            {
                'identificador': '5.25',
                'nombre': 'Evaluación y decisión sobre eventos de seguridad de la información',
                'dominio': 'ORGANIZACIONAL',
                'descripcion_guia': 'La organización debe evaluar los eventos de seguridad de la información y decidir si deben ser categorizados como incidentes de seguridad de la información.'
            },
            {
                'identificador': '5.26',
                'nombre': 'Respuesta a incidentes de seguridad de la información',
                'dominio': 'ORGANIZACIONAL',
                'descripcion_guia': 'Los incidentes de seguridad de la información deben ser respondidos de acuerdo con los procedimientos documentados.'
            },
            {
                'identificador': '5.27',
                'nombre': 'Aprender de los incidentes de seguridad de la información',
                'dominio': 'ORGANIZACIONAL',
                'descripcion_guia': 'El conocimiento obtenido de los incidentes de seguridad de la información debe ser usado para fortalecer y mejorar los controles de seguridad de la información.'
            },
            {
                'identificador': '5.28',
                'nombre': 'Recopilación de evidencia',
                'dominio': 'ORGANIZACIONAL',
                'descripcion_guia': 'La organización debe establecer e implementar procedimientos para la identificación, recopilación, adquisición y preservación de evidencia relacionada con eventos de seguridad de la información.'
            },
            {
                'identificador': '5.29',
                'nombre': 'Seguridad de la información durante la interrupción',
                'dominio': 'ORGANIZACIONAL',
                'descripcion_guia': 'La organización debe planificar cómo mantener la seguridad de la información a un nivel apropiado durante la interrupción.'
            },
            {
                'identificador': '5.30',
                'nombre': 'Preparación de las TIC para la continuidad del negocio',
                'dominio': 'ORGANIZACIONAL',
                'descripcion_guia': 'La preparación de las TIC debe ser planificada, implementada, mantenida y probada basándose en los objetivos de continuidad del negocio y los requisitos de continuidad de las TIC.'
            },
            {
                'identificador': '5.31',
                'nombre': 'Requisitos legales, estatutarios, regulatorios y contractuales',
                'dominio': 'ORGANIZACIONAL',
                'descripcion_guia': 'Los requisitos legales, estatutarios, regulatorios y contractuales relevantes para la seguridad de la información y el enfoque de la organización para cumplir con estos requisitos deben ser identificados, documentados y mantenidos actualizados.'
            },
            {
                'identificador': '5.32',
                'nombre': 'Derechos de propiedad intelectual',
                'dominio': 'ORGANIZACIONAL',
                'descripcion_guia': 'La organización debe implementar procedimientos apropiados para proteger los derechos de propiedad intelectual.'
            },
            {
                'identificador': '5.33',
                'nombre': 'Protección de registros',
                'dominio': 'ORGANIZACIONAL',
                'descripcion_guia': 'Los registros deben ser protegidos contra pérdida, destrucción, falsificación, acceso no autorizado y liberación no autorizada.'
            },
            {
                'identificador': '5.34',
                'nombre': 'Privacidad y protección de información de identificación personal',
                'dominio': 'ORGANIZACIONAL',
                'descripcion_guia': 'La organización debe identificar y cumplir con los requisitos relacionados con la preservación de la privacidad y la protección de PII de acuerdo con las leyes y regulaciones aplicables y los requisitos contractuales.'
            },
            {
                'identificador': '5.35',
                'nombre': 'Revisión independiente de la seguridad de la información',
                'dominio': 'ORGANIZACIONAL',
                'descripcion_guia': 'El enfoque de la organización para gestionar la seguridad de la información y su implementación deben ser revisados independientemente a intervalos planificados o cuando ocurran cambios significativos.'
            },
            {
                'identificador': '5.36',
                'nombre': 'Cumplimiento de políticas, reglas y normas de seguridad de la información',
                'dominio': 'ORGANIZACIONAL',
                'descripcion_guia': 'El cumplimiento con las políticas, reglas y normas de seguridad de la información de la organización debe ser revisado regularmente.'
            },
            {
                'identificador': '5.37',
                'nombre': 'Procedimientos operativos documentados',
                'dominio': 'ORGANIZACIONAL',
                'descripcion_guia': 'Los procedimientos operativos para las instalaciones de procesamiento de información deben ser documentados y puestos a disposición del personal que los necesite.'
            },
            
            # ===== CONTROLES DE PERSONAS (6.1 - 6.8) =====
            {
                'identificador': '6.1',
                'nombre': 'Selección',
                'dominio': 'PERSONAS',
                'descripcion_guia': 'Las verificaciones de antecedentes de todos los candidatos a empleo deben ser realizadas antes del empleo y de forma continua, teniendo en cuenta las leyes, regulaciones y ética aplicables, y deben ser proporcionales a los requisitos del negocio, la clasificación de la información a la que se accederá y los riesgos percibidos.'
            },
            {
                'identificador': '6.2',
                'nombre': 'Términos y condiciones de empleo',
                'dominio': 'PERSONAS',
                'descripcion_guia': 'Los acuerdos contractuales con el personal y contratistas deben establecer sus responsabilidades y las de la organización en cuanto a la seguridad de la información.'
            },
            {
                'identificador': '6.3',
                'nombre': 'Concienciación, educación y capacitación en seguridad de la información',
                'dominio': 'PERSONAS',
                'descripcion_guia': 'El personal de la organización y las partes interesadas relevantes deben recibir concienciación, educación y capacitación apropiadas en seguridad de la información y actualizaciones regulares sobre las políticas, procedimientos y normas de seguridad de la información de la organización según sea relevante para su función de trabajo.'
            },
            {
                'identificador': '6.4',
                'nombre': 'Proceso disciplinario',
                'dominio': 'PERSONAS',
                'descripcion_guia': 'Debe haber un proceso disciplinario formal comunicado para tomar medidas contra el personal y otras partes relevantes que hayan cometido una violación de la política de seguridad de la información.'
            },
            {
                'identificador': '6.5',
                'nombre': 'Responsabilidades después de la terminación o cambio de empleo',
                'dominio': 'PERSONAS',
                'descripcion_guia': 'Las responsabilidades y deberes de seguridad de la información que permanecen válidos después de la terminación o cambio de empleo deben ser definidos, comunicados al personal y las partes relevantes, y aplicados.'
            },
            {
                'identificador': '6.6',
                'nombre': 'Acuerdos de confidencialidad o no divulgación',
                'dominio': 'PERSONAS',
                'descripcion_guia': 'Los acuerdos de confidencialidad o no divulgación que reflejen las necesidades de la organización para la protección de la información deben ser identificados, documentados, revisados regularmente y firmados por el personal y otras partes relevantes.'
            },
            {
                'identificador': '6.7',
                'nombre': 'Trabajo remoto',
                'dominio': 'PERSONAS',
                'descripcion_guia': 'Se deben implementar medidas de seguridad cuando el personal trabaja de forma remota para proteger la información a la que se accede, procesa o almacena fuera de las instalaciones de la organización.'
            },
            {
                'identificador': '6.8',
                'nombre': 'Reporte de eventos de seguridad de la información',
                'dominio': 'PERSONAS',
                'descripcion_guia': 'La organización debe proporcionar un mecanismo para que el personal reporte eventos de seguridad de la información observados o sospechados a través de canales apropiados de manera oportuna.'
            },
            
            # ===== CONTROLES FÍSICOS (7.1 - 7.14) =====
            {
                'identificador': '7.1',
                'nombre': 'Perímetros de seguridad física',
                'dominio': 'FISICO',
                'descripcion_guia': 'Los perímetros de seguridad deben ser definidos y usados para proteger áreas que contienen información y otros activos asociados.'
            },
            {
                'identificador': '7.2',
                'nombre': 'Entrada física',
                'dominio': 'FISICO',
                'descripcion_guia': 'Las áreas seguras deben ser protegidas por controles de entrada apropiados y puntos de acceso.'
            },
            {
                'identificador': '7.3',
                'nombre': 'Seguridad de oficinas, salas e instalaciones',
                'dominio': 'FISICO',
                'descripcion_guia': 'La seguridad física de oficinas, salas e instalaciones debe ser diseñada e implementada.'
            },
            {
                'identificador': '7.4',
                'nombre': 'Monitoreo de seguridad física',
                'dominio': 'FISICO',
                'descripcion_guia': 'Las instalaciones deben ser monitoreadas continuamente para acceso físico no autorizado.'
            },
            {
                'identificador': '7.5',
                'nombre': 'Protección contra amenazas físicas y ambientales',
                'dominio': 'FISICO',
                'descripcion_guia': 'La protección contra amenazas físicas y ambientales, como desastres naturales y amenazas intencionales o accidentales, debe ser diseñada e implementada.'
            },
            {
                'identificador': '7.6',
                'nombre': 'Trabajo en áreas seguras',
                'dominio': 'FISICO',
                'descripcion_guia': 'Se deben diseñar e implementar medidas de seguridad para trabajar en áreas seguras.'
            },
            {
                'identificador': '7.7',
                'nombre': 'Escritorio y pantalla limpios',
                'dominio': 'FISICO',
                'descripcion_guia': 'Se deben definir e implementar apropiadamente reglas de escritorio y pantalla limpios para papeles e información almacenada en medios.'
            },
            {
                'identificador': '7.8',
                'nombre': 'Ubicación y protección del equipo',
                'dominio': 'FISICO',
                'descripcion_guia': 'El equipo debe ser ubicado de forma segura y protegido.'
            },
            {
                'identificador': '7.9',
                'nombre': 'Seguridad de los activos fuera de las instalaciones',
                'dominio': 'FISICO',
                'descripcion_guia': 'Los activos fuera de las instalaciones deben ser protegidos.'
            },
            {
                'identificador': '7.10',
                'nombre': 'Medios de almacenamiento',
                'dominio': 'FISICO',
                'descripcion_guia': 'Los medios de almacenamiento deben ser gestionados durante todo su ciclo de vida de adquisición, uso, transporte y disposición de acuerdo con el esquema de clasificación y los requisitos de manejo de la organización.'
            },
            {
                'identificador': '7.11',
                'nombre': 'Servicios de apoyo',
                'dominio': 'FISICO',
                'descripcion_guia': 'Las instalaciones de procesamiento de información deben ser protegidas contra fallas de energía y otras interrupciones causadas por fallas en los servicios de apoyo.'
            },
            {
                'identificador': '7.12',
                'nombre': 'Seguridad del cableado',
                'dominio': 'FISICO',
                'descripcion_guia': 'Los cables que transportan energía, datos o servicios de información de apoyo deben ser protegidos contra interceptación, interferencia o daño.'
            },
            {
                'identificador': '7.13',
                'nombre': 'Mantenimiento de equipo',
                'dominio': 'FISICO',
                'descripcion_guia': 'El equipo debe ser mantenido correctamente para asegurar la disponibilidad, integridad y confidencialidad de la información.'
            },
            {
                'identificador': '7.14',
                'nombre': 'Disposición o reutilización segura de equipo',
                'dominio': 'FISICO',
                'descripcion_guia': 'Los elementos de equipo que contienen medios de almacenamiento deben ser verificados para asegurar que cualquier dato sensible e información bajo licencia haya sido removido o sobrescrito de forma segura antes de su disposición o reutilización.'
            },
            
            # ===== CONTROLES TECNOLÓGICOS (8.1 - 8.34) =====
            {
                'identificador': '8.1',
                'nombre': 'Dispositivos de punto final de usuario',
                'dominio': 'TECNOLOGICO',
                'descripcion_guia': 'La información almacenada, procesada o accesible a través de dispositivos de punto final de usuario debe ser protegida.'
            },
            {
                'identificador': '8.2',
                'nombre': 'Derechos de acceso privilegiado',
                'dominio': 'TECNOLOGICO',
                'descripcion_guia': 'La asignación y el uso de derechos de acceso privilegiado deben ser restringidos y gestionados.'
            },
            {
                'identificador': '8.3',
                'nombre': 'Restricción de acceso a la información',
                'dominio': 'TECNOLOGICO',
                'descripcion_guia': 'El acceso a la información y otros activos asociados debe ser restringido de acuerdo con la política de control de acceso establecida.'
            },
            {
                'identificador': '8.4',
                'nombre': 'Acceso al código fuente',
                'dominio': 'TECNOLOGICO',
                'descripcion_guia': 'El acceso de lectura y escritura al código fuente, herramientas de desarrollo y bibliotecas de software debe ser gestionado apropiadamente.'
            },
            {
                'identificador': '8.5',
                'nombre': 'Autenticación segura',
                'dominio': 'TECNOLOGICO',
                'descripcion_guia': 'Las tecnologías y procedimientos de autenticación segura deben ser implementados basándose en restricciones de acceso a la información y la política de control de acceso.'
            },
            {
                'identificador': '8.6',
                'nombre': 'Gestión de capacidad',
                'dominio': 'TECNOLOGICO',
                'descripcion_guia': 'El uso de recursos debe ser monitoreado y ajustado en línea con los requisitos actuales y previstos de capacidad.'
            },
            {
                'identificador': '8.7',
                'nombre': 'Protección contra malware',
                'dominio': 'TECNOLOGICO',
                'descripcion_guia': 'La protección contra malware debe ser implementada y apoyada por la concienciación apropiada del usuario.'
            },
            {
                'identificador': '8.8',
                'nombre': 'Gestión de vulnerabilidades técnicas',
                'dominio': 'TECNOLOGICO',
                'descripcion_guia': 'La información sobre vulnerabilidades técnicas de los sistemas de información en uso debe ser obtenida, la exposición de la organización a tales vulnerabilidades debe ser evaluada y se deben tomar medidas apropiadas.'
            },
            {
                'identificador': '8.9',
                'nombre': 'Gestión de configuración',
                'dominio': 'TECNOLOGICO',
                'descripcion_guia': 'Las configuraciones, incluidas las configuraciones de seguridad, de hardware, software, servicios y redes deben ser establecidas, documentadas, implementadas, monitoreadas y revisadas.'
            },
            {
                'identificador': '8.10',
                'nombre': 'Eliminación de información',
                'dominio': 'TECNOLOGICO',
                'descripcion_guia': 'La información almacenada en sistemas de información, dispositivos o cualquier otro medio de almacenamiento debe ser eliminada cuando ya no sea requerida.'
            },
            {
                'identificador': '8.11',
                'nombre': 'Enmascaramiento de datos',
                'dominio': 'TECNOLOGICO',
                'descripcion_guia': 'El enmascaramiento de datos debe ser usado de acuerdo con la política de control de acceso de la organización y otros requisitos relacionados con el negocio y las leyes y regulaciones aplicables.'
            },
            {
                'identificador': '8.12',
                'nombre': 'Prevención de fuga de datos',
                'dominio': 'TECNOLOGICO',
                'descripcion_guia': 'Las medidas de prevención de fuga de datos deben ser aplicadas a sistemas, redes y cualquier otro dispositivo que procese, almacene o transmita información sensible.'
            },
            {
                'identificador': '8.13',
                'nombre': 'Respaldo de información',
                'dominio': 'TECNOLOGICO',
                'descripcion_guia': 'Las copias de respaldo de información, software e imágenes del sistema deben ser mantenidas y probadas regularmente de acuerdo con la política de respaldo acordada.'
            },
            {
                'identificador': '8.14',
                'nombre': 'Redundancia de las instalaciones de procesamiento de información',
                'dominio': 'TECNOLOGICO',
                'descripcion_guia': 'Las instalaciones de procesamiento de información deben ser implementadas con redundancia suficiente para cumplir con los requisitos de disponibilidad.'
            },
            {
                'identificador': '8.15',
                'nombre': 'Registro',
                'dominio': 'TECNOLOGICO',
                'descripcion_guia': 'Los registros que graban actividades, excepciones, fallas y otros eventos relevantes deben ser producidos, almacenados, protegidos y analizados.'
            },
            {
                'identificador': '8.16',
                'nombre': 'Actividades de monitoreo',
                'dominio': 'TECNOLOGICO',
                'descripcion_guia': 'Las redes, sistemas y aplicaciones deben ser monitoreadas para comportamientos anómalos y se deben tomar acciones apropiadas para evaluar incidentes potenciales de seguridad de la información.'
            },
            {
                'identificador': '8.17',
                'nombre': 'Sincronización de reloj',
                'dominio': 'TECNOLOGICO',
                'descripcion_guia': 'Los relojes de los sistemas de procesamiento de información usados por la organización deben ser sincronizados con fuentes de tiempo aprobadas.'
            },
            {
                'identificador': '8.18',
                'nombre': 'Uso de programas de utilidad privilegiados',
                'dominio': 'TECNOLOGICO',
                'descripcion_guia': 'El uso de programas de utilidad que pueden ser capaces de anular los controles del sistema y la aplicación debe ser restringido y estrechamente controlado.'
            },
            {
                'identificador': '8.19',
                'nombre': 'Instalación de software en sistemas operativos',
                'dominio': 'TECNOLOGICO',
                'descripcion_guia': 'Los procedimientos y medidas deben ser implementados para gestionar de forma segura la instalación de software en sistemas operativos.'
            },
            {
                'identificador': '8.20',
                'nombre': 'Seguridad de redes',
                'dominio': 'TECNOLOGICO',
                'descripcion_guia': 'Las redes y los dispositivos de red deben ser asegurados, gestionados y controlados para proteger la información en sistemas y aplicaciones.'
            },
            {
                'identificador': '8.21',
                'nombre': 'Seguridad de los servicios de red',
                'dominio': 'TECNOLOGICO',
                'descripcion_guia': 'Los mecanismos de seguridad, niveles de servicio y requisitos de servicio de los servicios de red deben ser identificados, implementados y monitoreados.'
            },
            {
                'identificador': '8.22',
                'nombre': 'Segregación de redes',
                'dominio': 'TECNOLOGICO',
                'descripcion_guia': 'Los grupos de servicios de información, usuarios y sistemas de información deben ser segregados en las redes de la organización.'
            },
            {
                'identificador': '8.23',
                'nombre': 'Filtrado web',
                'dominio': 'TECNOLOGICO',
                'descripcion_guia': 'El acceso a sitios web externos debe ser gestionado para reducir la exposición a contenido malicioso.'
            },
            {
                'identificador': '8.24',
                'nombre': 'Uso de criptografía',
                'dominio': 'TECNOLOGICO',
                'descripcion_guia': 'Las reglas para el uso efectivo de la criptografía, incluida la gestión de claves criptográficas, deben ser definidas e implementadas.'
            },
            {
                'identificador': '8.25',
                'nombre': 'Ciclo de vida de desarrollo seguro',
                'dominio': 'TECNOLOGICO',
                'descripcion_guia': 'Las reglas para el desarrollo seguro de software y sistemas deben ser establecidas y aplicadas.'
            },
            {
                'identificador': '8.26',
                'nombre': 'Requisitos de seguridad de aplicaciones',
                'dominio': 'TECNOLOGICO',
                'descripcion_guia': 'Los requisitos de seguridad de la información deben ser identificados, especificados y aprobados al desarrollar o adquirir aplicaciones.'
            },
            {
                'identificador': '8.27',
                'nombre': 'Arquitectura de sistema seguro y principios de ingeniería',
                'dominio': 'TECNOLOGICO',
                'descripcion_guia': 'Los principios para diseñar sistemas seguros deben ser establecidos, documentados, mantenidos y aplicados a cualquier actividad de desarrollo de sistemas de información.'
            },
            {
                'identificador': '8.28',
                'nombre': 'Codificación segura',
                'dominio': 'TECNOLOGICO',
                'descripcion_guia': 'Los principios de codificación segura deben ser aplicados al desarrollo de software.'
            },
            {
                'identificador': '8.29',
                'nombre': 'Pruebas de seguridad en desarrollo y aceptación',
                'dominio': 'TECNOLOGICO',
                'descripcion_guia': 'Los procesos de pruebas de seguridad deben ser definidos y implementados en el ciclo de vida de desarrollo.'
            },
            {
                'identificador': '8.30',
                'nombre': 'Desarrollo externalizado',
                'dominio': 'TECNOLOGICO',
                'descripcion_guia': 'La organización debe dirigir, monitorear y revisar las actividades relacionadas con el desarrollo de sistemas externalizados.'
            },
            {
                'identificador': '8.31',
                'nombre': 'Separación de ambientes de desarrollo, prueba y producción',
                'dominio': 'TECNOLOGICO',
                'descripcion_guia': 'Los ambientes de desarrollo, prueba y producción deben ser separados y asegurados.'
            },
            {
                'identificador': '8.32',
                'nombre': 'Gestión de cambios',
                'dominio': 'TECNOLOGICO',
                'descripcion_guia': 'Los cambios a las instalaciones de procesamiento de información y sistemas de información deben estar sujetos a procedimientos de gestión de cambios.'
            },
            {
                'identificador': '8.33',
                'nombre': 'Información de prueba',
                'dominio': 'TECNOLOGICO',
                'descripcion_guia': 'La información de prueba debe ser seleccionada, protegida y gestionada apropiadamente.'
            },
            {
                'identificador': '8.34',
                'nombre': 'Protección de sistemas de información durante las pruebas de auditoría',
                'dominio': 'TECNOLOGICO',
                'descripcion_guia': 'Las pruebas de auditoría y otras actividades de aseguramiento que involucren la evaluación de sistemas operativos deben ser planificadas y acordadas entre el probador y la gestión apropiada.'
            },
        ]

        contador_creados = 0
        contador_existentes = 0

        for control_data in controles:
            control, created = ControlISO.objects.get_or_create(
                identificador=control_data['identificador'],
                defaults={
                    'nombre': control_data['nombre'],
                    'dominio': control_data['dominio'],
                    'descripcion_guia': control_data['descripcion_guia']
                }
            )
            
            if created:
                contador_creados += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Creado: {control.identificador} - {control.nombre}')
                )
            else:
                contador_existentes += 1
                self.stdout.write(
                    self.style.WARNING(f'• Ya existe: {control.identificador} - {control.nombre}')
                )

        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS(f'\n✓ Proceso completado'))
        self.stdout.write(f'  - Controles creados: {contador_creados}')
        self.stdout.write(f'  - Controles existentes: {contador_existentes}')
        self.stdout.write(f'  - Total procesados: {len(controles)}')
        self.stdout.write('='*60 + '\n')
