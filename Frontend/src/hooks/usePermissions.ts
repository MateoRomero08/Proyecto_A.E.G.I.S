import { useCallback, useMemo } from "react";
import { obtenerPermisosUsuario, tienePermisoUsuario, type UsuarioAuthShape } from "../utils/auth";

export function usePermissions(usuarioEntrada?: UsuarioAuthShape | null) {
  const permisos = useMemo(() => {
    if (!usuarioEntrada) {
      return obtenerPermisosUsuario();
    }

    const permisosUsuario = Array.isArray(usuarioEntrada.permisos)
      ? usuarioEntrada.permisos
      : [];

    return Array.from(
      new Set(
        permisosUsuario.filter(
          (permiso): permiso is string => typeof permiso === "string" && permiso.trim().length > 0,
        ),
      ),
    );
  }, [usuarioEntrada]);

  const hasPermission = useCallback(
    (permisoEsperado: string | string[]) => tienePermisoUsuario(permisoEsperado, usuarioEntrada),
    [usuarioEntrada],
  );

  return {
    permisos,
    hasPermission,
  };
}
