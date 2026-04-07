from django.contrib import admin
from .models import Empresa, ControlISO, EvaluacionControl, Evidencia


@admin.register(Empresa)
class EmpresaAdmin(admin.ModelAdmin):
	list_display = ('id', 'nombre', 'tipo', 'revision_solicitada', 'fecha_solicitud_revision')
	search_fields = ('nombre',)
	list_filter = ('tipo',)


@admin.register(ControlISO)
class ControlISOAdmin(admin.ModelAdmin):
	list_display = ('id', 'identificador', 'nombre', 'dominio')
	search_fields = ('identificador', 'nombre')
	list_filter = ('dominio',)
	ordering = ('identificador',)


@admin.register(EvaluacionControl)
class EvaluacionControlAdmin(admin.ModelAdmin):
	list_display = ('empresa', 'control_identificador', 'estado', 'usuario')
	list_filter = ('estado', 'empresa')
	search_fields = ('empresa__nombre', 'control__identificador', 'control__nombre', 'usuario__username')
	autocomplete_fields = ('empresa', 'control', 'usuario')

	@admin.display(description='Control')
	def control_identificador(self, obj):
		return obj.control.identificador


@admin.register(Evidencia)
class EvidenciaAdmin(admin.ModelAdmin):
	list_display = ('id', 'evaluacion', 'fecha_subida')
	search_fields = ('evaluacion__empresa__nombre', 'evaluacion__control__identificador')
	list_filter = ('fecha_subida',)
	autocomplete_fields = ('evaluacion',)
