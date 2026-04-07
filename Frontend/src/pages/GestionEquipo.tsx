import { useEffect, useMemo, useState } from "react";
import { CheckCircle2, Clock3, UserX, Users } from "lucide-react";
import { apiFetch } from "../utils/api";
import { esAdministradorEmpresa, obtenerUsuario } from "../utils/auth";
import { RoleBadge } from "../components/RoleBadge";

interface UsuarioEquipo {
  id: number;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  rol: "EMPLEADO" | "IMPLEMENTADOR" | "AUDITOR" | "LIDER_EQUIPO" | "CAPACITADOR";
  rol_display: string;
  is_superuser?: boolean;
  is_active: boolean;
  is_approved: boolean;
  es_administrador_empresa: boolean;
  date_joined: string;
}

export function GestionEquipo() {
  const [usuarios, setUsuarios] = useState<UsuarioEquipo[]>([]);
  const [cargando, setCargando] = useState(true);
  const [accionandoId, setAccionandoId] = useState<number | null>(null);
  const [error, setError] = useState<string>("");
  const [filtro, setFiltro] = useState<"TODOS" | "PENDIENTES">("TODOS");

  const usuarioActual = obtenerUsuario();
  const liderEquipo = esAdministradorEmpresa();

  const pendientes = useMemo(
    () => usuarios.filter((usuario) => !usuario.is_approved && usuario.is_active),
    [usuarios]
  );

  const usuariosFiltrados = useMemo(() => {
    if (filtro === "PENDIENTES") {
      return usuarios.filter((usuario) => !usuario.is_approved && usuario.is_active);
    }
    return usuarios;
  }, [usuarios, filtro]);

  const cargarEquipo = async () => {
    setCargando(true);
    setError("");
    try {
      const data = await apiFetch<UsuarioEquipo[]>("/usuarios/equipo/");
      setUsuarios(data);
    } catch (err: any) {
      setError(err?.message || "No se pudo cargar el equipo.");
    } finally {
      setCargando(false);
    }
  };

  useEffect(() => {
    cargarEquipo();
  }, []);

  const aprobarUsuario = async (userId: number) => {
    setAccionandoId(userId);
    try {
      await apiFetch(`/usuarios/equipo/${userId}/aprobar/`, { method: "POST" });
      await cargarEquipo();
    } catch (err: any) {
      alert(err?.message || "No fue posible aprobar al usuario.");
    } finally {
      setAccionandoId(null);
    }
  };

  const rechazarUsuario = async (userId: number) => {
    const confirmar = window.confirm("¿Seguro que deseas rechazar este usuario? La cuenta quedará inactiva.");
    if (!confirmar) return;

    setAccionandoId(userId);
    try {
      await apiFetch(`/usuarios/equipo/${userId}/rechazar/`, { method: "POST" });
      await cargarEquipo();
    } catch (err: any) {
      alert(err?.message || "No fue posible rechazar al usuario.");
    } finally {
      setAccionandoId(null);
    }
  };

  if (!liderEquipo && !usuarioActual?.is_superuser) {
    return (
      <div className="bg-yellow-50 border border-yellow-200 rounded-xl p-6">
        <h1 className="text-2xl font-bold text-yellow-900">Gestión de Equipo</h1>
        <p className="text-yellow-800 mt-2">
          Esta sección está disponible únicamente para líderes de equipo.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Gestión de Equipo</h1>
          <p className="text-gray-600 mt-1">
            {usuarioActual?.is_superuser
              ? "Vista global: administra usuarios y aprobaciones de todas las empresas."
              : "Aprueba o rechaza usuarios pendientes de tu empresa."}
          </p>

          <div className="mt-4 inline-flex items-center rounded-lg border border-gray-200 bg-white p-1 shadow-sm">
            <button
              onClick={() => setFiltro("TODOS")}
              className={`px-3 py-1.5 text-sm font-semibold rounded-md transition-colors ${
                filtro === "TODOS"
                  ? "bg-slate-800 text-white"
                  : "text-slate-600 hover:bg-slate-100"
              }`}
            >
              Todos
            </button>
            <button
              onClick={() => setFiltro("PENDIENTES")}
              className={`px-3 py-1.5 text-sm font-semibold rounded-md transition-colors ${
                filtro === "PENDIENTES"
                  ? "bg-yellow-500 text-black"
                  : "text-slate-600 hover:bg-slate-100"
              }`}
            >
              Solo pendientes
            </button>
          </div>
        </div>
        <div className="bg-white rounded-lg border border-gray-200 px-4 py-3 shadow-sm">
          <div className="text-sm text-gray-600">Pendientes</div>
          <div className="text-2xl font-bold text-yellow-600">{pendientes.length}</div>
        </div>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">
          {error}
        </div>
      )}

      <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full min-w-[860px]">
            <thead className="bg-slate-700 text-white">
              <tr>
                <th className="px-6 py-4 text-left text-xs font-bold uppercase tracking-wider">Usuario</th>
                <th className="px-6 py-4 text-left text-xs font-bold uppercase tracking-wider">Rol</th>
                <th className="px-6 py-4 text-left text-xs font-bold uppercase tracking-wider">Estado</th>
                <th className="px-6 py-4 text-left text-xs font-bold uppercase tracking-wider">Registro</th>
                <th className="px-6 py-4 text-left text-xs font-bold uppercase tracking-wider">Acciones</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {cargando ? (
                <tr>
                  <td colSpan={5} className="px-6 py-8 text-center text-gray-500">
                    Cargando usuarios...
                  </td>
                </tr>
              ) : usuariosFiltrados.length === 0 ? (
                <tr>
                  <td colSpan={5} className="px-6 py-8 text-center text-gray-500">
                    {filtro === "PENDIENTES"
                      ? "No hay usuarios pendientes por aprobar."
                      : "No hay usuarios registrados en tu empresa."}
                  </td>
                </tr>
              ) : (
                usuariosFiltrados.map((usuario) => {
                  const nombre = `${usuario.first_name} ${usuario.last_name}`.trim() || usuario.username;
                  const esYo = usuarioActual?.id === usuario.id;
                  const pendiente = !usuario.is_approved && usuario.is_active;

                  return (
                    <tr key={usuario.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-3">
                          <div className="w-10 h-10 rounded-full bg-slate-100 flex items-center justify-center text-slate-700">
                            <Users className="w-5 h-5" />
                          </div>
                          <div>
                            <div className="font-semibold text-gray-900">{nombre}</div>
                            <div className="text-sm text-gray-500">{usuario.email || "Sin correo"}</div>
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <RoleBadge
                          rol={usuario.rol}
                          isSuperuser={Boolean(usuario.is_superuser)}
                          isLeader={usuario.rol === "LIDER_EQUIPO" || usuario.es_administrador_empresa}
                        />
                      </td>
                      <td className="px-6 py-4">
                        {usuario.is_approved ? (
                          <span className="inline-flex items-center gap-1 text-xs font-semibold px-2.5 py-1 rounded-full border bg-green-50 text-green-700 border-green-200">
                            <CheckCircle2 className="w-3.5 h-3.5" />
                            Aprobado
                          </span>
                        ) : usuario.is_active ? (
                          <span className="inline-flex items-center gap-1 text-xs font-semibold px-2.5 py-1 rounded-full border bg-yellow-50 text-yellow-700 border-yellow-200">
                            <Clock3 className="w-3.5 h-3.5" />
                            Pendiente
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1 text-xs font-semibold px-2.5 py-1 rounded-full border bg-red-50 text-red-700 border-red-200">
                            <UserX className="w-3.5 h-3.5" />
                            Rechazado
                          </span>
                        )}
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-600">
                        {new Date(usuario.date_joined).toLocaleDateString()}
                      </td>
                      <td className="px-6 py-4">
                        {pendiente && !esYo ? (
                          <div className="flex items-center gap-2">
                            <button
                              onClick={() => aprobarUsuario(usuario.id)}
                              disabled={accionandoId === usuario.id}
                              className="inline-flex items-center gap-1 px-3 py-1.5 rounded-md bg-green-600 text-white text-xs font-semibold hover:bg-green-700 disabled:opacity-60"
                            >
                              Aprobar
                            </button>
                            <button
                              onClick={() => rechazarUsuario(usuario.id)}
                              disabled={accionandoId === usuario.id}
                              className="inline-flex items-center gap-1 px-3 py-1.5 rounded-md bg-red-600 text-white text-xs font-semibold hover:bg-red-700 disabled:opacity-60"
                            >
                              Rechazar
                            </button>
                          </div>
                        ) : (
                          <span className="text-xs text-gray-400">Sin acciones</span>
                        )}
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
