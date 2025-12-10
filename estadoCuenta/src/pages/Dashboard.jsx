"use client"
import { useNavigate } from "react-router-dom"
import { jwtDecode } from "jwt-decode"  // Para decodificar el token
import Cookies from "js-cookie"  // Para leer cookies
import NavBar from "../components/NavBar/NavBar"

const modules = [
  {
    id: "cartera",
    name: "Cartera",
    description: "Gestiona y controla tu cartera de cuentas",
    icon: (
      <svg className="w-10 h-10" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M17 9V7a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2m2 4h10a2 2 0 002-2v-6a2 2 0 00-2-2H9a2 2 0 00-2 2v6a2 2 0 002 2zm7-5a2 2 0 11-4 0 2 2 0 014 0z"
        />
      </svg>
    ),
    color: "from-emerald-500 to-teal-600",
    bgColor: "from-emerald-50 to-teal-100",
    textColor: "text-emerald-600",
    hoverTextColor: "group-hover:text-emerald-700",
    path: "/estadoCuenta",
    permission: "can_view_cartera",  // Clave del permiso requerido para ver este módulo
  },
  {
    id: "ajustes",
    name: "Ajustes",
    description: "Configura los parámetros de tu aplicación",
    icon: (
      <svg className="w-10 h-10" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 100 4m0-4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 100 4m0-4v2m0-6V4"
        />
      </svg>
    ),
    color: "from-blue-500 to-indigo-600",
    bgColor: "from-blue-50 to-indigo-100",
    textColor: "text-blue-600",
    hoverTextColor: "group-hover:text-blue-700",
    path: "/ajustes",
    permission: "can_view_ajustes",
  },
  {
    id: "usuarios",
    name: "Usuarios",
    description: "Gestionar y controlas permisos de usuarios",
    icon: (
      <svg className="w-10 h-10" fill="#000000" width="800px" height="800px" viewBox="0 0 48 48" data-name="Layer 1" id="Layer_1" xmlns="http://www.w3.org/2000/svg">
        <title/>
        <path d="M24,21A10,10,0,1,1,34,11,10,10,0,0,1,24,21ZM24,5a6,6,0,1,0,6,6A6,6,0,0,0,24,5Z"/>
        <path d="M42,47H6a2,2,0,0,1-2-2V39A16,16,0,0,1,20,23h8A16,16,0,0,1,44,39v6A2,2,0,0,1,42,47ZM8,43H40V39A12,12,0,0,0,28,27H20A12,12,0,0,0,8,39Z"/>
      </svg>
    ),
    color: "from-blue-500 to-indigo-600",
    bgColor: "from-blue-50 to-indigo-100",
    textColor: "text-blue-600",
    hoverTextColor: "group-hover:text-blue-700",
    path: "/estadoCuenta/usuarios",
    permission: "can_view_usuarios",
  },
]

export default function Dashboard() {
  const navigate = useNavigate()

  // Función para obtener permisos del token (de cookies)
  const getUserPermissions = () => {
    const token = Cookies.get("access_token")  // Leer token de cookies
    if (!token) {
      // Si no hay token, permisos por defecto (todos false)
      return {
        can_view_cartera: false,
        can_view_ajustes: false,
        can_view_usuarios: false,
      }
    }
    
    try {
      const decoded = jwtDecode(token)
      // Retornar los permisos del token, o valores por defecto si no existen
      return decoded.permisos || {
        can_view_cartera: false,
        can_view_ajustes: false,
        can_view_usuarios: false,
      }
    } catch (error) {
      console.error("Error decodificando token:", error)
      // En caso de error, permisos por defecto
      return {
        can_view_cartera: false,
        can_view_ajustes: false,
        can_view_usuarios: false,
      }
    }
  }

  const userPermissions = getUserPermissions()

  // Filtrar módulos basados en permisos: solo mostrar si el usuario tiene el permiso correspondiente
  const allowedModules = modules.filter(module => userPermissions[module.permission])

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
      <NavBar />
      <div className="max-w-7xl mx-auto px-6 py-8">
        <div className="mb-10">
          <h1 className="text-4xl font-bold text-gray-900">Dashboard</h1>
          <p className="text-gray-600 mt-2">Bienvenido a tu panel de control</p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          {allowedModules.map((module) => (
            <button
              key={module.id}
              onClick={() => navigate(module.path)}
              className="group relative h-48 overflow-hidden rounded-xl bg-white shadow-lg hover:shadow-2xl transition-all duration-300 border border-gray-200 hover:border-gray-300 transform hover:-translate-y-1"
            >
              <div
                className={`absolute inset-0 bg-gradient-to-br ${module.color} opacity-0 group-hover:opacity-5 transition-opacity duration-300`}
              />

              <div className="relative h-full p-6 flex flex-col justify-between">
                <div className="flex justify-center items-center">
                  <div className={`p-3 rounded-full bg-gradient-to-br ${module.bgColor} ${module.textColor} group-hover:scale-110 transition-transform duration-300`}>
                    {module.icon}
                  </div>
                </div>

                <div className="text-center">
                  <h3 className={`text-lg font-bold text-gray-900 ${module.hoverTextColor} transition-colors duration-300`}>
                    {module.name}
                  </h3>
                  <p className="text-sm text-gray-600 mt-2 group-hover:text-gray-700 transition-colors duration-300">
                    {module.description}
                  </p>
                </div>

                <div className="flex justify-center">
                  <svg
                    className="w-5 h-5 text-gray-400 group-hover:text-gray-600 transform group-hover:translate-x-1 transition-all duration-300"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                </div>
              </div>
            </button>
          ))}
        </div>

        {/* Mensaje si no hay módulos permitidos */}
        {allowedModules.length === 0 && (
          <div className="text-center mt-10">
            <p className="text-gray-500">No tienes permisos para acceder a ningún módulo. Contacta a un administrador.</p>
          </div>
        )}
      </div>
    </div>
  )
}
