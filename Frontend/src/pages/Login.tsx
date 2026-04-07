import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { Lock, User, Shield, AlertCircle, Info, Loader2 } from "lucide-react";
import { iniciarSesion } from "../utils/auth";

export function Login() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [mensaje, setMensaje] = useState<{ tipo: "error" | "info"; texto: string } | null>(null);
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setMensaje(null);
    setIsLoading(true);
    
    try {
      const perfil = await iniciarSesion(email, password);
      const isApproved = Boolean(perfil?.is_superuser || perfil?.is_approved);

      if (isApproved) {
        navigate("/dashboard");
        return;
      }

      setMensaje({
        tipo: "info",
        texto: "Tu cuenta está pendiente de aprobación por el administrador de tu empresa. Te redirigiremos a la pantalla de espera.",
      });
      window.setTimeout(() => {
        navigate("/espera", { replace: true });
      }, 900);
    } catch (error: any) {
      setMensaje({
        tipo: "error",
        texto: error.message || "Error al iniciar sesión. Verifica tus credenciales.",
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-black to-gray-900 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        {/* Logo y título */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-20 h-20 bg-yellow-400 rounded-2xl mb-4 shadow-lg shadow-yellow-400/50">
            <Shield className="w-12 h-12 text-black" />
          </div>
          <h1 className="text-4xl font-bold text-white mb-2">A.E.G.I.S</h1>
          <p className="text-gray-400">Sistema de Gestión de Auditorías ISO 27001</p>
        </div>

        {/* Formulario */}
        <div className="bg-white rounded-2xl shadow-2xl p-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-6">Iniciar sesión</h2>

          {mensaje && (
            <div
              className={`mb-5 rounded-lg border px-4 py-3 text-sm flex items-start gap-2 ${
                mensaje.tipo === "error"
                  ? "bg-red-50 border-red-200 text-red-700"
                  : "bg-blue-50 border-blue-200 text-blue-700"
              }`}
            >
              {mensaje.tipo === "error" ? (
                <AlertCircle className="w-4 h-4 mt-0.5 flex-shrink-0" />
              ) : (
                <Info className="w-4 h-4 mt-0.5 flex-shrink-0" />
              )}
              <span>{mensaje.texto}</span>
            </div>
          )}
          
          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-2">
                Usuario
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <User className="h-5 w-5 text-gray-400" />
                </div>
                <input
                  id="email"
                  type="text"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  autoComplete="username"
                  className="block w-full pl-10 pr-3 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-yellow-400 focus:border-transparent outline-none transition"
                  placeholder="Ingrese su usuario"
                  required
                />
              </div>
            </div>

            <div>
              <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-2">
                Contraseña
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <Lock className="h-5 w-5 text-gray-400" />
                </div>
                <input
                  id="password"
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  autoComplete="new-password"
                  className="block w-full pl-10 pr-3 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-yellow-400 focus:border-transparent outline-none transition"
                  placeholder="Ingrese su contraseña"
                  required
                />
              </div>
            </div>

            <div className="flex items-center justify-end">
              <a href="#" className="text-sm text-yellow-600 hover:text-yellow-700 font-medium">
                ¿Olvidó su contraseña?
              </a>
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="w-full bg-yellow-400 text-black font-semibold py-3 px-4 rounded-lg hover:bg-yellow-500 transition-colors shadow-lg shadow-yellow-400/30 disabled:opacity-70 disabled:cursor-not-allowed inline-flex items-center justify-center gap-2"
            >
              {isLoading ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin" />
                  Ingresando...
                </>
              ) : (
                "Iniciar sesión"
              )}
            </button>
          </form>

          <div className="mt-6 text-center">
            <p className="text-gray-600">
              ¿No tienes cuenta?{' '}
              <Link to="/registro" className="text-yellow-600 hover:text-yellow-700 font-semibold">
                Crear cuenta
              </Link>
            </p>
          </div>

          <div className="mt-4 text-center">
            <Link to="/" className="text-sm text-gray-500 hover:text-gray-700">
              ← Volver al inicio
            </Link>
          </div>
        </div>

        <div className="text-center mt-6">
          <p className="text-gray-500 text-sm">
            © 2026 AEGIS. Todos los derechos reservados.
          </p>
        </div>
      </div>
    </div>
  );
}
