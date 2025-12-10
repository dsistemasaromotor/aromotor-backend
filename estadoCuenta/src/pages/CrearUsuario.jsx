import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from "../utils/axios";
import NavBar from "../components/NavBar/NavBar";
import Swal from "sweetalert2" // Import SweetAlert2


const CrearUsuario = () => {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    full_name: '',
    email: '',
    cedula: '',
    genero: '',
    fecha_nacimiento: '',
    telefono: '',
    id_perfil_FK: '',  // Cambié a string vacío para select
  });
  const [perfiles, setPerfiles] = useState([]);  // Estado para perfiles
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [enlace, setEnlace] = useState('');

  // Cargar perfiles al montar
  useEffect(() => {
    const fetchPerfiles = async () => {
      try {
        const response = await axios.get('/perfiles/');
        setPerfiles(response.data);
      } catch (err) {
        console.error('Error cargando perfiles:', err);
      }
    };
    fetchPerfiles();
  }, []);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData({ ...formData, [name]: value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      const response = await axios.post('/crear-usuario/', {
        ...formData,
        id_perfil_FK: formData.id_perfil_FK ? parseInt(formData.id_perfil_FK) : null,  // Convertir a int o null
      });
      setEnlace(response.data.enlace_cambiar_contraseña);
      Swal.fire({
        title: "Enlace Generado",
        html: `
          <div style="text-align: left;">
            <p style="margin-bottom: 15px; color: #666;">Comparte este enlace con el usuario:</p>
            <div style="background: #f5f5f5; padding: 12px; border-radius: 8px; word-break: break-all; font-family: monospace; font-size: 13px; color: #333;">
              ${response.data.enlace_cambiar_contraseña}
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
    } catch (err) {
      setError('Error al crear: ' + (err.response?.data?.detail || 'Desconocido'));
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
      <NavBar />
      <div className="max-w-2xl mx-auto px-6 py-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-6">Crear Usuario</h1>
        <form onSubmit={handleSubmit} className="bg-white p-6 rounded-xl shadow-sm border">
          {/* Campos existentes */}
          <div className="mb-4">
            <label className="block text-gray-700">Nombre Completo</label>
            <input
              type="text"
              name="full_name"
              value={formData.full_name}
              onChange={handleChange}
              className="w-full p-2 border rounded"
              required
            />
          </div>
          <div className="mb-4">
            <label className="block text-gray-700">Email</label>
            <input
              type="email"
              name="email"
              value={formData.email}
              onChange={handleChange}
              className="w-full p-2 border rounded"
              required
            />
          </div>
          <div className="mb-4">
            <label className="block text-gray-700">Cédula</label>
            <input
              type="text"
              name="cedula"
              value={formData.cedula}
              onChange={handleChange}
              className="w-full p-2 border rounded"
            />
          </div>
          <div className="mb-4">
            <label className="block text-gray-700">Género</label>
            <select
              name="genero"
              value={formData.genero}
              onChange={handleChange}
              className="w-full p-2 border rounded"
            >
              <option value="">Seleccionar</option>
              <option value="Masculino">Masculino</option>
              <option value="Femenino">Femenino</option>
            </select>
          </div>
          <div className="mb-4">
            <label className="block text-gray-700">Fecha de Nacimiento</label>
            <input
              type="date"
              name="fecha_nacimiento"
              value={formData.fecha_nacimiento}
              onChange={handleChange}
              className="w-full p-2 border rounded"
            />
          </div>
          <div className="mb-4">
            <label className="block text-gray-700">Teléfono</label>
            <input
              type="text"
              name="telefono"
              value={formData.telefono}
              onChange={handleChange}
              className="w-full p-2 border rounded"
            />
          </div>
          {/* Nuevo campo para perfil */}
          <div className="mb-4">
            <label className="block text-gray-700">Perfil</label>
            <select
              name="id_perfil_FK"
              value={formData.id_perfil_FK}
              onChange={handleChange}
              className="w-full p-2 border rounded"
            >
              <option value="">Seleccionar Perfil</option>
              {perfiles.map((perfil) => (
                <option key={perfil.id} value={perfil.id}>
                  {perfil.perfil} - {perfil.descripcion}
                </option>
              ))}
            </select>
          </div>
          <button
            type="submit"
            disabled={saving}
            className="w-full py-2 bg-green-600 text-white rounded hover:bg-green-700 disabled:bg-gray-400"
          >
            {saving ? 'Creando...' : 'Crear Usuario'}
          </button>
        </form>
        {error && <p className="text-red-600 mt-4">{error}</p>}
      </div>
    </div>
  );
};

export default CrearUsuario;