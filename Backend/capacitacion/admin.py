from django.contrib import admin

from .models import CursoCapacitacion, ModuloContenido, ProgresoUsuario


class ModuloContenidoInline(admin.TabularInline):
    model = ModuloContenido
    extra = 0


@admin.register(CursoCapacitacion)
class CursoCapacitacionAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'titulo',
        'empresa',
        'creado_por_admin',
        'activo',
        'fecha_creacion',
    )
    list_filter = ('creado_por_admin', 'activo', 'empresa')
    search_fields = ('titulo', 'descripcion', 'empresa__nombre')
    ordering = ('-fecha_creacion',)
    inlines = [ModuloContenidoInline]


@admin.register(ModuloContenido)
class ModuloContenidoAdmin(admin.ModelAdmin):
    list_display = ('id', 'curso', 'orden', 'tipo', 'activo')
    list_filter = ('tipo', 'activo')
    search_fields = ('titulo', 'curso__titulo')
    ordering = ('curso', 'orden')


@admin.register(ProgresoUsuario)
class ProgresoUsuarioAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'usuario',
        'curso',
        'porcentaje_completado',
        'curso_completado',
        'fecha_ultima_actividad',
    )
    list_filter = ('curso_completado', 'curso__creado_por_admin')
    search_fields = ('usuario__username', 'curso__titulo')
    ordering = ('-fecha_ultima_actividad',)
