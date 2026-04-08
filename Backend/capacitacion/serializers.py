from rest_framework import serializers

from .models import CursoCapacitacion, ModuloContenido, ProgresoUsuario


class ModuloContenidoSerializer(serializers.ModelSerializer):
    curso_titulo = serializers.CharField(source='curso.titulo', read_only=True)

    class Meta:
        model = ModuloContenido
        fields = [
            'id',
            'curso',
            'curso_titulo',
            'titulo',
            'descripcion',
            'tipo',
            'url_recurso',
            'orden',
            'duracion_minutos',
            'activo',
            'fecha_creacion',
        ]
        read_only_fields = ['fecha_creacion']


class ProgresoUsuarioSerializer(serializers.ModelSerializer):
    modulos_completados = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    modulos_completados_count = serializers.SerializerMethodField()
    total_modulos = serializers.SerializerMethodField()

    class Meta:
        model = ProgresoUsuario
        fields = [
            'id',
            'usuario',
            'curso',
            'modulos_completados',
            'modulos_completados_count',
            'total_modulos',
            'porcentaje_completado',
            'curso_completado',
            'fecha_ultima_actividad',
            'fecha_completado',
        ]
        read_only_fields = [
            'usuario',
            'curso',
            'porcentaje_completado',
            'curso_completado',
            'fecha_ultima_actividad',
            'fecha_completado',
        ]

    def get_modulos_completados_count(self, obj):
        return obj.modulos_completados.filter(curso=obj.curso, activo=True).count()

    def get_total_modulos(self, obj):
        return obj.curso.modulos.filter(activo=True).count()


class CursoCapacitacionWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = CursoCapacitacion
        fields = ['id', 'titulo', 'descripcion', 'activo']


class CursoCapacitacionSerializer(serializers.ModelSerializer):
    empresa_nombre = serializers.CharField(source='empresa.nombre', read_only=True)
    modulos = ModuloContenidoSerializer(many=True, read_only=True)
    es_oficial_aegis = serializers.SerializerMethodField()
    progreso = serializers.SerializerMethodField()
    total_modulos = serializers.SerializerMethodField()

    class Meta:
        model = CursoCapacitacion
        fields = [
            'id',
            'titulo',
            'descripcion',
            'empresa',
            'empresa_nombre',
            'creado_por_admin',
            'es_oficial_aegis',
            'activo',
            'fecha_creacion',
            'fecha_actualizacion',
            'total_modulos',
            'modulos',
            'progreso',
        ]

    def get_es_oficial_aegis(self, obj):
        return bool(obj.creado_por_admin)

    def get_total_modulos(self, obj):
        return obj.modulos.filter(activo=True).count()

    def get_progreso(self, obj):
        request = self.context.get('request')
        user = getattr(request, 'user', None)
        total_modulos = self.get_total_modulos(obj)

        progreso_base = {
            'id': None,
            'porcentaje_completado': 0,
            'curso_completado': False,
            'modulos_completados': [],
            'modulos_completados_count': 0,
            'total_modulos': total_modulos,
            'fecha_completado': None,
        }

        if (
            not user
            or not user.is_authenticated
            or user.is_superuser
            or getattr(user, 'rol', None) == 'ADMIN_SISTEMA'
        ):
            return progreso_base

        progreso_obj = None
        progreso_prefetch = getattr(obj, 'progreso_usuario_actual', None)
        if progreso_prefetch:
            progreso_obj = progreso_prefetch[0]
        else:
            progreso_obj = ProgresoUsuario.objects.filter(usuario=user, curso=obj).first()

        if not progreso_obj:
            return progreso_base

        modulos_ids = list(
            progreso_obj.modulos_completados.filter(curso=obj, activo=True).values_list('id', flat=True)
        )

        return {
            'id': progreso_obj.id,
            'porcentaje_completado': progreso_obj.porcentaje_completado,
            'curso_completado': progreso_obj.curso_completado,
            'modulos_completados': modulos_ids,
            'modulos_completados_count': len(modulos_ids),
            'total_modulos': total_modulos,
            'fecha_completado': progreso_obj.fecha_completado,
        }
