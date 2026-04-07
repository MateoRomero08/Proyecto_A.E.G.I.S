from django.contrib.auth import get_user_model
from django.contrib.auth.signals import user_logged_in, user_login_failed, user_logged_out
from django.dispatch import receiver

from .models import BitacoraSeguridadUsuario

User = get_user_model()


def _extract_client_ip(request):
    if request is None:
        return None

    forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if forwarded_for:
        return forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


def _extract_user_agent(request):
    if request is None:
        return ''
    return (request.META.get('HTTP_USER_AGENT') or '')[:512]


@receiver(user_logged_in)
def registrar_login_exitoso(sender, request, user, **kwargs):
    if not user:
        return

    BitacoraSeguridadUsuario.objects.create(
        actor=user,
        usuario_objetivo=user,
        empresa=getattr(user, 'empresa', None),
        accion='LOGIN_EXITOSO',
        detalle={
            'mensaje': 'Autenticación correcta.',
        },
        ip_origen=_extract_client_ip(request),
        user_agent=_extract_user_agent(request),
    )


@receiver(user_logged_out)
def registrar_logout(sender, request, user, **kwargs):
    if not user:
        return

    BitacoraSeguridadUsuario.objects.create(
        actor=user,
        usuario_objetivo=user,
        empresa=getattr(user, 'empresa', None),
        accion='LOGOUT',
        detalle={
            'mensaje': 'Cierre de sesión exitoso.',
        },
        ip_origen=_extract_client_ip(request),
        user_agent=_extract_user_agent(request),
    )


@receiver(user_login_failed)
def registrar_login_fallido(sender, credentials, request, **kwargs):
    username_intentado = (credentials or {}).get('username', '')
    email_intentado = (credentials or {}).get('email', '')

    usuario_objetivo = None
    if username_intentado:
        usuario_objetivo = User.objects.filter(username__iexact=username_intentado).first()
    elif email_intentado:
        usuario_objetivo = User.objects.filter(email__iexact=email_intentado).first()

    BitacoraSeguridadUsuario.objects.create(
        actor=usuario_objetivo,
        usuario_objetivo=usuario_objetivo,
        empresa=getattr(usuario_objetivo, 'empresa', None),
        accion='LOGIN_FALLIDO',
        detalle={
            'username_intentado': username_intentado,
            'email_intentado': email_intentado,
            'mensaje': 'Intento de autenticación fallido.',
        },
        ip_origen=_extract_client_ip(request),
        user_agent=_extract_user_agent(request),
    )
