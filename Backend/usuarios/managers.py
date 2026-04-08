from django.contrib.auth.models import BaseUserManager


class UsuarioCustomManager(BaseUserManager):
    """
    Manager personalizado para el modelo UsuarioCustom.
    Proporciona métodos para crear usuarios y superusuarios.
    """
    
    def create_user(self, username, email=None, password=None, **extra_fields):
        """
        Crea y guarda un usuario regular con el username, email y password proporcionados.
        """
        if not username:
            raise ValueError('El usuario debe tener un nombre de usuario')
        
        email = self.normalize_email(email) if email else None
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, username, email=None, password=None, **extra_fields):
        """
        Crea y guarda un superusuario con el username, email y password proporcionados.
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('is_approved', True)
        extra_fields.setdefault('es_administrador_empresa', True)
        extra_fields.setdefault('empresa', None)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('El superusuario debe tener is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('El superusuario debe tener is_superuser=True.')
        
        return self.create_user(username, email, password, **extra_fields)
    
    def implementadores(self):
        """Retorna todos los usuarios con rol de IMPLEMENTADOR"""
        return self.filter(rol='IMPLEMENTADOR')
    
    def auditores(self):
        """Retorna todos los usuarios con rol de AUDITOR (incluye legacy)."""
        return self.filter(rol__in=['AUDITOR', 'AUDITOR_INTERNO'])

    def lideres_equipo(self):
        """Retorna usuarios con rol de liderazgo operativo de equipo."""
        return self.filter(rol='LIDER_EQUIPO')

    def capacitadores(self):
        """Retorna usuarios con rol de capacitador."""
        return self.filter(rol='CAPACITADOR')
    
    def por_empresa(self, empresa):
        """Retorna todos los usuarios de una empresa específica"""
        return self.filter(empresa=empresa)
