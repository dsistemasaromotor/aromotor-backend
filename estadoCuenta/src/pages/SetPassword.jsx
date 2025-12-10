"use client"

import { useState } from "react"
import { useSearchParams, useNavigate } from "react-router-dom"
import axios from "../utils/axios"
import Swal from "sweetalert2"
import {jwtDecode} from 'jwt-decode'

const SetPassword = () => {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const [newPassword, setNewPassword] = useState("")
  const [confirmPassword, setConfirmPassword] = useState("")
  const [error, setError] = useState("")
  const [success, setSuccess] = useState(false)
  const [isLoading, setIsLoading] = useState(false)

  const token = searchParams.get("token")
  const decoded = jwtDecode(token);

  const handleSubmit = async (e) => {
    e.preventDefault()
    setIsLoading(true)

    if (newPassword !== confirmPassword) {
      setError("Las contraseñas no coinciden")
      setIsLoading(false)
      return
    }

    try {
      await axios.post("/set-password/", { token, new_password: newPassword, confirm_password: confirmPassword })
      setSuccess(true)
      Swal.fire({
        icon: "success",
        title: "Éxito",
        text: "Contraseña actualizada. Redirigiendo...",
        confirmButtonText: "OK",
      })
      setTimeout(() => navigate("/estadoCuenta/login"), 2000)
    } catch (err) {
      setIsLoading(false)
      Swal.fire({
        icon: "error",
        title: "Error",
        text: "Error al actualizar contraseña. Token inválido o expirado.",
        confirmButtonText: "OK",
      })
    }
  }

  if (!token) {
    return (
      <div className="min-h-screen bg-white flex items-center justify-center px-4 py-12">
        <div className="absolute top-0 right-0 w-96 h-96 bg-gradient-to-br from-red-100 to-transparent rounded-full blur-3xl opacity-30 -z-10" />
        <div className="w-full max-w-md text-center">
          <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-8">
            <p className="text-red-600 font-semibold">Enlace inválido o expirado</p>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-white flex items-center justify-center px-4 py-12">
      <div className="absolute top-0 right-0 w-96 h-96 bg-gradient-to-br from-red-100 to-transparent rounded-full blur-3xl opacity-30 -z-10" />

      <div className="w-full max-w-md">
        <div className="mb-4 text-center">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">Establece tu contraseña</h1>
          {decoded?.full_name && (
            <div className="inline-block bg-gradient-to-r from-red-50 to-orange-50 border border-red-200 rounded-full px-4 py-2 mb-4">
              <p className="text-sm font-semibold text-red-700">
                Bienvenido, <span className="font-bold text-red-900">{decoded.full_name}</span>
              </p>
            </div>
          )}
          <p className="text-gray-500 text-base">Crea una nueva contraseña segura para tu cuenta</p>
        </div>

        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-8">
          <form onSubmit={handleSubmit} className="space-y-5">
            <div className="space-y-2">
              <label htmlFor="newPassword" className="block text-sm font-semibold text-gray-900">
                Nueva contraseña
              </label>
              <input
                id="newPassword"
                type="password"
                placeholder="••••••••"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                className="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-xl text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-red-600 focus:border-transparent transition"
                required
              />
            </div>

            <div className="space-y-2">
              <label htmlFor="confirmPassword" className="block text-sm font-semibold text-gray-900">
                Confirma contraseña
              </label>
              <input
                id="confirmPassword"
                type="password"
                placeholder="••••••••"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                className="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-xl text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-red-600 focus:border-transparent transition"
                required
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
                  Actualizando...
                </>
              ) : (
                "Guardar contraseña"
              )}
            </button>
          </form>
        </div>
      </div>
    </div>
  )
}

export default SetPassword
