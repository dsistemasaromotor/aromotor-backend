"use client"

import { useNavigate } from "react-router-dom"

const NotFound = () => {
  const navigate = useNavigate()

  return (
    <div className="min-h-screen bg-white flex items-center justify-center px-4 py-12">
        
      <div className="absolute top-0 right-0 w-96 h-96 bg-gradient-to-br from-red-100 to-transparent rounded-full blur-3xl opacity-30 -z-10" />

      <div className="w-full max-w-md">
        <div className="mb-12 text-center">
          <div className="mb-6">
            <p className="text-9xl font-bold text-red-600">404</p>
          </div>
          <h1 className="text-4xl font-bold text-gray-900 mb-3">Página No Encontrada</h1>
          <p className="text-gray-500 text-base">La página que buscas no existe o ha sido movida.</p>
        </div>

        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-8">
          <button
            onClick={() => navigate("/estadoCuenta/home")}
            className="w-full py-3 px-4 bg-red-600 hover:bg-red-700 text-white font-semibold rounded-xl transition duration-200 flex items-center justify-center gap-2"
          >
            <svg
    width="20"
    height="20"
    viewBox="0 0 32 32"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
  >
    <circle cx="16" cy="16" r="13" />
    <polyline points="18,21 13,16 18,11" />
  </svg>
            Volver al Inicio
          </button>
        </div>
      </div>
    </div>
  )
}

export default NotFound
