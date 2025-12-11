import { SearchProvider } from './context/SearchContext.jsx'
import { BrowserRouter, Routes, Route  } from 'react-router-dom'
import Login from './pages/Login.jsx'
import EstadoCuenta from './pages/EstadoCuenta.jsx'
import MainWrapper from './layouts/MainWrapper.jsx'
import PrivateRoute from './layouts/PrivateRoute.jsx'
import SetPassword from './pages/SetPassword.jsx'
import NotFound from './pages/NotFound.jsx'
import Dashboard from './pages/Dashboard.jsx'
import Usuarios from './pages/Usuarios.jsx'
import CrearUsuario from './pages/CrearUsuario.jsx'
import EditarUsuario from './pages/EditarUsuario.jsx'

function App() {
  return (

    <BrowserRouter basename='/estadoCuenta'>
      <MainWrapper>
        <Routes>
          <Route path="/estadoCuenta/login" element={<Login/>} />
          <Route path="/estadoCuenta/home" element={<Dashboard/>} />
          <Route path="/estadoCuenta/set-password" element={<SetPassword/>} />
          <Route path="/estadoCuenta/usuarios" element={<Usuarios/>} />
          <Route path="/usuarios/editar/:id" element={<EditarUsuario />} />
          <Route 
            path="/usuarios/crear"  
            element={<CrearUsuario />} 
          />
          <Route
            path="/estadoCuenta/"
            element={
              <PrivateRoute>
                <SearchProvider>
                  <EstadoCuenta />
                </SearchProvider>
              </PrivateRoute>
            }
          />
          <Route path="*" element={<NotFound/>} />
        </Routes>
      </MainWrapper>
    </BrowserRouter>
  )
}

export default App
