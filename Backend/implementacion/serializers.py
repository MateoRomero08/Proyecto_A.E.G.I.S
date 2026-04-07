from rest_framework import serializers
from .models import Empresa, ControlISO, EvaluacionControl, Evidencia


class EmpresaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Empresa
        fields = ['id', 'nombre', 'tipo', 'revision_solicitada', 'fecha_solicitud_revision']


class ControlISOSerializer(serializers.ModelSerializer):
    class Meta:
        model = ControlISO
        fields = ['id', 'identificador', 'nombre', 'dominio', 'descripcion_guia']


class EvidenciaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Evidencia
        fields = ['id', 'evaluacion', 'archivo', 'fecha_subida']
        read_only_fields = ['fecha_subida']


class EvaluacionControlSerializer(serializers.ModelSerializer):
    evidencias = EvidenciaSerializer(many=True, read_only=True)
    empresa_nombre = serializers.CharField(source='empresa.nombre', read_only=True)
    control_identificador = serializers.CharField(source='control.identificador', read_only=True)
    control_nombre = serializers.CharField(source='control.nombre', read_only=True)
    nombre_implementador = serializers.SerializerMethodField(read_only=True)
    evidencia = serializers.FileField(write_only=True, required=False, allow_null=True)
    evidencia_url = serializers.SerializerMethodField(read_only=True)
    evidencia_nombre = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = EvaluacionControl
        fields = [
            'id', 
            'empresa', 
            'empresa_nombre',
            'control', 
            'control_identificador',
            'control_nombre',
            'nombre_implementador',
            'estado', 
            'justificacion', 
            'evidencias',
            'evidencia',
            'evidencia_url',
            'evidencia_nombre'
        ]

    def validate(self, attrs):
        """
        En PATCH parcial no exigir empresa/control.
        En creación sí se requieren para mantener integridad.
        """
        if self.instance is None and not self.partial:
            if 'empresa' not in attrs:
                raise serializers.ValidationError({'empresa': 'Este campo es obligatorio.'})
            if 'control' not in attrs:
                raise serializers.ValidationError({'control': 'Este campo es obligatorio.'})

        # Campos inmutables una vez creada la evaluación
        if self.instance is not None:
            if 'empresa' in attrs and attrs['empresa'] != self.instance.empresa:
                raise serializers.ValidationError({'empresa': 'No se puede modificar la empresa de una evaluación existente.'})
            if 'control' in attrs and attrs['control'] != self.instance.control:
                raise serializers.ValidationError({'control': 'No se puede modificar el control de una evaluación existente.'})

        return attrs

    def get_nombre_implementador(self, obj):
        """Devuelve el nombre completo del usuario implementador si existe."""
        usuario = obj.usuario

        if not usuario:
            return None

        nombre_completo = usuario.get_full_name()
        return nombre_completo or usuario.username
    
    def get_evidencia_url(self, obj):
        """Devuelve la URL absoluta del archivo de evidencia o null si no existe"""
        evidencia = obj.evidencias.first()
        if evidencia and evidencia.archivo:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(evidencia.archivo.url)
            return evidencia.archivo.url
        return None
    
    def get_evidencia_nombre(self, obj):
        """Devuelve el nombre del archivo de evidencia o null si no existe"""
        evidencia = obj.evidencias.first()
        if evidencia and evidencia.archivo:
            import os
            return os.path.basename(evidencia.archivo.name)
        return None
    
    def create(self, validated_data):
        """Crea la evaluación y la evidencia si se proporciona un archivo"""
        evidencia_file = validated_data.pop('evidencia', None)
        evaluacion = EvaluacionControl.objects.create(**validated_data)
        
        if evidencia_file:
            Evidencia.objects.create(
                evaluacion=evaluacion,
                archivo=evidencia_file
            )
        
        return evaluacion
    
    def update(self, instance, validated_data):
        """Actualiza la evaluación y la evidencia si se proporciona un archivo"""
        evidencia_file = validated_data.pop('evidencia', None)
        
        # Actualizar campos de la evaluación
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Si se proporciona un nuevo archivo de evidencia
        if evidencia_file:
            # Eliminar evidencias anteriores (opcional, según tu lógica de negocio)
            instance.evidencias.all().delete()
            
            # Crear nueva evidencia
            Evidencia.objects.create(
                evaluacion=instance,
                archivo=evidencia_file
            )
        
        return instance
