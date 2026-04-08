import { useEffect, useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";
import {
  Building2,
  CheckCircle2,
  History,
  KeyRound,
  Loader2,
  Pencil,
  Plus,
  Power,
  Search,
  Shield,
  ShieldCheck,
  UserRound,
  Users,
} from "lucide-react";
import { toast } from "sonner";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "../app/components/ui/dialog";
import { Tooltip, TooltipContent, TooltipTrigger } from "../app/components/ui/tooltip";
import { Skeleton } from "../app/components/ui/skeleton";
import { Badge } from "../app/components/ui/badge";
import { RoleBadge } from "../components/RoleBadge";
import { esAdminSistema, esSuperusuario, obtenerUsuario } from "../utils/auth";
import {
  BitacoraAccion,
  BitacoraEvento,
  createGlobalUser,
  EmpresaOption,
  fetchEmpresasOptions,
  fetchGlobalBitacora,
  fetchGlobalUsers,
  fetchGlobalUsersStats,
  forceResetPassword,
  GlobalUser,
  GlobalUserPayload,
  GlobalUsersStats,
  inactivateGlobalUser,
  updateGlobalUser,
} from "../utils/userAdminApi";

type GlobalUserForm = {
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  rol: "EMPLEADO" | "IMPLEMENTADOR" | "AUDITOR" | "LIDER_EQUIPO" | "CAPACITADOR" | "ADMIN_SISTEMA";
  empresa: number | null;
  is_active: boolean;
  is_approved: boolean;
  es_administrador_empresa: boolean;
  password: string;
};

const INITIAL_FORM: GlobalUserForm = {
  username: "",
  email: "",
  first_name: "",
  last_name: "",
  rol: "EMPLEADO",
  empresa: null,
  is_active: true,
  is_approved: true,
  es_administrador_empresa: false,
  password: "",
};

const BITACORA_ACCIONES: Array<{ value: BitacoraAccion; label: string }> = [
  { value: "CREACION_USUARIO", label: "Creación de Usuario" },
  { value: "ACTUALIZACION_USUARIO", label: "Actualización de Usuario" },
  { value: "CAMBIO_ROL", label: "Cambio de Rol" },
  { value: "INACTIVACION_USUARIO", label: "Inactivación" },
  { value: "RESET_PASSWORD_FORZADO", label: "Reset Forzado" },
  { value: "APROBACION_USUARIO", label: "Aprobación" },
  { value: "RECHAZO_USUARIO", label: "Rechazo" },
  { value: "LOGIN_EXITOSO", label: "Login Exitoso" },
  { value: "LOGIN_FALLIDO", label: "Login Fallido" },
  { value: "LOGOUT", label: "Logout" },
];

const parseApiError = (error: unknown, fallback: string) => {
  if (!(error instanceof Error)) {
    return fallback;
  }

  const raw = error.message || fallback;
  const parts = raw.split(" - ");
  const payload = parts.length > 1 ? parts.slice(1).join(" - ") : raw;

  try {
    const parsed = JSON.parse(payload);
    if (typeof parsed === "string") {
      return parsed;
    }
    if (parsed?.detail) {
      return String(parsed.detail);
    }
    const firstKey = Object.keys(parsed || {})[0];
    if (firstKey) {
      const value = parsed[firstKey];
      if (Array.isArray(value)) {
        return `${firstKey}: ${value[0]}`;
      }
      return `${firstKey}: ${String(value)}`;
    }
  } catch {
    return raw;
  }

  return raw;
};

const estadoBadge = (isActive: boolean) => {
  if (isActive) {
    return <Badge className="bg-emerald-100 text-emerald-800 border-emerald-300">Activo</Badge>;
  }
  return <Badge className="bg-gray-200 text-gray-700 border-gray-300">Inactivo</Badge>;
};

const aprobacionBadge = (isApproved: boolean) => {
  if (isApproved) {
    return <Badge className="bg-green-100 text-green-800 border-green-300">Aprobado</Badge>;
  }
  return <Badge className="bg-amber-100 text-amber-800 border-amber-300">Pendiente</Badge>;
};

const accionBitacoraBadge = (accion: BitacoraEvento["accion"], label: string) => {
  const styleByAction: Record<BitacoraEvento["accion"], string> = {
    CREACION_USUARIO: "bg-cyan-100 text-cyan-800 border-cyan-300",
    ACTUALIZACION_USUARIO: "bg-slate-100 text-slate-800 border-slate-300",
    CAMBIO_ROL: "bg-indigo-100 text-indigo-800 border-indigo-300",
    INACTIVACION_USUARIO: "bg-red-100 text-red-800 border-red-300",
    RESET_PASSWORD_FORZADO: "bg-orange-100 text-orange-800 border-orange-300",
    APROBACION_USUARIO: "bg-emerald-100 text-emerald-800 border-emerald-300",
    RECHAZO_USUARIO: "bg-rose-100 text-rose-800 border-rose-300",
    LOGIN_EXITOSO: "bg-green-100 text-green-800 border-green-300",
    LOGIN_FALLIDO: "bg-amber-100 text-amber-800 border-amber-300",
    LOGOUT: "bg-blue-100 text-blue-800 border-blue-300",
  };

  return <Badge className={styleByAction[accion]}>{label}</Badge>;
};

const nombreUsuarioBitacora = (info: BitacoraEvento["actor_info"]) => {
  if (!info) {
    return "Sistema/Anónimo";
  }
  return info.full_name || info.username;
};

const resumenBitacora = (detalle: Record<string, unknown>) => {
  if (!detalle || Object.keys(detalle).length === 0) {
    return "Sin detalle técnico";
  }

  const mensaje = detalle.mensaje;
  if (typeof mensaje === "string" && mensaje.trim()) {
    return mensaje;
  }

  const usernameIntentado = detalle.username_intentado;
  if (typeof usernameIntentado === "string" && usernameIntentado.trim()) {
    return `Intento de autenticación para ${usernameIntentado}`;
  }

  const cambios = detalle.cambios;
  if (cambios && typeof cambios === "object" && !Array.isArray(cambios)) {
    const campos = Object.keys(cambios as Record<string, unknown>);
    if (campos.length > 0) {
      return `Campos modificados: ${campos.join(", ")}`;
    }
  }

  const preview = Object.entries(detalle)
    .slice(0, 2)
    .map(([key, value]) => {
      if (typeof value === "string" || typeof value === "number" || typeof value === "boolean") {
        return `${key}: ${value}`;
      }
      return `${key}: [obj]`;
    });

  return preview.join(" | ");
};

export function GestionUsuarios() {
  const usuarioActual = obtenerUsuario();
  const [searchParams] = useSearchParams();
  const panelQuery = searchParams.get("panel");
  const esSuperAdmin = esSuperusuario();
  const esAdminSistemaGlobal = esAdminSistema();
  const puedeGestionPremium = esSuperAdmin;
  const puedeForense = esSuperAdmin || esAdminSistemaGlobal;

  const [panelActivo, setPanelActivo] = useState<"usuarios" | "bitacora">(() => (
    esAdminSistemaGlobal || panelQuery === "bitacora" ? "bitacora" : "usuarios"
  ));

  const [stats, setStats] = useState<GlobalUsersStats | null>(null);
  const [usuarios, setUsuarios] = useState<GlobalUser[]>([]);
  const [empresas, setEmpresas] = useState<EmpresaOption[]>([]);
  const [eventosBitacora, setEventosBitacora] = useState<BitacoraEvento[]>([]);

  const [loadingStats, setLoadingStats] = useState(true);
  const [loadingTable, setLoadingTable] = useState(true);
  const [loadingEmpresas, setLoadingEmpresas] = useState(true);
  const [loadingBitacora, setLoadingBitacora] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const [searchInput, setSearchInput] = useState("");
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);
  const [totalCount, setTotalCount] = useState(0);

  const [bitacoraSearchInput, setBitacoraSearchInput] = useState("");
  const [bitacoraSearch, setBitacoraSearch] = useState("");
  const [bitacoraAccion, setBitacoraAccion] = useState<BitacoraAccion | "">("");
  const [bitacoraPage, setBitacoraPage] = useState(1);
  const [bitacoraPageSize, setBitacoraPageSize] = useState(20);
  const [bitacoraTotalCount, setBitacoraTotalCount] = useState(0);

  const [reloadKey, setReloadKey] = useState(0);

  const [openFormModal, setOpenFormModal] = useState(false);
  const [editandoUsuario, setEditandoUsuario] = useState<GlobalUser | null>(null);
  const [form, setForm] = useState<GlobalUserForm>(INITIAL_FORM);

  const [usuarioPendienteInactivar, setUsuarioPendienteInactivar] = useState<GlobalUser | null>(null);
  const [confirmarCambioRol, setConfirmarCambioRol] = useState<{
    user: GlobalUser;
    payload: GlobalUserPayload;
  } | null>(null);
  const [usuarioPendienteReset, setUsuarioPendienteReset] = useState<GlobalUser | null>(null);
  const [resultadoReset, setResultadoReset] = useState<{
    username: string;
    temporary_password: string;
    reset_link: string;
  } | null>(null);

  useEffect(() => {
    if (!puedeForense) {
      return;
    }

    if (esAdminSistemaGlobal || panelQuery === "bitacora") {
      setPanelActivo("bitacora");
    }
  }, [esAdminSistemaGlobal, panelQuery, puedeForense]);

  const totalPages = useMemo(() => Math.max(1, Math.ceil(totalCount / pageSize)), [totalCount, pageSize]);
  const pageStart = totalCount === 0 ? 0 : (page - 1) * pageSize + 1;
  const pageEnd = Math.min(page * pageSize, totalCount);

  const totalPagesBitacora = useMemo(
    () => Math.max(1, Math.ceil(bitacoraTotalCount / bitacoraPageSize)),
    [bitacoraTotalCount, bitacoraPageSize],
  );
  const bitacoraPageStart = bitacoraTotalCount === 0 ? 0 : (bitacoraPage - 1) * bitacoraPageSize + 1;
  const bitacoraPageEnd = Math.min(bitacoraPage * bitacoraPageSize, bitacoraTotalCount);

  useEffect(() => {
    const timeout = window.setTimeout(() => {
      setPage(1);
      setSearch(searchInput.trim());
    }, 350);

    return () => window.clearTimeout(timeout);
  }, [searchInput]);

  useEffect(() => {
    const timeout = window.setTimeout(() => {
      setBitacoraPage(1);
      setBitacoraSearch(bitacoraSearchInput.trim());
    }, 350);

    return () => window.clearTimeout(timeout);
  }, [bitacoraSearchInput]);

  useEffect(() => {
    if (!puedeGestionPremium) {
      setLoadingStats(false);
      return;
    }

    const loadStats = async () => {
      setLoadingStats(true);
      try {
        const data = await fetchGlobalUsersStats();
        setStats(data);
      } catch (error) {
        toast.error(parseApiError(error, "No se pudieron cargar las métricas globales."));
      } finally {
        setLoadingStats(false);
      }
    };

    loadStats();
  }, [puedeGestionPremium, reloadKey]);

  useEffect(() => {
    if (!puedeGestionPremium) {
      setLoadingTable(false);
      setUsuarios([]);
      setTotalCount(0);
      return;
    }

    const loadUsers = async () => {
      setLoadingTable(true);
      try {
        const response = await fetchGlobalUsers({
          page,
          pageSize,
          search,
        });

        setUsuarios(response.results);
        setTotalCount(response.count);

        const maxPages = Math.max(1, Math.ceil(response.count / pageSize));
        if (page > maxPages) {
          setPage(maxPages);
        }
      } catch (error) {
        toast.error(parseApiError(error, "No se pudo cargar la tabla de usuarios."));
      } finally {
        setLoadingTable(false);
      }
    };

    loadUsers();
  }, [page, pageSize, puedeGestionPremium, search, reloadKey]);

  useEffect(() => {
    if (!puedeGestionPremium) {
      setLoadingEmpresas(false);
      setEmpresas([]);
      return;
    }

    const loadEmpresas = async () => {
      setLoadingEmpresas(true);
      try {
        const data = await fetchEmpresasOptions();
        setEmpresas(data);
      } catch (error) {
        toast.error(parseApiError(error, "No fue posible cargar el catálogo de empresas."));
      } finally {
        setLoadingEmpresas(false);
      }
    };

    loadEmpresas();
  }, [puedeGestionPremium]);

  useEffect(() => {
    if (panelActivo !== "bitacora") {
      return;
    }

    const loadBitacora = async () => {
      setLoadingBitacora(true);
      try {
        const response = await fetchGlobalBitacora({
          page: bitacoraPage,
          pageSize: bitacoraPageSize,
          search: bitacoraSearch,
          accion: bitacoraAccion,
        });

        setEventosBitacora(response.results);
        setBitacoraTotalCount(response.count);

        const maxPages = Math.max(1, Math.ceil(response.count / bitacoraPageSize));
        if (bitacoraPage > maxPages) {
          setBitacoraPage(maxPages);
        }
      } catch (error) {
        toast.error(parseApiError(error, "No se pudo cargar la bitácora forense."));
      } finally {
        setLoadingBitacora(false);
      }
    };

    loadBitacora();
  }, [panelActivo, bitacoraPage, bitacoraPageSize, bitacoraSearch, bitacoraAccion, reloadKey]);

  const refreshData = () => {
    setReloadKey((current) => current + 1);
  };

  const abrirCrear = () => {
    setEditandoUsuario(null);
    setForm(INITIAL_FORM);
    setOpenFormModal(true);
  };

  const abrirEditar = (user: GlobalUser) => {
    setEditandoUsuario(user);
    setForm({
      username: user.username,
      email: user.email,
      first_name: user.first_name,
      last_name: user.last_name,
      rol: user.rol,
      empresa: user.empresa,
      is_active: user.is_active,
      is_approved: user.is_approved,
      es_administrador_empresa: user.rol === "LIDER_EQUIPO" || user.es_administrador_empresa,
      password: "",
    });
    setOpenFormModal(true);
  };

  const closeFormModal = () => {
    setOpenFormModal(false);
    setEditandoUsuario(null);
    setForm(INITIAL_FORM);
  };

  const buildPayloadFromForm = (): GlobalUserPayload => ({
    username: form.username.trim(),
    email: form.email.trim(),
    first_name: form.first_name.trim(),
    last_name: form.last_name.trim(),
    rol: form.rol,
    empresa: form.empresa,
    is_active: form.is_active,
    is_approved: form.is_approved,
    es_administrador_empresa: form.rol === "LIDER_EQUIPO",
    ...(form.password.trim() ? { password: form.password.trim() } : {}),
  });

  const executeUpdate = async (user: GlobalUser, payload: GlobalUserPayload) => {
    setIsSubmitting(true);
    try {
      await updateGlobalUser(user.id, payload);
      toast.success("Usuario actualizado correctamente.");
      closeFormModal();
      refreshData();
    } catch (error) {
      toast.error(parseApiError(error, "No se pudo actualizar el usuario."));
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleSubmitForm = async (event: React.FormEvent) => {
    event.preventDefault();

    const payload = buildPayloadFromForm();
    setIsSubmitting(true);

    if (editandoUsuario) {
      if (payload.rol !== editandoUsuario.rol) {
        setIsSubmitting(false);
        setConfirmarCambioRol({
          user: editandoUsuario,
          payload,
        });
        return;
      }

      await executeUpdate(editandoUsuario, payload);
      return;
    }

    try {
      const created = await createGlobalUser(payload);
      toast.success("Usuario creado exitosamente.");

      if (created.temporary_password) {
        setResultadoReset({
          username: created.username,
          temporary_password: created.temporary_password,
          reset_link: "Generado automáticamente para entrega segura.",
        });
      }

      closeFormModal();
      refreshData();
    } catch (error) {
      toast.error(parseApiError(error, "No fue posible crear el usuario."));
    } finally {
      setIsSubmitting(false);
    }
  };

  const confirmarInactivacion = async () => {
    if (!usuarioPendienteInactivar) {
      return;
    }

    try {
      await inactivateGlobalUser(usuarioPendienteInactivar.id);
      toast.success("Usuario inactivado. Registro preservado por trazabilidad.");
      setUsuarioPendienteInactivar(null);
      refreshData();
    } catch (error) {
      toast.error(parseApiError(error, "No se pudo inactivar el usuario."));
    }
  };

  const confirmarForzarReset = async () => {
    if (!usuarioPendienteReset) {
      return;
    }

    try {
      const data = await forceResetPassword(usuarioPendienteReset.id);
      toast.success("Reseteo forzado ejecutado correctamente.");
      setResultadoReset({
        username: usuarioPendienteReset.username,
        temporary_password: data.temporary_password,
        reset_link: data.reset_link,
      });
      setUsuarioPendienteReset(null);
    } catch (error) {
      toast.error(parseApiError(error, "No se pudo forzar el reseteo de contraseña."));
    }
  };

  if (!puedeForense) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-xl p-6">
        <h1 className="text-2xl font-bold text-red-900">Acceso Restringido</h1>
        <p className="text-red-700 mt-2">
          Este módulo requiere privilegios globales de administración/forense.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col xl:flex-row xl:items-center xl:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">
            {puedeGestionPremium ? "G.U ADMIN" : "Bitácora Forense Global"}
          </h1>
          <p className="text-gray-600 mt-1">
            {puedeGestionPremium
              ? "Administración global de identidades, estados y acceso multi-tenant."
              : "Consulta global de trazabilidad WORM para operaciones críticas de usuarios."}
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={refreshData}
            className="inline-flex items-center gap-2 px-4 py-2 border border-slate-300 rounded-lg bg-white text-slate-700 hover:bg-slate-100"
          >
            <Loader2 className="w-4 h-4" />
            Refrescar
          </button>
          {puedeGestionPremium && (
            <button
              onClick={abrirCrear}
              className="inline-flex items-center gap-2 bg-yellow-400 text-black font-semibold py-2.5 px-5 rounded-lg hover:bg-yellow-500 transition-colors shadow-md"
            >
              <Plus className="w-5 h-5" />
              Crear Usuario
            </button>
          )}
        </div>
      </div>

      {puedeGestionPremium && (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
          {loadingStats || !stats ? (
            Array.from({ length: 4 }).map((_, index) => (
              <div key={index} className="bg-white rounded-xl border border-gray-200 p-5">
                <Skeleton className="h-4 w-28" />
                <Skeleton className="h-8 w-16 mt-3" />
              </div>
            ))
          ) : (
            <>
              <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-sm">
                <p className="text-sm text-gray-600">Total de Usuarios</p>
                <p className="text-3xl font-bold text-gray-900 mt-2">{stats.total_users}</p>
                <div className="mt-3 inline-flex items-center gap-2 text-xs text-slate-500">
                  <Users className="w-4 h-4" />
                  Universo de identidades
                </div>
              </div>
              <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-sm">
                <p className="text-sm text-gray-600">Usuarios Activos</p>
                <p className="text-3xl font-bold text-emerald-700 mt-2">{stats.active_users}</p>
                <div className="mt-3 inline-flex items-center gap-2 text-xs text-emerald-700">
                  <CheckCircle2 className="w-4 h-4" />
                  Cuentas habilitadas
                </div>
              </div>
              <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-sm">
                <p className="text-sm text-gray-600">Administradores Globales</p>
                <p className="text-3xl font-bold text-purple-700 mt-2">{stats.global_admins}</p>
                <div className="mt-3 inline-flex items-center gap-2 text-xs text-purple-700">
                  <ShieldCheck className="w-4 h-4" />
                  Infraestructura
                </div>
              </div>
              <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-sm">
                <p className="text-sm text-gray-600">Empresas Registradas</p>
                <p className="text-3xl font-bold text-blue-700 mt-2">{stats.total_companies}</p>
                <div className="mt-3 inline-flex items-center gap-2 text-xs text-blue-700">
                  <Building2 className="w-4 h-4" />
                  Tenants activos
                </div>
              </div>
            </>
          )}
        </div>
      )}

      <div className="bg-white rounded-xl border border-gray-200 p-2 shadow-sm inline-flex items-center gap-2 w-fit">
        {puedeGestionPremium && (
          <button
            type="button"
            onClick={() => setPanelActivo("usuarios")}
            className={`inline-flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-semibold transition-colors ${
              panelActivo === "usuarios"
                ? "bg-slate-900 text-white"
                : "text-slate-700 hover:bg-slate-100"
            }`}
          >
            <Users className="w-4 h-4" />
            G.U ADMIN
          </button>
        )}
        <button
          type="button"
          onClick={() => setPanelActivo("bitacora")}
          className={`inline-flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-semibold transition-colors ${
            panelActivo === "bitacora"
              ? "bg-slate-900 text-white"
              : "text-slate-700 hover:bg-slate-100"
          }`}
        >
          <History className="w-4 h-4" />
          Bitácora Forense
        </button>
      </div>

      {panelActivo === "usuarios" ? (
        <>
          <div className="bg-white rounded-xl border border-gray-200 p-4 shadow-sm">
            <div className="flex flex-col lg:flex-row gap-3 lg:items-center lg:justify-between">
              <div className="relative flex-1 max-w-2xl">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                <input
                  value={searchInput}
                  onChange={(event) => setSearchInput(event.target.value)}
                  placeholder="Buscar por nombre, usuario, email o empresa..."
                  className="w-full pl-10 pr-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-yellow-400 focus:border-transparent outline-none"
                />
              </div>

              <div className="flex items-center gap-2 text-sm">
                <span className="text-gray-600">Filas por página:</span>
                <select
                  value={pageSize}
                  onChange={(event) => {
                    setPage(1);
                    setPageSize(Number(event.target.value));
                  }}
                  className="border border-gray-300 rounded-lg px-3 py-2 outline-none focus:ring-2 focus:ring-yellow-400"
                >
                  <option value={10}>10</option>
                  <option value={20}>20</option>
                  <option value={50}>50</option>
                </select>
              </div>
            </div>

            <div className="mt-3 text-sm text-gray-600">
              Mostrando <span className="font-semibold text-gray-900">{pageStart}</span> a <span className="font-semibold text-gray-900">{pageEnd}</span> de <span className="font-semibold text-gray-900">{totalCount}</span> usuarios.
            </div>
          </div>

          <div className="bg-white rounded-xl border border-gray-200 overflow-hidden shadow-sm">
            <div className="overflow-x-auto">
              <table className="w-full min-w-[980px]">
                <thead className="bg-slate-900 text-white">
                  <tr>
                    <th className="px-5 py-4 text-left text-xs font-semibold uppercase tracking-wider">Usuario</th>
                    <th className="px-5 py-4 text-left text-xs font-semibold uppercase tracking-wider">Empresa</th>
                    <th className="px-5 py-4 text-left text-xs font-semibold uppercase tracking-wider">Rol</th>
                    <th className="px-5 py-4 text-left text-xs font-semibold uppercase tracking-wider">Estado</th>
                    <th className="px-5 py-4 text-left text-xs font-semibold uppercase tracking-wider">Aprobación</th>
                    <th className="px-5 py-4 text-left text-xs font-semibold uppercase tracking-wider">Último acceso</th>
                    <th className="px-5 py-4 text-left text-xs font-semibold uppercase tracking-wider">Acciones</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                  {loadingTable ? (
                    Array.from({ length: 8 }).map((_, row) => (
                      <tr key={row}>
                        <td className="px-5 py-4"><Skeleton className="h-4 w-40" /></td>
                        <td className="px-5 py-4"><Skeleton className="h-4 w-32" /></td>
                        <td className="px-5 py-4"><Skeleton className="h-6 w-24" /></td>
                        <td className="px-5 py-4"><Skeleton className="h-6 w-20" /></td>
                        <td className="px-5 py-4"><Skeleton className="h-6 w-24" /></td>
                        <td className="px-5 py-4"><Skeleton className="h-4 w-28" /></td>
                        <td className="px-5 py-4"><Skeleton className="h-8 w-28" /></td>
                      </tr>
                    ))
                  ) : usuarios.length === 0 ? (
                    <tr>
                      <td colSpan={7} className="px-5 py-12 text-center text-gray-500">
                        No se encontraron usuarios para los filtros actuales.
                      </td>
                    </tr>
                  ) : (
                    usuarios.map((user) => (
                      <tr key={user.id} className="hover:bg-slate-50">
                        <td className="px-5 py-4">
                          <div className="flex items-center gap-3">
                            <div className="w-10 h-10 rounded-full bg-slate-100 text-slate-700 flex items-center justify-center">
                              <UserRound className="w-5 h-5" />
                            </div>
                            <div>
                              <p className="font-semibold text-gray-900">{user.full_name}</p>
                              <p className="text-xs text-gray-500">@{user.username} • {user.email}</p>
                            </div>
                          </div>
                        </td>
                        <td className="px-5 py-4 text-sm text-gray-700">
                          {user.empresa_info?.nombre || "Sin empresa"}
                        </td>
                        <td className="px-5 py-4">
                          <RoleBadge
                            rol={user.rol}
                            isSuperuser={user.is_superuser}
                            isLeader={user.rol === "LIDER_EQUIPO" || user.es_administrador_empresa}
                          />
                        </td>
                        <td className="px-5 py-4">{estadoBadge(user.is_active)}</td>
                        <td className="px-5 py-4">{aprobacionBadge(user.is_approved)}</td>
                        <td className="px-5 py-4 text-sm text-gray-600">
                          {user.last_login ? new Date(user.last_login).toLocaleString() : "Sin registro"}
                        </td>
                        <td className="px-5 py-4">
                          <div className="flex items-center gap-2">
                            <button
                              onClick={() => abrirEditar(user)}
                              className="inline-flex items-center justify-center w-8 h-8 rounded-md bg-slate-100 text-slate-700 hover:bg-slate-200 border border-slate-300"
                              title="Editar"
                            >
                              <Pencil className="w-4 h-4" />
                            </button>

                            <button
                              onClick={() => setUsuarioPendienteReset(user)}
                              disabled={user.id === usuarioActual?.id}
                              className="inline-flex items-center justify-center w-8 h-8 rounded-md bg-blue-50 text-blue-700 hover:bg-blue-100 border border-blue-200 disabled:opacity-40"
                              title="Forzar reseteo de contraseña"
                            >
                              <KeyRound className="w-4 h-4" />
                            </button>

                            <Tooltip>
                              <TooltipTrigger asChild>
                                <button
                                  onClick={() => setUsuarioPendienteInactivar(user)}
                                  disabled={!user.is_active || user.id === usuarioActual?.id}
                                  className="inline-flex items-center justify-center w-8 h-8 rounded-md bg-red-50 text-red-700 hover:bg-red-100 border border-red-200 disabled:opacity-40"
                                  title="Inactivar usuario"
                                >
                                  <Power className="w-4 h-4" />
                                </button>
                              </TooltipTrigger>
                              <TooltipContent sideOffset={8}>
                                Soft Delete ISO 27001: inactiva cuenta (is_active=false) sin borrar trazabilidad histórica.
                              </TooltipContent>
                            </Tooltip>
                          </div>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>

          <div className="flex flex-col sm:flex-row items-center justify-between gap-3">
            <div className="text-sm text-gray-600">
              Página <span className="font-semibold text-gray-900">{page}</span> de <span className="font-semibold text-gray-900">{totalPages}</span>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={() => setPage((current) => Math.max(1, current - 1))}
                disabled={page <= 1}
                className="px-3 py-2 text-sm rounded-lg border border-gray-300 bg-white hover:bg-gray-50 disabled:opacity-40"
              >
                Anterior
              </button>
              <button
                onClick={() => setPage((current) => Math.min(totalPages, current + 1))}
                disabled={page >= totalPages}
                className="px-3 py-2 text-sm rounded-lg border border-gray-300 bg-white hover:bg-gray-50 disabled:opacity-40"
              >
                Siguiente
              </button>
            </div>
          </div>
        </>
      ) : (
        <>
          <div className="bg-white rounded-xl border border-gray-200 p-4 shadow-sm">
            <div className="flex flex-col xl:flex-row gap-3 xl:items-center xl:justify-between">
              <div className="relative flex-1 max-w-2xl">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                <input
                  value={bitacoraSearchInput}
                  onChange={(event) => setBitacoraSearchInput(event.target.value)}
                  placeholder="Buscar por actor, usuario objetivo, empresa o IP..."
                  className="w-full pl-10 pr-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-yellow-400 focus:border-transparent outline-none"
                />
              </div>

              <div className="flex flex-wrap items-center gap-2 text-sm">
                <select
                  value={bitacoraAccion}
                  onChange={(event) => {
                    setBitacoraPage(1);
                    setBitacoraAccion(event.target.value as BitacoraAccion | "");
                  }}
                  className="border border-gray-300 rounded-lg px-3 py-2 outline-none focus:ring-2 focus:ring-yellow-400"
                >
                  <option value="">Todas las acciones</option>
                  {BITACORA_ACCIONES.map((accion) => (
                    <option key={accion.value} value={accion.value}>
                      {accion.label}
                    </option>
                  ))}
                </select>

                <div className="flex items-center gap-2">
                  <span className="text-gray-600">Filas:</span>
                  <select
                    value={bitacoraPageSize}
                    onChange={(event) => {
                      setBitacoraPage(1);
                      setBitacoraPageSize(Number(event.target.value));
                    }}
                    className="border border-gray-300 rounded-lg px-3 py-2 outline-none focus:ring-2 focus:ring-yellow-400"
                  >
                    <option value={10}>10</option>
                    <option value={20}>20</option>
                    <option value={50}>50</option>
                  </select>
                </div>
              </div>
            </div>

            <div className="mt-3 text-sm text-gray-600">
              Mostrando <span className="font-semibold text-gray-900">{bitacoraPageStart}</span> a <span className="font-semibold text-gray-900">{bitacoraPageEnd}</span> de <span className="font-semibold text-gray-900">{bitacoraTotalCount}</span> eventos forenses.
            </div>
          </div>

          <div className="bg-white rounded-xl border border-gray-200 overflow-hidden shadow-sm">
            <div className="overflow-x-auto">
              <table className="w-full min-w-[1260px]">
                <thead className="bg-slate-900 text-white">
                  <tr>
                    <th className="px-5 py-4 text-left text-xs font-semibold uppercase tracking-wider">Fecha</th>
                    <th className="px-5 py-4 text-left text-xs font-semibold uppercase tracking-wider">Acción</th>
                    <th className="px-5 py-4 text-left text-xs font-semibold uppercase tracking-wider">Actor</th>
                    <th className="px-5 py-4 text-left text-xs font-semibold uppercase tracking-wider">Objetivo</th>
                    <th className="px-5 py-4 text-left text-xs font-semibold uppercase tracking-wider">Empresa</th>
                    <th className="px-5 py-4 text-left text-xs font-semibold uppercase tracking-wider">Origen</th>
                    <th className="px-5 py-4 text-left text-xs font-semibold uppercase tracking-wider">Detalle</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                  {loadingBitacora ? (
                    Array.from({ length: 8 }).map((_, row) => (
                      <tr key={row}>
                        <td className="px-5 py-4"><Skeleton className="h-4 w-36" /></td>
                        <td className="px-5 py-4"><Skeleton className="h-6 w-36" /></td>
                        <td className="px-5 py-4"><Skeleton className="h-4 w-40" /></td>
                        <td className="px-5 py-4"><Skeleton className="h-4 w-40" /></td>
                        <td className="px-5 py-4"><Skeleton className="h-4 w-32" /></td>
                        <td className="px-5 py-4"><Skeleton className="h-4 w-40" /></td>
                        <td className="px-5 py-4"><Skeleton className="h-4 w-56" /></td>
                      </tr>
                    ))
                  ) : eventosBitacora.length === 0 ? (
                    <tr>
                      <td colSpan={7} className="px-5 py-12 text-center text-gray-500">
                        No hay eventos para los filtros de bitácora seleccionados.
                      </td>
                    </tr>
                  ) : (
                    eventosBitacora.map((evento) => (
                      <tr key={evento.id} className="hover:bg-slate-50">
                        <td className="px-5 py-4 text-sm text-gray-700">
                          {new Date(evento.fecha_evento).toLocaleString()}
                        </td>
                        <td className="px-5 py-4">
                          {accionBitacoraBadge(evento.accion, evento.accion_display)}
                        </td>
                        <td className="px-5 py-4 text-sm text-gray-700">
                          <p className="font-semibold text-gray-900">{nombreUsuarioBitacora(evento.actor_info)}</p>
                          <p className="text-xs text-gray-500">
                            {evento.actor_info ? `@${evento.actor_info.username}` : "Evento de sistema"}
                          </p>
                        </td>
                        <td className="px-5 py-4 text-sm text-gray-700">
                          {evento.usuario_objetivo_info ? (
                            <>
                              <p className="font-semibold text-gray-900">{nombreUsuarioBitacora(evento.usuario_objetivo_info)}</p>
                              <p className="text-xs text-gray-500">@{evento.usuario_objetivo_info.username}</p>
                            </>
                          ) : (
                            <span className="text-gray-500">No identificado</span>
                          )}
                        </td>
                        <td className="px-5 py-4 text-sm text-gray-700">
                          {evento.empresa_info?.nombre || "Sin empresa"}
                        </td>
                        <td className="px-5 py-4 text-sm text-gray-700 max-w-[220px]">
                          <p className="font-semibold text-gray-900">{evento.ip_origen || "IP no informada"}</p>
                          <p className="text-xs text-gray-500 break-all">
                            {evento.user_agent || "User-Agent no informado"}
                          </p>
                        </td>
                        <td className="px-5 py-4 text-sm text-gray-700 max-w-[320px] break-words">
                          {resumenBitacora(evento.detalle)}
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>

          <div className="flex flex-col sm:flex-row items-center justify-between gap-3">
            <div className="text-sm text-gray-600">
              Página <span className="font-semibold text-gray-900">{bitacoraPage}</span> de <span className="font-semibold text-gray-900">{totalPagesBitacora}</span>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={() => setBitacoraPage((current) => Math.max(1, current - 1))}
                disabled={bitacoraPage <= 1}
                className="px-3 py-2 text-sm rounded-lg border border-gray-300 bg-white hover:bg-gray-50 disabled:opacity-40"
              >
                Anterior
              </button>
              <button
                onClick={() => setBitacoraPage((current) => Math.min(totalPagesBitacora, current + 1))}
                disabled={bitacoraPage >= totalPagesBitacora}
                className="px-3 py-2 text-sm rounded-lg border border-gray-300 bg-white hover:bg-gray-50 disabled:opacity-40"
              >
                Siguiente
              </button>
            </div>
          </div>
        </>
      )}

      <Dialog open={openFormModal} onOpenChange={(open) => (!open ? closeFormModal() : setOpenFormModal(true))}>
        <DialogContent className="sm:max-w-3xl">
          <DialogHeader>
            <DialogTitle>{editandoUsuario ? "Editar Usuario Global" : "Crear Usuario Global"}</DialogTitle>
            <DialogDescription>
              Operación exclusiva de infraestructura. Todos los cambios quedan trazados para auditoría.
            </DialogDescription>
          </DialogHeader>

          <form onSubmit={handleSubmitForm} className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-1">Username</label>
              <input
                value={form.username}
                onChange={(event) => setForm({ ...form, username: event.target.value })}
                required
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-yellow-400 outline-none"
              />
            </div>
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-1">Correo</label>
              <input
                type="email"
                value={form.email}
                onChange={(event) => setForm({ ...form, email: event.target.value })}
                required
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-yellow-400 outline-none"
              />
            </div>
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-1">Nombre</label>
              <input
                value={form.first_name}
                onChange={(event) => setForm({ ...form, first_name: event.target.value })}
                required
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-yellow-400 outline-none"
              />
            </div>
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-1">Apellido</label>
              <input
                value={form.last_name}
                onChange={(event) => setForm({ ...form, last_name: event.target.value })}
                required
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-yellow-400 outline-none"
              />
            </div>
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-1">Rol de Negocio</label>
              <select
                value={form.rol}
                onChange={(event) => {
                  const rolSeleccionado = event.target.value as "EMPLEADO" | "IMPLEMENTADOR" | "AUDITOR" | "LIDER_EQUIPO" | "CAPACITADOR";
                  setForm({
                    ...form,
                    rol: rolSeleccionado,
                    es_administrador_empresa: rolSeleccionado === "LIDER_EQUIPO",
                  });
                }}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-yellow-400 outline-none"
              >
                <option value="EMPLEADO">Empleado</option>
                <option value="IMPLEMENTADOR">Implementador</option>
                <option value="AUDITOR">Auditor</option>
                <option value="LIDER_EQUIPO">Líder de Equipo</option>
                <option value="CAPACITADOR">Capacitador</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-1">Empresa</label>
              <select
                value={form.empresa ?? ""}
                onChange={(event) => {
                  const value = event.target.value;
                  setForm({ ...form, empresa: value ? Number(value) : null });
                }}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-yellow-400 outline-none"
                disabled={loadingEmpresas}
              >
                <option value="">Sin empresa</option>
                {empresas.map((empresa) => (
                  <option key={empresa.id} value={empresa.id}>
                    {empresa.nombre}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-1">
                {editandoUsuario ? "Nueva contraseña (opcional)" : "Contraseña (opcional)"}
              </label>
              <input
                type="password"
                value={form.password}
                onChange={(event) => setForm({ ...form, password: event.target.value })}
                minLength={8}
                placeholder="Si lo dejas vacío, el sistema genera temporal"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-yellow-400 outline-none"
              />
            </div>

            <div className="md:col-span-2 grid grid-cols-1 md:grid-cols-2 gap-2 mt-1">
              <label className="flex items-center gap-2 text-sm text-gray-700">
                <input
                  type="checkbox"
                  checked={form.is_active}
                  onChange={(event) => setForm({ ...form, is_active: event.target.checked })}
                  className="rounded"
                />
                Usuario activo
              </label>

              <label className="flex items-center gap-2 text-sm text-gray-700">
                <input
                  type="checkbox"
                  checked={form.is_approved}
                  onChange={(event) => setForm({ ...form, is_approved: event.target.checked })}
                  className="rounded"
                />
                Usuario aprobado
              </label>
            </div>

            <div className="md:col-span-2 text-xs text-slate-600 bg-slate-50 border border-slate-200 rounded-lg px-3 py-2">
              El rol <span className="font-semibold">Líder de Equipo</span> activa automáticamente permisos de gestión de equipo local.
            </div>

            <DialogFooter className="md:col-span-2 mt-3">
              <button
                type="button"
                onClick={closeFormModal}
                className="px-4 py-2 rounded-lg border border-gray-300 text-gray-700 hover:bg-gray-100"
              >
                Cancelar
              </button>
              <button
                type="submit"
                disabled={isSubmitting}
                className="inline-flex items-center justify-center gap-2 bg-yellow-400 text-black font-semibold px-5 py-2 rounded-lg hover:bg-yellow-500 disabled:opacity-60"
              >
                {isSubmitting ? <Loader2 className="w-4 h-4 animate-spin" /> : <Shield className="w-4 h-4" />}
                {editandoUsuario ? "Guardar cambios" : "Crear usuario"}
              </button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      <Dialog open={Boolean(confirmarCambioRol)} onOpenChange={() => setConfirmarCambioRol(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Confirmar cambio de rol</DialogTitle>
            <DialogDescription>
              Estás por modificar el rol de negocio de este usuario. Esta operación impacta permisos operativos.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <button
              type="button"
              onClick={() => setConfirmarCambioRol(null)}
              className="px-4 py-2 rounded-lg border border-gray-300 text-gray-700 hover:bg-gray-100"
            >
              Cancelar
            </button>
            <button
              type="button"
              onClick={async () => {
                if (!confirmarCambioRol) {
                  return;
                }
                setConfirmarCambioRol(null);
                await executeUpdate(confirmarCambioRol.user, confirmarCambioRol.payload);
              }}
              className="px-4 py-2 rounded-lg bg-blue-600 text-white font-semibold hover:bg-blue-700"
            >
              Confirmar cambio
            </button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog open={Boolean(usuarioPendienteInactivar)} onOpenChange={() => setUsuarioPendienteInactivar(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Inactivar usuario</DialogTitle>
            <DialogDescription>
              Esta acción aplica Soft Delete: la cuenta se inactiva (is_active=false) sin eliminar evidencia histórica en base de datos.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <button
              type="button"
              onClick={() => setUsuarioPendienteInactivar(null)}
              className="px-4 py-2 rounded-lg border border-gray-300 text-gray-700 hover:bg-gray-100"
            >
              Cancelar
            </button>
            <button
              type="button"
              onClick={confirmarInactivacion}
              className="px-4 py-2 rounded-lg bg-red-600 text-white font-semibold hover:bg-red-700"
            >
              Inactivar
            </button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog open={Boolean(usuarioPendienteReset)} onOpenChange={() => setUsuarioPendienteReset(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Forzar reseteo de contraseña</DialogTitle>
            <DialogDescription>
              Se generará una clave temporal y un enlace de recuperación simulado para contingencia.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <button
              type="button"
              onClick={() => setUsuarioPendienteReset(null)}
              className="px-4 py-2 rounded-lg border border-gray-300 text-gray-700 hover:bg-gray-100"
            >
              Cancelar
            </button>
            <button
              type="button"
              onClick={confirmarForzarReset}
              className="px-4 py-2 rounded-lg bg-blue-600 text-white font-semibold hover:bg-blue-700"
            >
              Generar credencial temporal
            </button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog open={Boolean(resultadoReset)} onOpenChange={() => setResultadoReset(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Resultado del Reseteo</DialogTitle>
            <DialogDescription>
              Entrega esta información por canal seguro al usuario objetivo.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-3 text-sm">
            <div className="bg-slate-50 border border-slate-200 rounded-lg p-3">
              <p className="text-slate-600">Usuario</p>
              <p className="font-semibold text-slate-900">{resultadoReset?.username}</p>
            </div>
            <div className="bg-slate-50 border border-slate-200 rounded-lg p-3">
              <p className="text-slate-600">Contraseña temporal</p>
              <p className="font-mono font-semibold text-slate-900">{resultadoReset?.temporary_password}</p>
            </div>
            <div className="bg-slate-50 border border-slate-200 rounded-lg p-3 break-all">
              <p className="text-slate-600">Enlace simulado de reseteo</p>
              <p className="font-semibold text-slate-900">{resultadoReset?.reset_link}</p>
            </div>
          </div>

          <DialogFooter>
            <button
              type="button"
              onClick={() => setResultadoReset(null)}
              className="px-4 py-2 rounded-lg bg-slate-900 text-white font-semibold hover:bg-black"
            >
              Cerrar
            </button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
