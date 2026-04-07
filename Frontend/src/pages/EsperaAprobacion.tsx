import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Clock3, RefreshCw, ShieldAlert, LogOut, CheckCircle2 } from "lucide-react";
import { apiFetch } from "../utils/api";
import { cerrarSesionRemota, guardarUsuario, obtenerUsuario } from "../utils/auth";

interface PerfilUsuario {
  id: number;
  is_superuser: boolean;
  is_approved: boolean;
  empresa_info?: {
    nombre?: string;
  } | null;
}

export function EsperaAprobacion() {
  const navigate = useNavigate();
  const [verificando, setVerificando] = useState(false);

  const usuario = obtenerUsuario();
  const nombreEmpresa = usuario?.empresa_info?.nombre || "tu empresa";

  const handleVerificarEstado = async () => {
    setVerificando(true);
    try {
      const perfil = await apiFetch<PerfilUsuario>("/usuarios/perfil/");
      guardarUsuario(perfil);

      if (perfil.is_superuser || perfil.is_approved) {
        alert("Tu cuenta ya fue aprobada. Bienvenido a AEGIS.");
        navigate("/dashboard", { replace: true });
        return;
      }

      alert("Tu solicitud sigue en revisión. Te avisaremos cuando seas aprobado.");
    } catch (error: any) {
      alert(error?.message || "No fue posible verificar el estado de tu cuenta.");
    } finally {
      setVerificando(false);
    }
  };

  const handleCerrarSesion = async () => {
    await cerrarSesionRemota();
    navigate("/login", { replace: true });
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-black to-gray-900 flex items-center justify-center p-4">
      <div className="w-full max-w-2xl bg-white rounded-2xl shadow-2xl border border-gray-200 p-8">
        <div className="flex items-start gap-4">
          <div className="w-14 h-14 rounded-xl bg-yellow-100 text-yellow-700 flex items-center justify-center flex-shrink-0">
            <Clock3 className="w-8 h-8" />
          </div>
          <div className="flex-1">
            <h1 className="text-3xl font-bold text-gray-900">Solicitud en Espera</h1>
            <p className="text-gray-600 mt-2 leading-relaxed">
              Tu usuario fue registrado correctamente para la empresa <span className="font-semibold text-gray-800">{nombreEmpresa}</span>,
              pero aún necesitas la aprobación del administrador de equipo para acceder al dashboard y a los módulos internos.
            </p>
          </div>
        </div>

        <div className="mt-6 space-y-3">
          <div className="flex items-center gap-2 text-sm text-gray-700 bg-gray-50 border border-gray-200 rounded-lg px-4 py-3">
            <ShieldAlert className="w-4 h-4 text-gray-600" />
            Estado actual: pendiente de aprobación.
          </div>
          <div className="flex items-center gap-2 text-sm text-green-700 bg-green-50 border border-green-200 rounded-lg px-4 py-3">
            <CheckCircle2 className="w-4 h-4" />
            Seguridad activa: sin aprobación no se habilita acceso a datos de la empresa.
          </div>
        </div>

        <div className="mt-8 flex flex-col sm:flex-row gap-3">
          <button
            onClick={handleVerificarEstado}
            disabled={verificando}
            className="flex-1 inline-flex items-center justify-center gap-2 bg-yellow-400 text-black font-semibold py-3 px-6 rounded-lg hover:bg-yellow-500 transition-colors disabled:opacity-60"
          >
            <RefreshCw className={`w-5 h-5 ${verificando ? "animate-spin" : ""}`} />
            {verificando ? "Verificando..." : "Verificar Estado"}
          </button>
          <button
            onClick={() => {
              void handleCerrarSesion();
            }}
            className="inline-flex items-center justify-center gap-2 bg-gray-200 text-gray-800 font-semibold py-3 px-6 rounded-lg hover:bg-gray-300 transition-colors"
          >
            <LogOut className="w-5 h-5" />
            Cerrar sesión
          </button>
        </div>
      </div>
    </div>
  );
}
