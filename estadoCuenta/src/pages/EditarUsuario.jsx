import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from "../utils/axios";
import Cookies from 'js-cookie';  // Asegúrate de tener js-cookie instalado
import NavBar from "../components/NavBar/NavBar";

const EditarUsuario = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    full_name: '',
    email: '',
    cedula: '',
    genero: '',
    fecha_nacimiento: '',
    telefono: '',
    id_perfil_FK: '',
  });
  const [perfiles, setPerfiles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchUsuario = async () => {
      try {
        const response = await axios.get(`/users/${id}/`);
        setFormData({
          ...response.data,
          id_perfil_FK: response.data.id_perfil_FK ? response.data.id_perfil_FK.toString() : '',
        });
      } catch (err) {
        setError('Error al cargar usuario: ' + (err.response?.data?.detail || 'Desconocido'));
      } finally {
        setLoading(false);
      }
    };

    const fetchPerfiles = async () => {
      try {
        const response = await axios.get('/perfiles/');
        setPerfiles(response.data);
      } catch (err) {
        console.error('Error cargando perfiles:', err);
      }
    };

    fetchUsuario();
    fetchPerfiles();
  }, [id]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData({ ...formData, [name]: value });
  };

  // Función para refrescar el token
  const refreshToken = async () => {
  try {
    const refreshTokenValue = Cookies.get('refresh_token');  // Asumiendo que guardas el refresh token en cookies
    if (!refreshTokenValue) throw new Error('No hay refresh token');
    
    const response = await axios.post('/token/refresh/', { refresh: refreshTokenValue });
    Cookies.set('access_token', response.data.access, { expires: 7 });  // Actualiza el access token
    alert('Permisos actualizados. Los cambios surtirán efecto ahora.');
  } catch (err) {
    console.error('Error refrescando token:', err);
    alert('Error al actualizar permisos. Haz logout y login de nuevo.');
  }
};

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      await axios.put(`/users/${id}/`, {
        ...formData,
        id_perfil_FK: formData.id_perfil_FK ? parseInt(formData.id_perfil_FK) : null,
      });
      
      // Refresca el token si el admin está editando su propio perfil
      if (parseInt(id) === getCurrentUserId()) {  // Función para obtener ID del usuario logueado
        await refreshToken();
        alert('Usuario actualizado exitosamente. Permisos actualizados.');
      } else {
        alert('Usuario actualizado exitosamente.');
      }
      
      navigate('/estadoCuenta/usuarios/');
    } catch (err) {
      setError('Error al actualizar: ' + (err.response?.data?.detail || 'Desconocido'));
    } finally {
      setSaving(false);
    }
  };

  // Función auxiliar para obtener el ID del usuario logueado (decodificando el token)
  const getCurrentUserId = () => {
    const token = Cookies.get('access_token');
    if (!token) return null;
    try {
      const decoded = jwtDecode(token);  // Necesitas importar jwtDecode
      return decoded.user_id;  // Asumiendo que tienes 'user_id' en el token
    } catch {
      return null;
    }
  };

  if (loading) return <div className="min-h-screen bg-white flex items-center justify-center">Cargando...</div>;
  if (error) return <div className="min-h-screen bg-white flex items-center justify-center text-red-600">{error}</div>;

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
      <NavBar />
      <div className="max-w-2xl mx-auto px-6 py-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-6">Editar Usuario</h1>
        <form onSubmit={handleSubmit} className="bg-white p-6 rounded-xl shadow-sm border">
          {/* Campos del formulario (iguales) */}
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
            className="w-full py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:bg-gray-400"
          >
            {saving ? 'Guardando...' : 'Actualizar Usuario'}
          </button>
        </form>
      </div>
    </div>
  );
};

export default EditarUsuario;