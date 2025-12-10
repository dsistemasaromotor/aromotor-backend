import { useState} from "react"
import { useNavigate } from "react-router-dom"
import {login} from "../utils/auth"
import Swal from "sweetalert2";

const Login = () => {

    const [email, setEmail] = useState("")
    const [password, setPassword] = useState("")
    const [isLoading, setIsLoading] = useState(false)
    const navigate = useNavigate()


    const [error, setError] = useState("")
    const [isLoggedIn, setIsLoggedIn] = useState(false)


    const handleSubmit = async (e) => {
        e.preventDefault()
        setIsLoading(true)
        const { error } = await login(email, password);
        if (error) {
            setIsLoading(false);
            Swal.fire({
                icon: 'error', // Icono de error
                title: 'Error',
                text: 'Correo o contreña incorrectos.',
                confirmButtonText: 'OK',
            });
        } else {
            navigate("/estadoCuenta/home");
            setIsLoading(false);
        }
    }

    if (isLoggedIn) {
        return (
        <div className="min-h-screen bg-white flex items-center justify-center px-4 py-12">
            <div className="absolute top-0 right-0 w-96 h-96 bg-gradient-to-br from-red-100 to-transparent rounded-full blur-3xl opacity-30 -z-10" />

            <div className="w-full max-w-md text-center">
            <div className="mb-8">
                <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <span className="text-3xl">✓</span>
                </div>
                <h1 className="text-3xl font-bold text-gray-900 mb-2">¡Bienvenido!</h1>
                <p className="text-gray-500">Has iniciado sesión exitosamente</p>
            </div>

            <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-8 space-y-6">
                <div>
                <p className="text-gray-600 text-sm mb-1">Cuenta conectada</p>
                <p className="text-lg font-semibold text-gray-900">{email}</p>
                </div>

                <button
                onClick={handleLogout}
                className="w-full py-3 px-4 bg-red-600 hover:bg-red-700 text-white font-semibold rounded-xl transition duration-200"
                >
                Cerrar sesión
                </button>
            </div>
            </div>
        </div>
        )
    }
    return (
    <div className="min-h-screen bg-white flex items-center justify-center px-4 py-12">
      <div className="absolute top-0 right-0 w-96 h-96 bg-gradient-to-br from-red-100 to-transparent rounded-full blur-3xl opacity-30 -z-10" />

      <div className="w-full max-w-md">
        <div className="mb-12 text-center">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">Bienvenido</h1>
          <p className="text-gray-500 text-base">Inicia sesión en tu cuenta</p>
        </div>

        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-8">
          <form onSubmit={handleSubmit} className="space-y-5">
            <div className="space-y-2">
              <label htmlFor="email" className="block text-sm font-semibold text-gray-900">
                Email
              </label>
              <input
                id="email"
                type="email"
                placeholder="ejemplo@correo.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-xl text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-red-600 focus:border-transparent transition"
              />
            </div>

            <div className="space-y-2">
              <label htmlFor="password" className="block text-sm font-semibold text-gray-900">
                Contraseña
              </label>
              <input
                id="password"
                type="password"
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-xl text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-red-600 focus:border-transparent transition"
              />
            </div>

            {error && (
              <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
                <p className="text-sm text-red-700">{error}</p>
              </div>
            )}

            <button
              type="submit"
              disabled={isLoading}
              className="w-full py-3 px-4 bg-red-600 hover:bg-red-700 disabled:bg-gray-400 text-white font-semibold rounded-xl transition duration-200 mt-6 flex items-center justify-center gap-2"
            >
              {isLoading ? (
                <>
                  <span className="inline-block w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  Iniciando sesión...
                </>
              ) : (
                "Iniciar sesión"
              )}
            </button>
          </form>
        </div>
      </div>
    </div>
  )
}
export default Login   