"use client"

import { useState, useEffect } from "react"
import { useNavigate } from "react-router-dom"
import axios from "../utils/axios"
import NavBar from "../components/NavBar/NavBar"
import Swal from "sweetalert2" // Import SweetAlert2

const Usuarios = () => {
  const navigate = useNavigate()
  const [usuarios, setUsuarios] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState("")
  const [generating, setGenerating] = useState(null)

  const generarEnlace = async (userId) => {
    setGenerating(userId)
    try {
      const response = await axios.post("/generar-enlace-reset/", { user_id: userId })
      const enlace = response.data.enlace_cambiar_contraseña

      Swal.fire({
        title: "Enlace Generado",
        html: `
          <div style="text-align: left;">
            <p style="margin-bottom: 15px; color: #666;">Comparte este enlace con el usuario:</p>
            <div style="background: #f5f5f5; padding: 12px; border-radius: 8px; word-break: break-all; font-family: monospace; font-size: 13px; color: #333;">
              ${enlace}
            </div>
          </div>
        `,
        icon: "success",
        confirmButtonText: "Cerrar",
        confirmButtonColor: "#dc2626",
        didOpen: () => {
          // Add copy button dynamically
          const copyBtn = document.createElement("button")
          copyBtn.textContent = "Copiar Enlace"
          copyBtn.style.cssText =
            "padding: 10px 20px; background: #10b981; color: white; border: none; border-radius: 6px; cursor: pointer; margin-right: 10px; font-weight: 500;"
          copyBtn.onmouseover = () => (copyBtn.style.background = "#059669")
          copyBtn.onmouseout = () => (copyBtn.style.background = "#10b981")
          copyBtn.onclick = () => {
            navigator.clipboard.writeText(enlace)
            Swal.showValidationMessage("¡Enlace copiado al portapapeles!")
          }

          const buttonContainer = Swal.getHtmlContainer().parentElement.querySelector(".swal2-actions")
          buttonContainer.insertBefore(copyBtn, buttonContainer.firstChild)
        },
      })
    } catch (error) {
      setError("Error al generar enlace: " + (error.response?.data?.error || "Desconocido"))
    } finally {
      setGenerating(null)
    }
  }

  const handleEdit = (userId) => {
    navigate(`/usuarios/editar/${userId}`)
  }

  const handleCreate = () => {
    navigate("/usuarios/crear")
  }

  useEffect(() => {
    const fetchUsuarios = async () => {
      try {
        const response = await axios.get("/users")
        console.log(response.data)
        const sortedUsuarios = response.data.sort((a, b) =>
          (a.full_name || a.username).localeCompare(b.full_name || b.username),
        )
        setUsuarios(sortedUsuarios)
      } catch (err) {
        setError("Error al cargar usuarios: " + (err.response?.data?.detail || "Desconocido"))
      } finally {
        setLoading(false)
      }
    }
    fetchUsuarios()
  }, [])

  if (loading) {
    return (
      <div className="min-h-screen bg-white flex items-center justify-center">
        <div className="flex items-center gap-3">
          <span className="inline-block w-6 h-6 border-2 border-red-600 border-t-transparent rounded-full animate-spin" />
          <p className="text-gray-600">Cargando usuarios...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen bg-white flex items-center justify-center px-4">
        <div className="bg-red-50 border border-red-200 rounded-xl p-6 max-w-md text-center">
          <p className="text-red-700 font-semibold">{error}</p>
          <button
            onClick={() => window.location.reload()}
            className="mt-4 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition"
          >
            Reintentar
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
      <NavBar />

      {/* Fondo decorativo */}
      <div className="absolute top-0 left-0 w-96 h-96 bg-gradient-to-br from-red-100 to-transparent rounded-full blur-3xl opacity-30 -z-10" />
      <div className="absolute bottom-0 right-0 w-96 h-96 bg-gradient-to-tl from-orange-100 to-transparent rounded-full blur-3xl opacity-30 -z-10" />

      <div className="max-w-7xl mx-auto px-6 py-8">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">Listado de Usuarios</h1>
          <p className="text-gray-500">Gestiona los usuarios y genera enlaces para cambio de contraseña</p>
          {/* Botón para crear usuario */}
          <button
            onClick={handleCreate}
            className="mt-4 px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition"
          >
            Crear Usuario
          </button>
        </div>

        {/* Lista ordenada */}
        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
          <ul className="space-y-4">
            {usuarios.map((user) => (
              <li
                key={user.id}
                className="flex items-center justify-between p-4 bg-gray-50 rounded-xl hover:bg-gray-100 transition duration-200 cursor-pointer"
                onClick={() => handleEdit(user.id)}
              >
                <div>
                  <h3 className="text-lg font-semibold text-gray-900">{user.full_name || user.username}</h3>
                  <p className="text-sm text-gray-500">
                    @{user.username} - {user.email}
                  </p>
                </div>
                <button
                  onClick={(e) => {
                    e.stopPropagation()
                    generarEnlace(user.id)
                  }}
                  disabled={generating === user.id}
                  className="py-2 px-4 bg-red-600 hover:bg-red-700 disabled:bg-gray-400 text-white font-semibold rounded-lg transition duration-200 flex items-center gap-2"
                >
                  {generating === user.id ? (
                    <>
                      <span className="inline-block w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                      Generando...
                    </>
                  ) : (
                    "Cambiar Contraseña"
                  )}
                </button>
              </li>
            ))}
          </ul>
        </div>

        {usuarios.length === 0 && (
          <div className="text-center mt-12">
            <p className="text-gray-500">No hay usuarios registrados.</p>
          </div>
        )}
      </div>
    </div>
  )
}

export default Usuarios
