import axios from 'axios'
import {useEffect} from 'react'
import NavBar from '../components/NavBar/NavBar'
import Table from '../components/Table/Table'
import Footer from '../components/Footer/Footer'
import SearchBar from '../components/SearchBar/SearchBar'
import { useSearch } from '../hooks/useSearch'
import Cookie from 'js-cookie'; 
import {jwtDecode} from 'jwt-decode' 


const EstadoCuenta = () => {

  const userData = jwtDecode(Cookie.get("access_token"))
  const perfil = userData?.perfil;
  const fullName = userData?.full_name
  console.log(perfil);
  console.log(fullName);
  

  const apiUrl = import.meta.env.VITE_API_URL;
  const {setIsLoading, clientes, setClientes} = useSearch()

  const obtener_estado_cuenta = async () => {
      try {
      setIsLoading(true)
      if(perfil === 3){
        const response = await axios.get(`${apiUrl}obtener-cxc/?comercial=${fullName}`)
        setClientes(response.data)
      }else{
        const response = await axios.get(`${apiUrl}obtener-cxc/`)
        setClientes(response.data)
      }
      } catch (error) {
      console.error("Error al obtener datos:", error)
      } finally {
      setIsLoading(false)
      }
  }

  const consultar = async (term, termVendedor, emisionDesde, emisionHasta, venciDesde, venciHasta) => {
    try {
      setIsLoading(true)
      if(perfil === 3){
        const response = await axios.get(`${apiUrl}obtener-cxc/?cliente=${term}&comercial=${fullName}&emision_desde=${emisionDesde}&emision_hasta=${emisionHasta}&vencimiento_desde=${venciDesde}&vencimiento_hasta=${venciHasta}`, {})
        setClientes(response.data)
      }else{
        const response = await axios.get(`${apiUrl}obtener-cxc/?cliente=${term}&comercial=${termVendedor}&emision_desde=${emisionDesde}&emision_hasta=${emisionHasta}&vencimiento_desde=${venciDesde}&vencimiento_hasta=${venciHasta}`, {})
        setClientes(response.data)
      }
    } catch (error) {
      console.error("Error al obtener datos:", error)
    } finally {
      setIsLoading(false)
    }
  }


    useEffect(() => {
        obtener_estado_cuenta()
    }, [])

    return(
        <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
            <NavBar/>
            <main className="max-w-full mx-auto px-6 py-8">
              <SearchBar consultar={consultar}/>
              <Table data={clientes} />
              <Footer/>
            </main>
        </div>

    )
}

export default EstadoCuenta
