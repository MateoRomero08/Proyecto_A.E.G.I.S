import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Shield, Mail, Lock, User, CheckCircle2, Building2, AlertCircle, Info, Loader2 } from 'lucide-react';
import { guardarToken, guardarUsuario } from '../utils/auth';
import { API_URL } from '../utils/api';

const REGISTRO_API_URL = `${API_URL.replace(/\/$/, '')}/api/usuarios/registro/`;

type MensajeRegistro = {
  tipo: 'error' | 'success' | 'info';
  texto: string;
};

export function Registro() {
  const navigate = useNavigate();
  
  // Estados individuales para cada campo
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [password, setPassword] = useState('');
  const [passwordConfirm, setPasswordConfirm] = useState('');
  const [nombreEmpresa, setNombreEmpresa] = useState('');
  const [passwordStrength, setPasswordStrength] = useState(0);
  const [isLoading, setIsLoading] = useState(false);
  const [mensaje, setMensaje] = useState<MensajeRegistro | null>(null);

  const calculatePasswordStrength = (password: string) => {
    let strength = 0;
    if (password.length >= 8) strength++;
    if (/[a-z]/.test(password) && /[A-Z]/.test(password)) strength++;
    if (/\d/.test(password)) strength++;
    if (/[^a-zA-Z\d]/.test(password)) strength++;
    return strength;
  };

  const handlePasswordChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newPassword = e.target.value;
    setPassword(newPassword);
    setPasswordStrength(calculatePasswordStrength(newPassword));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setMensaje(null);
    
    // Validaciones
    if (password !== passwordConfirm) {
      setMensaje({
        tipo: 'error',
        texto: 'Las contraseñas no coinciden.'
      });
      return;
    }

    if (passwordStrength < 2) {
      setMensaje({
        tipo: 'error',
        texto: 'Por favor, usa una contraseña más segura.'
      });
      return;
    }

    setIsLoading(true);

    try {
      // Crear objeto con datos del registro
      const registroData = {
        username,
        email,
        first_name: firstName,
        last_name: lastName,
        password,
        password_confirm: passwordConfirm,
        nombre_empresa: nombreEmpresa,
        rol: 'EMPLEADO'
      };

      // Hacer POST al endpoint de registro
      const response = await fetch(REGISTRO_API_URL, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
          // NO enviar Authorization porque es un registro público
        },
        body: JSON.stringify(registroData)
      });

      if (!response.ok) {
        const errorData = await response.json();
        
        // Manejar errores específicos del backend
        if (errorData.username) {
          throw new Error(`Usuario: ${errorData.username[0]}`);
        }
        if (errorData.email) {
          throw new Error(`Email: ${errorData.email[0]}`);
        }
        if (errorData.password) {
          throw new Error(`Contraseña: ${errorData.password[0]}`);
        }
        if (errorData.detail) {
          throw new Error(errorData.detail);
        }
        
        throw new Error('Error al registrar usuario. Por favor, verifica los datos.');
      }

      const data = await response.json();

      // Guardar token y usuario en localStorage
      if (data.access) {
        guardarToken(data.access);
      }
      if (data.usuario) {
        guardarUsuario(data.usuario);
      }

      const isApproved = Boolean(data?.usuario?.is_superuser || data?.usuario?.is_approved);

      if (isApproved) {
        setMensaje({
          tipo: 'success',
          texto: 'Registro exitoso. Tu empresa fue creada y ahora eres el administrador del equipo.'
        });
        window.setTimeout(() => {
          navigate('/dashboard', { replace: true });
        }, 900);
      } else {
        setMensaje({
          tipo: 'info',
          texto: 'Registro exitoso. Tu cuenta quedó pendiente de aprobación por el administrador de tu empresa. Te redirigiremos a la pantalla de espera.'
        });
        window.setTimeout(() => {
          navigate('/espera', { replace: true });
        }, 1000);
      }

    } catch (error: any) {
      console.error('Error en el registro:', error);
      setMensaje({
        tipo: 'error',
        texto: error.message || 'Error al crear la cuenta. Por favor, intenta nuevamente.'
      });
    } finally {
      setIsLoading(false);
    }
  };

  const getStrengthColor = () => {
    if (passwordStrength === 0) return 'bg-gray-200';
    if (passwordStrength === 1) return 'bg-red-500';
    if (passwordStrength === 2) return 'bg-yellow-500';
    if (passwordStrength === 3) return 'bg-yellow-400';
    return 'bg-green-500';
  };

  const getStrengthText = () => {
    if (passwordStrength === 0) return '';
    if (passwordStrength === 1) return 'Débil';
    if (passwordStrength === 2) return 'Media';
    if (passwordStrength === 3) return 'Buena';
    return 'Excelente';
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-black to-gray-900 flex items-center justify-center p-4">
      <div className="w-full max-w-2xl">
        {/* Logo y título */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-20 h-20 bg-yellow-400 rounded-2xl mb-4 shadow-lg shadow-yellow-400/50">
            <Shield className="w-12 h-12 text-black" />
          </div>
          <h1 className="text-4xl font-bold text-white mb-2">A.E.G.I.S</h1>
          <p className="text-gray-400">Únete a la plataforma innovadora para el cumplimiento ISO 27001</p>
        </div>

        {/* Formulario */}
        <div className="bg-white rounded-2xl shadow-2xl p-8 lg:p-10">
          <div className="mb-8">
            <h2 className="text-3xl font-bold text-gray-900 mb-2">Crear cuenta</h2>
            <p className="text-gray-600">Completa los datos para comenzar</p>
          </div>

          {mensaje && (
            <div
              className={`mb-6 rounded-lg border px-4 py-3 text-sm flex items-start gap-2 ${
                mensaje.tipo === 'error'
                  ? 'bg-red-50 border-red-200 text-red-700'
                  : mensaje.tipo === 'success'
                    ? 'bg-green-50 border-green-200 text-green-700'
                    : 'bg-blue-50 border-blue-200 text-blue-700'
              }`}
            >
              {mensaje.tipo === 'error' ? (
                <AlertCircle className="w-4 h-4 mt-0.5 flex-shrink-0" />
              ) : mensaje.tipo === 'success' ? (
                <CheckCircle2 className="w-4 h-4 mt-0.5 flex-shrink-0" />
              ) : (
                <Info className="w-4 h-4 mt-0.5 flex-shrink-0" />
              )}
              <span>{mensaje.texto}</span>
            </div>
          )}
          
          <form onSubmit={handleSubmit} className="space-y-5">
            {/* Grid de 2 columnas en pantallas grandes */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
              {/* Nombre */}
              <div>
                <label htmlFor="firstName" className="block text-sm font-medium text-gray-700 mb-2">
                  Nombre
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                    <User className="h-5 w-5 text-gray-400" />
                  </div>
                  <input
                    type="text"
                    id="firstName"
                    name="firstName"
                    value={firstName}
                    onChange={(e) => setFirstName(e.target.value)}
                    required
                    className="block w-full pl-10 pr-3 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-yellow-400 focus:border-transparent outline-none transition"
                    placeholder="Juan"
                  />
                </div>
              </div>

              {/* Apellido */}
              <div>
                <label htmlFor="lastName" className="block text-sm font-medium text-gray-700 mb-2">
                  Apellido
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                    <User className="h-5 w-5 text-gray-400" />
                  </div>
                  <input
                    type="text"
                    id="lastName"
                    name="lastName"
                    value={lastName}
                    onChange={(e) => setLastName(e.target.value)}
                    required
                    className="block w-full pl-10 pr-3 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-yellow-400 focus:border-transparent outline-none transition"
                    placeholder="Pérez"
                  />
                </div>
              </div>
            </div>

            {/* Username */}
            <div>
              <label htmlFor="username" className="block text-sm font-medium text-gray-700 mb-2">
                Nombre de Usuario
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <User className="h-5 w-5 text-gray-400" />
                </div>
                <input
                  type="text"
                  id="username"
                  name="username"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  required
                  className="block w-full pl-10 pr-3 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-yellow-400 focus:border-transparent outline-none transition"
                  placeholder="juanperez"
                />
              </div>
            </div>

            {/* Empresa */}
            <div>
              <label htmlFor="nombreEmpresa" className="block text-sm font-medium text-gray-700 mb-2">
                Nombre de tu Empresa
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <Building2 className="h-5 w-5 text-gray-400" />
                </div>
                <input
                  type="text"
                  id="nombreEmpresa"
                  name="nombreEmpresa"
                  value={nombreEmpresa}
                  onChange={(e) => setNombreEmpresa(e.target.value)}
                  required
                  className="block w-full pl-10 pr-3 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-yellow-400 focus:border-transparent outline-none transition"
                  placeholder="Mi Empresa S.A."
                />
              </div>
            </div>

            {/* Email - ancho completo */}
            <div>
              <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-2">
                Correo Electrónico
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <Mail className="h-5 w-5 text-gray-400" />
                </div>
                <input
                  type="email"
                  id="email"
                  name="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  className="block w-full pl-10 pr-3 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-yellow-400 focus:border-transparent outline-none transition"
                  placeholder="usuario@empresa.com"
                />
              </div>
            </div>

            {/* Contraseña */}
            <div>
              <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-2">
                Contraseña
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <Lock className="h-5 w-5 text-gray-400" />
                </div>
                <input
                  type="password"
                  id="password"
                  name="password"
                  value={password}
                  onChange={handlePasswordChange}
                  required
                  minLength={8}
                  className="block w-full pl-10 pr-3 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-yellow-400 focus:border-transparent outline-none transition"
                  placeholder="Mínimo 8 caracteres"
                />
              </div>
              
              {/* Indicador de fortaleza de contraseña */}
              {password && (
                <div className="mt-2">
                  <div className="flex items-center gap-2 mb-1">
                    <div className="flex-1 h-2 bg-gray-200 rounded-full overflow-hidden">
                      <div 
                        className={`h-full ${getStrengthColor()} transition-all duration-300`}
                        style={{ width: `${(passwordStrength / 4) * 100}%` }}
                      />
                    </div>
                    <span className="text-xs font-medium text-gray-600">{getStrengthText()}</span>
                  </div>
                  <p className="text-xs text-gray-500">
                    Usa mayúsculas, minúsculas, números y símbolos
                  </p>
                </div>
              )}
            </div>

            {/* Confirmar Contraseña */}
            <div>
              <label htmlFor="passwordConfirm" className="block text-sm font-medium text-gray-700 mb-2">
                Confirmar Contraseña
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <CheckCircle2 className="h-5 w-5 text-gray-400" />
                </div>
                <input
                  type="password"
                  id="passwordConfirm"
                  name="passwordConfirm"
                  value={passwordConfirm}
                  onChange={(e) => setPasswordConfirm(e.target.value)}
                  required
                  minLength={8}
                  className="block w-full pl-10 pr-3 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-yellow-400 focus:border-transparent outline-none transition"
                  placeholder="Confirma tu contraseña"
                />
              </div>
              {passwordConfirm && password !== passwordConfirm && (
                <p className="mt-1 text-sm text-red-600">Las contraseñas no coinciden</p>
              )}
            </div>

            {/* Términos y condiciones */}
            <div className="flex items-start">
              <div className="flex items-center h-5">
                <input
                  id="terms"
                  name="terms"
                  type="checkbox"
                  required
                  className="w-4 h-4 border-gray-300 rounded text-yellow-400 focus:ring-yellow-400"
                />
              </div>
              <div className="ml-3 text-sm">
                <label htmlFor="terms" className="text-gray-700">
                  Acepto los{' '}
                  <a href="#" className="text-yellow-600 hover:text-yellow-700 font-medium">
                    términos y condiciones
                  </a>{' '}
                  y la{' '}
                  <a href="#" className="text-yellow-600 hover:text-yellow-700 font-medium">
                    política de privacidad
                  </a>
                </label>
              </div>
            </div>

            {/* Botón de registro */}
            <button
              type="submit"
              disabled={isLoading}
              className="w-full bg-yellow-400 text-black font-semibold py-4 px-4 rounded-lg hover:bg-yellow-500 transition-all shadow-lg shadow-yellow-400/30 hover:shadow-yellow-400/50 transform hover:-translate-y-0.5 disabled:opacity-70 disabled:cursor-not-allowed inline-flex items-center justify-center gap-2"
            >
              {isLoading ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin" />
                  Creando cuenta...
                </>
              ) : (
                'Crear Cuenta'
              )}
            </button>
          </form>

          {/* Divider */}
          <div className="relative my-6">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-gray-300"></div>
            </div>
            <div className="relative flex justify-center text-sm">
              <span className="px-4 bg-white text-gray-500">o</span>
            </div>
          </div>

          {/* Link a login */}
          <div className="text-center">
            <p className="text-gray-600">
              ¿Ya tienes cuenta?{' '}
              <Link to="/login" className="text-yellow-600 hover:text-yellow-700 font-semibold">
                Inicia Sesión
              </Link>
            </p>
          </div>

          {/* Link volver al inicio */}
          <div className="mt-4 text-center">
            <Link to="/" className="text-sm text-gray-500 hover:text-gray-700 inline-flex items-center">
              ← Volver al inicio
            </Link>
          </div>
        </div>

        {/* Footer */}
        <div className="text-center mt-6">
          <p className="text-gray-500 text-sm">
            © 2026 AEGIS. Todos los derechos reservados.
          </p>
        </div>
      </div>
    </div>
  );
}
