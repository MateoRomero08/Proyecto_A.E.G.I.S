import { Link } from 'react-router-dom';
import { Shield, Mail, Phone, MapPin } from 'lucide-react';

export function Footer() {
  return (
    <footer className="bg-slate-900 text-gray-300 pt-16 pb-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-12 mb-12">
          {/* Logo y descripción */}
          <div className="col-span-1 md:col-span-2">
            <div className="flex items-center space-x-3 mb-4">
              <div className="flex items-center justify-center w-10 h-10 bg-yellow-400 rounded-lg">
                <Shield className="w-6 h-6 text-black" />
              </div>
              <span className="text-2xl font-bold text-white">A.E.G.I.S</span>
            </div>
            <p className="text-gray-400 mb-6 max-w-md">
              Aplicación de Evaluación y Gestión para la ISO 27001 y Seguridad de la información.
              
              Tu aliado tecnológico para la ISO 27001. A.E.G.I.S. delimita un entorno de trabajo claro y estructurado para que gestiones evidencias, evalúes controles y capacites a tu equipo bajo los lineamientos del estándar internacional de seguridad de la información.
            </p>
            <div className="flex space-x-4">
              <a href="#" className="w-10 h-10 bg-white/10 rounded-lg flex items-center justify-center hover:bg-yellow-400 hover:text-black transition-colors">
                <span className="font-bold">f</span>
              </a>
              <a href="#" className="w-10 h-10 bg-white/10 rounded-lg flex items-center justify-center hover:bg-yellow-400 hover:text-black transition-colors">
                <span className="font-bold">in</span>
              </a>
              <a href="#" className="w-10 h-10 bg-white/10 rounded-lg flex items-center justify-center hover:bg-yellow-400 hover:text-black transition-colors">
                <span className="font-bold">𝕏</span>
              </a>
            </div>
          </div>

          {/* Enlaces rápidos */}
          <div>
            <h3 className="text-white font-bold text-lg mb-4">Enlaces</h3>
            <ul className="space-y-3">
              <li>
                <a href="#features" className="hover:text-yellow-400 transition-colors">
                  Características
                </a>
              </li>
              <li>
                <Link to="/registro" className="hover:text-yellow-400 transition-colors">
                  Registrarse
                </Link>
              </li>
              <li>
                <Link to="/login" className="hover:text-yellow-400 transition-colors">
                  Iniciar Sesión
                </Link>
              </li>
              <li>
                <a href="#" className="hover:text-yellow-400 transition-colors">
                  Documentación
                </a>
              </li>
            </ul>
          </div>

          {/* Contacto */}
          <div>
            <h3 className="text-white font-bold text-lg mb-4">Contacto</h3>
            <ul className="space-y-3">
              <li className="flex items-start gap-2">
                <Mail className="w-5 h-5 text-yellow-400 mt-0.5" />
                <span className="text-sm">contacto@aegis.com</span>
              </li>
              <li className="flex items-start gap-2">
                <Phone className="w-5 h-5 text-yellow-400 mt-0.5" />
                <span className="text-sm">+1 (555) 123-4567</span>
              </li>
              <li className="flex items-start gap-2">
                <MapPin className="w-5 h-5 text-yellow-400 mt-0.5" />
                <span className="text-sm">Ciudad de México, México</span>
              </li>
            </ul>
          </div>
        </div>

        {/* Línea divisoria */}
        <div className="border-t border-gray-800 pt-8">
          <div className="flex flex-col md:flex-row justify-between items-center gap-4">
            <p className="text-gray-400 text-sm">
              © 2026 AEGIS. Todos los derechos reservados.
            </p>
            <div className="flex gap-6 text-sm">
              <a href="#" className="hover:text-yellow-400 transition-colors">
                Términos de Servicio
              </a>
              <a href="#" className="hover:text-yellow-400 transition-colors">
                Política de Privacidad
              </a>
              <a href="#" className="hover:text-yellow-400 transition-colors">
                Cookies
              </a>
            </div>
          </div>
        </div>
      </div>
    </footer>
  );
}
