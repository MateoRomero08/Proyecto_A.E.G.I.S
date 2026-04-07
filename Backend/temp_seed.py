import random
from django.contrib.auth import get_user_model
from django.db import transaction
from rest_framework.test import APIRequestFactory, force_authenticate

from implementacion.models import Empresa, ControlISO, EvaluacionControl
from auditoria.models import ProcesoAuditoria
from auditoria.views import RevisionAuditoriaViewSet


User = get_user_model()

with transaction.atomic():
    # 1) Empresa de prueba
    empresa, _ = Empresa.objects.get_or_create(
        nombre="Empresa Demo QA",
        defaults={"tipo": "MEDIANA"},
    )

    # Usuario implementador (para EvaluacionControl.usuario)
    implementador, created_impl = User.objects.get_or_create(
        username="implementador_demo",
        defaults={
            "email": "implementador.demo@aegis.local",
            "first_name": "Imple",
            "last_name": "Demo",
            "rol": "IMPLEMENTADOR",
            "empresa": empresa,
            "is_active": True,
        },
    )
    if created_impl:
        implementador.set_password("Demo12345!")
    implementador.rol = "IMPLEMENTADOR"
    implementador.empresa = empresa
    implementador.is_active = True
    implementador.save()

    # Usuario auditor (para crear revisiones vía ViewSet y disparar snapshot)
    auditor, created_aud = User.objects.get_or_create(
        username="auditor_demo",
        defaults={
            "email": "auditor.demo@aegis.local",
            "first_name": "Auditor",
            "last_name": "Demo",
            "rol": "AUDITOR_INTERNO",
            "empresa": empresa,
            "is_active": True,
        },
    )
    if created_aud:
        auditor.set_password("Demo12345!")
    auditor.rol = "AUDITOR_INTERNO"
    auditor.empresa = empresa
    auditor.is_active = True
    auditor.save()

    # 1) Proceso de auditoría activo
    proceso = (
        ProcesoAuditoria.objects.filter(
            empresa=empresa,
            auditor=auditor,
            estado="ACTIVA",
        )
        .order_by("-id")
        .first()
    )
    if not proceso:
        proceso = ProcesoAuditoria.objects.create(
            nombre="Auditoría ISO 27001 - Prueba Automática",
            empresa=empresa,
            auditor=auditor,
            estado="ACTIVA",
            visible_para_auditor=True,
        )

    # 2) Recorrer controles ISO existentes
    controles = list(ControlISO.objects.all().order_by("identificador"))
    if not controles:
        raise RuntimeError("No hay controles ISO cargados en la base de datos.")

    if len(controles) != 93:
        print(f"Advertencia: se encontraron {len(controles)} controles (esperados: 93).")

    factory = APIRequestFactory()
    create_revision_view = RevisionAuditoriaViewSet.as_view({"post": "create"})

    estados = ["IMPLEMENTADO", "NO_APLICA"]
    veredictos = ["CONFORME", "NO_CONFORME"]

    procesados = 0

    for idx, control in enumerate(controles, start=1):
        estado = random.choice(estados)
        justificacion = (
            f"Justificación automática de prueba para {control.identificador} "
            f"(iteración {idx}, estado {estado})."
        )

        # Evaluación del implementador (se actualiza/crea para pruebas)
        evaluacion, _ = EvaluacionControl.objects.update_or_create(
            empresa=empresa,
            control=control,
            defaults={
                "estado": estado,
                "justificacion": justificacion,
                "usuario": implementador,
            },
        )

        # 3) Crear revisión usando el ViewSet para DISPARAR snapshot automático
        payload = {
            "proceso": proceso.id,
            "evaluacion_control": evaluacion.id,
            "veredicto": random.choice(veredictos),
            "observaciones": f"Observación automática de auditoría para {control.identificador}.",
        }

        request = factory.post("/api/auditoria/revisiones/", payload, format="json")
        force_authenticate(request, user=auditor)
        response = create_revision_view(request)

        if response.status_code not in (200, 201):
            raise RuntimeError(
                f"Error creando revisión para control {control.identificador}: "
                f"{response.status_code} - {getattr(response, 'data', None)}"
            )

        procesados += 1

    proceso.refresh_from_db()
    print(f"Controles procesados: {procesados}")
    print(f"Progreso del proceso: {proceso.progreso_porcentaje()}%")

print("¡Auditoría de prueba completada al 100%!")