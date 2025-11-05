import axios from 'axios'
import { useState, useEffect } from 'react'


function App() {

  const [datos, setDatos] = useState([])
  

  const obtenerDatos = () => {
    axios.get('http://127.0.0.1:8000/api/datos/')
      .then(response => {
        setDatos(response.data.mensaje)
        console.log(response.data)
      })
  }

  useEffect(() => {
    obtenerDatos()
  }, [])
  console.log('Datos obtenidos:', datos)
  
 

  return (
    <div className='font-bold'>
      {datos}
    </div>
  )
}

export default App
