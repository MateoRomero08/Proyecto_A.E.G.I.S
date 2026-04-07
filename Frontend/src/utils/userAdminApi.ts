import { apiFetch } from "./api";

export interface EmpresaOption {
  id: number;
  nombre: string;
  tipo: string;
}

export interface GlobalUser {
  id: number;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  full_name: string;
  rol: "EMPLEADO" | "IMPLEMENTADOR" | "AUDITOR" | "LIDER_EQUIPO" | "CAPACITADOR";
  rol_display: string;
  empresa: number | null;
  empresa_info: EmpresaOption | null;
  is_active: boolean;
  is_approved: boolean;
  es_administrador_empresa: boolean;
  is_staff: boolean;
  is_superuser: boolean;
  date_joined: string;
  last_login: string | null;
  temporary_password?: string;
}

export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export interface GlobalUsersStats {
  total_users: number;
  active_users: number;
  global_admins: number;
  total_companies: number;
}

export interface GlobalUserPayload {
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  rol: "EMPLEADO" | "IMPLEMENTADOR" | "AUDITOR" | "LIDER_EQUIPO" | "CAPACITADOR";
  empresa: number | null;
  is_active: boolean;
  is_approved: boolean;
  es_administrador_empresa: boolean;
  password?: string;
}

export interface GlobalUsersQuery {
  page?: number;
  pageSize?: number;
  search?: string;
}

export type BitacoraAccion =
  | "CREACION_USUARIO"
  | "ACTUALIZACION_USUARIO"
  | "CAMBIO_ROL"
  | "INACTIVACION_USUARIO"
  | "RESET_PASSWORD_FORZADO"
  | "APROBACION_USUARIO"
  | "RECHAZO_USUARIO"
  | "LOGIN_EXITOSO"
  | "LOGIN_FALLIDO"
  | "LOGOUT";

export interface BitacoraUserRef {
  id: number;
  username: string;
  email: string;
  full_name: string;
}

export interface BitacoraEvento {
  id: number;
  accion: BitacoraAccion;
  accion_display: string;
  actor: number | null;
  actor_info: BitacoraUserRef | null;
  usuario_objetivo: number | null;
  usuario_objetivo_info: BitacoraUserRef | null;
  empresa: number | null;
  empresa_info: EmpresaOption | null;
  detalle: Record<string, unknown>;
  ip_origen: string | null;
  user_agent: string;
  fecha_evento: string;
}

export interface GlobalBitacoraQuery {
  page?: number;
  pageSize?: number;
  search?: string;
  accion?: BitacoraAccion | "";
  empresaId?: number;
  actorId?: number;
  fechaDesde?: string;
  fechaHasta?: string;
}

export const fetchGlobalUsers = async ({
  page = 1,
  pageSize = 10,
  search = "",
}: GlobalUsersQuery): Promise<PaginatedResponse<GlobalUser>> => {
  const params = new URLSearchParams();
  params.set("page", String(page));
  params.set("page_size", String(pageSize));
  if (search.trim()) {
    params.set("search", search.trim());
  }

  return apiFetch<PaginatedResponse<GlobalUser>>(`/usuarios/global/?${params.toString()}`);
};

export const fetchGlobalBitacora = async ({
  page = 1,
  pageSize = 20,
  search = "",
  accion = "",
  empresaId,
  actorId,
  fechaDesde,
  fechaHasta,
}: GlobalBitacoraQuery): Promise<PaginatedResponse<BitacoraEvento>> => {
  const params = new URLSearchParams();
  params.set("page", String(page));
  params.set("page_size", String(pageSize));

  if (search.trim()) {
    params.set("search", search.trim());
  }

  if (accion) {
    params.set("accion", accion);
  }

  if (typeof empresaId === "number") {
    params.set("empresa_id", String(empresaId));
  }

  if (typeof actorId === "number") {
    params.set("actor_id", String(actorId));
  }

  if (fechaDesde) {
    params.set("fecha_desde", fechaDesde);
  }

  if (fechaHasta) {
    params.set("fecha_hasta", fechaHasta);
  }

  return apiFetch<PaginatedResponse<BitacoraEvento>>(`/usuarios/bitacora/?${params.toString()}`);
};

export const fetchGlobalUsersStats = async (): Promise<GlobalUsersStats> => {
  return apiFetch<GlobalUsersStats>("/usuarios/global/stats/");
};

export const fetchEmpresasOptions = async (): Promise<EmpresaOption[]> => {
  return apiFetch<EmpresaOption[]>("/usuarios/global/empresas/");
};

export const createGlobalUser = async (payload: GlobalUserPayload): Promise<GlobalUser> => {
  return apiFetch<GlobalUser>("/usuarios/global/", {
    method: "POST",
    body: JSON.stringify(payload),
  });
};

export const updateGlobalUser = async (
  userId: number,
  payload: Partial<GlobalUserPayload>,
): Promise<GlobalUser> => {
  return apiFetch<GlobalUser>(`/usuarios/global/${userId}/`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
};

export const inactivateGlobalUser = async (userId: number): Promise<{ detail: string; usuario: GlobalUser }> => {
  return apiFetch<{ detail: string; usuario: GlobalUser }>(`/usuarios/global/${userId}/inactivar/`, {
    method: "PATCH",
  });
};

export const forceResetPassword = async (
  userId: number,
): Promise<{ detail: string; temporary_password: string; reset_link: string }> => {
  return apiFetch<{ detail: string; temporary_password: string; reset_link: string }>(
    `/usuarios/global/${userId}/forzar-reset-password/`,
    {
      method: "POST",
    },
  );
};
