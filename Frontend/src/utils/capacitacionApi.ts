import { apiFetch } from './api';

export type TipoModulo = 'VIDEO' | 'PDF' | 'CUESTIONARIO';

export interface ModuloContenido {
  id: number;
  curso: number;
  curso_titulo?: string;
  titulo: string;
  descripcion: string;
  tipo: TipoModulo;
  url_recurso: string;
  orden: number;
  duracion_minutos: number;
  activo: boolean;
}

export interface ProgresoCurso {
  id: number | null;
  porcentaje_completado: number;
  curso_completado: boolean;
  modulos_completados: number[];
  modulos_completados_count: number;
  total_modulos: number;
  fecha_completado: string | null;
}

export interface CursoCapacitacion {
  id: number;
  titulo: string;
  descripcion: string;
  empresa: number | null;
  empresa_nombre: string | null;
  creado_por_admin: boolean;
  es_oficial_aegis: boolean;
  activo: boolean;
  fecha_creacion: string;
  fecha_actualizacion: string;
  total_modulos: number;
  modulos: ModuloContenido[];
  progreso: ProgresoCurso;
}

export interface CrearCursoPayload {
  titulo: string;
  descripcion: string;
  activo?: boolean;
}

export interface CrearModuloPayload {
  curso: number;
  titulo: string;
  descripcion: string;
  tipo: TipoModulo;
  url_recurso: string;
  orden: number;
  duracion_minutos: number;
  activo?: boolean;
}

export interface ActualizarProgresoPayload {
  modulo_id: number;
  completado: boolean;
}

export interface ActualizarProgresoResponse {
  detail: string;
  curso_id: number;
  progreso: {
    id: number;
    usuario: number;
    curso: number;
    modulos_completados: number[];
    modulos_completados_count: number;
    total_modulos: number;
    porcentaje_completado: number;
    curso_completado: boolean;
    fecha_ultima_actividad: string;
    fecha_completado: string | null;
  };
}

export const listarCursosCapacitacion = () =>
  apiFetch<CursoCapacitacion[]>('/capacitacion/cursos/');

export const crearCursoCapacitacion = (payload: CrearCursoPayload) =>
  apiFetch<CursoCapacitacion>('/capacitacion/cursos/', {
    method: 'POST',
    body: JSON.stringify({
      ...payload,
      activo: payload.activo ?? true,
    }),
  });

export const crearModuloContenido = (payload: CrearModuloPayload) =>
  apiFetch<ModuloContenido>('/capacitacion/modulos/', {
    method: 'POST',
    body: JSON.stringify({
      ...payload,
      activo: payload.activo ?? true,
    }),
  });

export const actualizarProgresoCurso = (cursoId: number, payload: ActualizarProgresoPayload) =>
  apiFetch<ActualizarProgresoResponse>(`/capacitacion/cursos/${cursoId}/progreso/`, {
    method: 'POST',
    body: JSON.stringify(payload),
  });

export const eliminarCurso = (id: number) =>
  apiFetch(`/capacitacion/cursos/${id}/`, {
    method: 'DELETE',
  });

export const eliminarModulo = (id: number) =>
  apiFetch(`/capacitacion/modulos/${id}/`, {
    method: 'DELETE',
  });
