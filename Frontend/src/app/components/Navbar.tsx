import { Link } from 'react-router-dom';
import { Shield } from 'lucide-react';

export function Navbar() {
  return (
    <nav className="sticky top-0 z-50 bg-white border-b border-gray-200 shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Logo y nombre */}
          <Link to="/" className="flex items-center space-x-3 group">
            <div className="flex items-center justify-center w-10 h-10 bg-yellow-400 rounded-lg group-hover:bg-yellow-500 transition-colors">
              <Shield className="w-6 h-6 text-black" />
            </div>
            <span className="text-2xl font-bold text-gray-900 group-hover:text-gray-700 transition-colors">
              A.E.G.I.S
            </span>
          </Link>

          {/* Botones de acción */}
          <div className="flex items-center space-x-4">
            <Link
              to="/login"
              className="px-5 py-2 text-gray-700 font-medium hover:text-gray-900 transition-colors"
            >
              Iniciar Sesión
            </Link>
            <Link
              to="/registro"
              className="px-5 py-2 bg-yellow-400 text-black font-semibold rounded-lg hover:bg-yellow-500 transition-colors shadow-md hover:shadow-lg"
            >
              Registrarse
            </Link>
          </div>
        </div>
      </div>
    </nav>
  );
}
