from django.apps import AppConfig


class UsuariosConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'usuarios'

    def ready(self):
        # Import tardío para registrar receivers de señales de autenticación.
        import usuarios.signals  # noqa: F401
