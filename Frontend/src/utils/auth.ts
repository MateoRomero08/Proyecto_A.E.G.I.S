// src/utils/auth.ts
/**
 * Utilidades para manejo de autenticación en el frontend
 */

// Claves de localStorage
const TOKEN_KEY = 'token_acceso';
const USER_KEY = 'usuario_info';

export type RolUsuario = 'EMPLEADO' | 'IMPLEMENTADOR' | 'AUDITOR' | 'LIDER_EQUIPO' | 'CAPACITADOR';
type RolUsuarioBackend = RolUsuario | 'AUDITOR_INTERNO';

export const PERMISOS_FRONTEND = {
  VER_DASHBOARD: 'frontend.view_dashboard',
  VER_IMPLEMENTACION: 'frontend.view_implementacion',
  VER_AUDITORIA: 'frontend.view_auditoria',
  VER_CAPACITACION: 'frontend.view_capacitacion',
  VER_EQUIPO: 'frontend.view_equipo',
  VER_REPORTES: 'frontend.view_reportes',
  VER_USUARIOS_GLOBALES: 'frontend.view_usuarios_globales',
} as const;

export type UsuarioAuthShape = {
  [key: string]: any;
  rol?: RolUsuarioBackend;
  permisos?: string[];
  is_superuser?: boolean;
  is_staff?: boolean;
  is_approved?: boolean;
  es_administrador_empresa?: boolean;
};

const ALIAS_PERMISOS: Record<string, string[]> = {
  'capacitacion.add_cursocapacitacion': ['capacitacion.add_curso'],
  'capacitacion.change_cursocapacitacion': ['capacitacion.change_curso'],
  'capacitacion.add_curso': ['capacitacion.add_cursocapacitacion'],
  'capacitacion.change_curso': ['capacitacion.change_cursocapacitacion'],
};

const normalizarPermisos = (permisos: unknown): string[] => {
  if (!Array.isArray(permisos)) {
    return [];
  }

  const valoresValidos = permisos
    .filter((permiso): permiso is string => typeof permiso === 'string')
    .map((permiso) => permiso.trim())
    .filter(Boolean);

  const expandidos = valoresValidos.flatMap((permiso) => [permiso, ...(ALIAS_PERMISOS[permiso] || [])]);

  return Array.from(new Set(expandidos));
};

const permisosCompatibilidadPorRol = (rol: RolUsuario | null, isSuperuser: boolean): string[] => {
  if (isSuperuser) {
    return [
      PERMISOS_FRONTEND.VER_DASHBOARD,
      PERMISOS_FRONTEND.VER_USUARIOS_GLOBALES,
      PERMISOS_FRONTEND.VER_EQUIPO,
      PERMISOS_FRONTEND.VER_REPORTES,
      PERMISOS_FRONTEND.VER_CAPACITACION,
    ];
  }

  switch (rol) {
    case 'LIDER_EQUIPO':
      return [
        PERMISOS_FRONTEND.VER_DASHBOARD,
        PERMISOS_FRONTEND.VER_EQUIPO,
        PERMISOS_FRONTEND.VER_REPORTES,
      ];
    case 'IMPLEMENTADOR':
      return [
        PERMISOS_FRONTEND.VER_DASHBOARD,
        PERMISOS_FRONTEND.VER_IMPLEMENTACION,
        PERMISOS_FRONTEND.VER_CAPACITACION,
      ];
    case 'AUDITOR':
      return [
        PERMISOS_FRONTEND.VER_DASHBOARD,
        PERMISOS_FRONTEND.VER_AUDITORIA,
        PERMISOS_FRONTEND.VER_CAPACITACION,
      ];
    case 'CAPACITADOR':
    case 'EMPLEADO':
      return [
        PERMISOS_FRONTEND.VER_DASHBOARD,
        PERMISOS_FRONTEND.VER_CAPACITACION,
      ];
    default:
      return [PERMISOS_FRONTEND.VER_DASHBOARD];
  }
};

const normalizarRol = (rol?: string): RolUsuario | null => {
  if (!rol) {
    return null;
  }

  if (rol === 'AUDITOR_INTERNO') {
    return 'AUDITOR';
  }

  if (rol === 'EMPLEADO' || rol === 'IMPLEMENTADOR' || rol === 'AUDITOR' || rol === 'LIDER_EQUIPO' || rol === 'CAPACITADOR') {
    return rol;
  }

  return null;
};

const normalizarUsuarioAuth = (usuario: UsuarioAuthShape | null): UsuarioAuthShape | null => {
  if (!usuario || typeof usuario !== 'object') {
    return null;
  }

  const isSuperuser = Boolean(usuario.is_superuser);
  const rolNormalizado = normalizarRol(String(usuario.rol || ''));
  const rolFinal: RolUsuario | null = (!isSuperuser && (rolNormalizado === null && usuario.es_administrador_empresa))
    ? 'LIDER_EQUIPO'
    : rolNormalizado;
  const esLider = rolFinal === 'LIDER_EQUIPO';
  const permisosBackend = normalizarPermisos(usuario.permisos);
  // Compatibilidad con sesiones persistidas previas al campo `permisos`.
  const permisosCompatibilidad = permisosBackend.length === 0
    ? permisosCompatibilidadPorRol(rolFinal, isSuperuser)
    : [];
  const permisosFinales = Array.from(new Set([...permisosBackend, ...permisosCompatibilidad]));

  return {
    ...usuario,
    rol: rolFinal ?? undefined,
    permisos: permisosFinales,
    is_superuser: isSuperuser,
    is_staff: Boolean(usuario.is_staff),
    is_approved: Boolean(isSuperuser || usuario.is_approved),
    es_administrador_empresa: Boolean(isSuperuser || esLider || usuario.es_administrador_empresa),
  };
};

/**
 * Guarda el token de acceso en localStorage
 */
export const guardarToken = (token: string): void => {
  localStorage.setItem(TOKEN_KEY, token);
};

/**
 * Obtiene el token de acceso desde localStorage
 */
export const obtenerToken = (): string | null => {
  return localStorage.getItem(TOKEN_KEY);
};

/**
 * Elimina el token de acceso de localStorage
 */
export const eliminarToken = (): void => {
  localStorage.removeItem(TOKEN_KEY);
};

/**
 * Verifica si hay un token guardado
 */
export const tieneToken = (): boolean => {
  return !!obtenerToken();
};

/**
 * Guarda la información del usuario en localStorage
 */
export const guardarUsuario = (usuario: any): void => {
  const normalizado = normalizarUsuarioAuth(usuario);
  if (!normalizado) {
    localStorage.removeItem(USER_KEY);
    return;
  }
  localStorage.setItem(USER_KEY, JSON.stringify(normalizado));
};

/**
 * Obtiene la información del usuario desde localStorage
 */
export const obtenerUsuario = (): any | null => {
  const usuario = localStorage.getItem(USER_KEY);
  if (!usuario) {
    return null;
  }

  try {
    return normalizarUsuarioAuth(JSON.parse(usuario));
  } catch {
    return null;
  }
};

/**
 * Verifica si el usuario actual ya fue aprobado por su empresa.
 */
export const estaAprobadoUsuario = (): boolean => {
  const usuario = obtenerUsuario();
  if (!usuario) return false;
  if (usuario.is_superuser) return true;
  return Boolean(usuario.is_approved);
};

/**
 * Verifica si el usuario actual administra su equipo.
 */
export const esAdministradorEmpresa = (): boolean => {
  const usuario = obtenerUsuario();
  if (!usuario) return false;
  if (usuario.is_superuser) return true;
  return Boolean(usuario.es_administrador_empresa || usuario.rol === 'LIDER_EQUIPO');
};

/**
 * Verifica si el usuario actual es superusuario global.
 */
export const esSuperusuario = (): boolean => {
  const usuario = obtenerUsuario();
  return Boolean(usuario?.is_superuser);
};

/**
 * Elimina la información del usuario de localStorage
 */
export const eliminarUsuario = (): void => {
  localStorage.removeItem(USER_KEY);
};

/**
 * Limpia completamente la sesión (token + usuario)
 */
export const cerrarSesion = (): void => {
  eliminarToken();
  eliminarUsuario();
};

/**
 * Cierra sesión contra backend (para trazabilidad) y limpia sesión local.
 */
export const cerrarSesionRemota = async (): Promise<void> => {
  const token = obtenerToken();

  try {
    if (token) {
      await fetch('http://localhost:8000/api/usuarios/logout/', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });
    }
  } catch (error) {
    console.warn('No fue posible registrar el logout remoto:', error);
  } finally {
    cerrarSesion();
  }
};

/**
 * Verifica si el usuario está autenticado
 */
export const estaAutenticado = (): boolean => {
  return tieneToken() && obtenerUsuario() !== null;
};

/**
 * Obtiene el listado de permisos del usuario autenticado.
 */
export const obtenerPermisosUsuario = (): string[] => {
  const usuario = obtenerUsuario();
  return normalizarPermisos(usuario?.permisos);
};

/**
 * Verifica si el usuario posee alguno de los permisos esperados (OR lógico).
 */
export const tienePermisoUsuario = (
  permisoEsperado: string | string[],
  usuarioEntrada?: UsuarioAuthShape | null,
): boolean => {
  const usuario = normalizarUsuarioAuth(usuarioEntrada ?? obtenerUsuario());
  if (!usuario) {
    return false;
  }

  const permisosUsuario = normalizarPermisos(usuario.permisos);
  if (!permisoEsperado) {
    return true;
  }

  if (Array.isArray(permisoEsperado)) {
    return permisoEsperado.some((permiso) => permisosUsuario.includes(permiso));
  }

  return permisosUsuario.includes(permisoEsperado);
};

/**
 * Obtiene el rol del usuario actual
 */
export const obtenerRolUsuario = (): RolUsuario | null => {
  const usuario = obtenerUsuario();
  return normalizarRol(usuario?.rol) || null;
};

/**
 * Verifica si el usuario es un implementador
 */
export const esImplementador = (): boolean => {
  return obtenerRolUsuario() === 'IMPLEMENTADOR';
};

/**
 * Verifica si el usuario es empleado.
 */
export const esEmpleado = (): boolean => {
  return obtenerRolUsuario() === 'EMPLEADO';
};

/**
 * Verifica si el usuario es un auditor
 */
export const esAuditor = (): boolean => {
  return obtenerRolUsuario() === 'AUDITOR';
};

/**
 * Verifica si el usuario es líder de equipo.
 */
export const esLiderEquipo = (): boolean => {
  return obtenerRolUsuario() === 'LIDER_EQUIPO';
};

/**
 * Verifica si el usuario es capacitador.
 */
export const esCapacitador = (): boolean => {
  return obtenerRolUsuario() === 'CAPACITADOR';
};

const RUTAS_SUPERADMIN = [
  '/dashboard',
  '/dashboard/usuarios',
  '/dashboard/equipo',
  '/dashboard/reportes',
  '/dashboard/capacitacion',
];

const REGLAS_RUTA_DASHBOARD: Array<{
  rutaBase: string;
  permisos: string | string[];
}> = [
  { rutaBase: '/dashboard/usuarios', permisos: PERMISOS_FRONTEND.VER_USUARIOS_GLOBALES },
  { rutaBase: '/dashboard/implementacion', permisos: PERMISOS_FRONTEND.VER_IMPLEMENTACION },
  { rutaBase: '/dashboard/auditorias', permisos: PERMISOS_FRONTEND.VER_AUDITORIA },
  { rutaBase: '/dashboard/auditoria/proceso', permisos: PERMISOS_FRONTEND.VER_AUDITORIA },
  { rutaBase: '/dashboard/equipo', permisos: PERMISOS_FRONTEND.VER_EQUIPO },
  { rutaBase: '/dashboard/reportes', permisos: PERMISOS_FRONTEND.VER_REPORTES },
  { rutaBase: '/dashboard/capacitacion', permisos: PERMISOS_FRONTEND.VER_CAPACITACION },
  { rutaBase: '/dashboard', permisos: PERMISOS_FRONTEND.VER_DASHBOARD },
];

const coincideRuta = (pathname: string, rutaBase: string): boolean => {
  if (rutaBase === '/dashboard') {
    return pathname === '/dashboard';
  }

  if (rutaBase === '/dashboard/auditoria/proceso') {
    return pathname.startsWith('/dashboard/auditoria/proceso/');
  }

  return pathname === rutaBase || pathname.startsWith(`${rutaBase}/`);
};

/**
 * Matriz RBAC de rutas privadas de dashboard.
 */
export const tieneAccesoRutaDashboard = (
  pathname: string,
  usuarioEntrada?: UsuarioAuthShape | null,
): boolean => {
  if (!pathname.startsWith('/dashboard')) {
    return true;
  }

  const usuario = normalizarUsuarioAuth(usuarioEntrada ?? obtenerUsuario());
  if (!usuario) {
    return false;
  }

  if (usuario.is_superuser) {
    return RUTAS_SUPERADMIN.some((ruta) => coincideRuta(pathname, ruta));
  }

  const reglaRuta = REGLAS_RUTA_DASHBOARD.find((regla) => coincideRuta(pathname, regla.rutaBase));

  if (!reglaRuta) {
    return false;
  }

  return tienePermisoUsuario(reglaRuta.permisos, usuario);
};

/**
 * Obtiene la empresa del usuario actual
 */
export const obtenerEmpresaUsuario = (): any | null => {
  const usuario = obtenerUsuario();
  return usuario?.empresa_info || null;
};

/**
 * Verifica si el usuario tiene una empresa asignada
 */
export const tieneEmpresa = (): boolean => {
  return obtenerEmpresaUsuario() !== null;
};

/**
 * Redirige al login y limpia la sesión
 */
export const redirigirALogin = (): void => {
  cerrarSesion();
  window.location.href = '/login';
};

/**
 * Inicia sesión enviando credenciales al backend y guardando el token
 */
export const iniciarSesion = async (username: string, password: string): Promise<any> => {
  try {
    const response = await fetch('http://localhost:8000/api/usuarios/login/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        username,
        password,
      }),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Error al iniciar sesión');
    }

    const data = await response.json();
    
    // Guardar el token de acceso
    guardarToken(data.access);
    
    // Obtener el perfil del usuario usando el token
    const perfilResponse = await fetch('http://localhost:8000/api/usuarios/perfil/', {
      method: 'GET',
      headers: {
        'Authorization': 'Bearer ' + data.access,
        'Content-Type': 'application/json',
      },
    });

    if (!perfilResponse.ok) {
      throw new Error('Error al obtener el perfil del usuario');
    }

    const perfilData = await perfilResponse.json();
    const usuarioDesdeLogin = normalizarUsuarioAuth(data?.usuario ?? null);
    const usuarioFinal = normalizarUsuarioAuth({
      ...(usuarioDesdeLogin || {}),
      ...(perfilData || {}),
    });
    
    // Guardar la información del usuario en localStorage
    guardarUsuario(usuarioFinal);
    
    return usuarioFinal;
    
  } catch (error) {
    throw error;
  }
};
