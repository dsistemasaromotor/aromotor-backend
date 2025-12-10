import { Search } from 'lucide-react'
import { useSearch } from '../../hooks/useSearch'
import Cookie from 'js-cookie'; 
import { jwtDecode } from 'jwt-decode'  // Cambié a 'jwt-decode' por consistencia

const SearchBar = ({ consultar }) => {
  const { clientes, searchTerm, setSearchTerm, searchTermVendedor, setSearchTermVendedor, fechaEmisionDesde, setFechaEmisionDesde, fechaEmisionHasta, setFechaEmisionHasta, fechaVenciDesde, setFechaVenciDesde, fechaVenciHasta, setFechaVenciHasta } = useSearch()

  const userData = jwtDecode(Cookie.get("access_token"))
  const perfil = userData?.perfil;

  return (
    <div className="mb-8">
      <div className="bg-white rounded-2xl border border-gray-200 p-4 md:p-6 shadow-sm mb-4">
        {/* Flex en columna por defecto, fila solo en pantallas grandes (lg = 1024px) */}
        <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:gap-4">

          {/* Buscar: ocupa 2 partes del espacio en lg */}
          <div className="bg-gray-50 border border-gray-200 rounded-lg p-3 md:p-4 flex flex-col gap-3 lg:gap-3 lg:flex-[2]">
            <h3 className="text-xs md:text-sm font-semibold text-gray-700">
              Buscar
            </h3>
            <div className="flex flex-col md:flex-row gap-3">
              <div className="flex-1">
                <label className="block text-xs font-semibold text-gray-600 mb-1">
                  Cliente
                </label>
                <input
                  type="text"
                  placeholder="Ingrese nombre..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="w-full px-3 py-2 bg-white border-2 border-gray-200 rounded-lg focus:outline-none focus:border-red-600 focus:ring-2 focus:ring-red-100 transition-all text-xs text-gray-900"
                />
              </div>

              {/* Campo Vendedor: Solo mostrar si perfil !== 3 */}
              {perfil !== 3 && (
                <div className="flex-1">
                  <label className="block text-xs font-semibold text-gray-600 mb-1">
                    Vendedor
                  </label>
                  <input
                    type="text"
                    placeholder="Ingrese nombre..."
                    value={searchTermVendedor}
                    onChange={(e) => setSearchTermVendedor(e.target.value)}
                    className="w-full px-3 py-2 bg-white border-2 border-gray-200 rounded-lg focus:outline-none focus:border-red-600 focus:ring-2 focus:ring-red-100 transition-all text-xs text-gray-900"
                  />
                </div>
              )}
            </div>
          </div>

          {/* Fecha de emisión: ocupa 1 parte en lg */}
          <div className="bg-gray-50 border border-gray-200 rounded-lg p-3 md:p-4 flex flex-col gap-3 lg:gap-3 lg:flex-1">
            <h3 className="text-xs md:text-sm font-semibold text-gray-700">
              Fecha de emisión
            </h3>
            <div className="flex flex-col md:flex-row gap-3">
              <div className="flex-1">
                <label className="block text-xs font-semibold text-gray-600 mb-1">
                  Desde
                </label>
                <input
                  value={fechaEmisionDesde}
                  onChange={(e) => setFechaEmisionDesde(e.target.value)}
                  type="date"
                  className="w-full px-3 py-2 bg-white border-2 border-gray-200 rounded-lg focus:outline-none focus:border-red-600 focus:ring-2 focus:ring-red-100 transition-all text-xs text-gray-900"
                />
              </div>
              <div className="flex-1">
                <label className="block text-xs font-semibold text-gray-600 mb-1">
                  Hasta
                </label>
                <input
                  value={fechaEmisionHasta}
                  onChange={(e) => setFechaEmisionHasta(e.target.value)}
                  type="date"
                  className="w-full px-3 py-2 bg-white border-2 border-gray-200 rounded-lg focus:outline-none focus:border-red-600 focus:ring-2 focus:ring-red-100 transition-all text-xs text-gray-900"
                />
              </div>
            </div>
          </div>

          {/* Fecha de Vencimiento: ocupa 1 parte en lg */}
          <div className="bg-gray-50 border border-gray-200 rounded-lg p-3 md:p-4 flex flex-col gap-3 lg:gap-3 lg:flex-1">
            <h3 className="text-xs md:text-sm font-semibold text-gray-700">
              Fecha de Vencimiento
            </h3>
            <div className="flex flex-col md:flex-row gap-3">
              <div className="flex-1">
                <label className="block text-xs font-semibold text-gray-600 mb-1">
                  Desde
                </label>
                <input
                  value={fechaVenciDesde}
                  onChange={(e) => setFechaVenciDesde(e.target.value)}
                  type="date"
                  className="w-full px-3 py-2 bg-white border-2 border-gray-200 rounded-lg focus:outline-none focus:border-red-600 focus:ring-2 focus:ring-red-100 transition-all text-xs text-gray-900"
                />
              </div>

              <div className="flex-1">
                <label className="block text-xs font-semibold text-gray-600 mb-1">
                  Hasta
                </label>
                <input
                  value={fechaVenciHasta}
                  onChange={(e) => setFechaVenciHasta(e.target.value)}
                  type="date"
                  className="w-full px-3 py-2 bg-white border-2 border-gray-200 rounded-lg focus:outline-none focus:border-red-600 focus:ring-2 focus:ring-red-100 transition-all text-xs text-gray-900"
                />
              </div>
            </div>
          </div>

          {/* Botón Consultar */}
          <div className="flex justify-center lg:self-center">
            <button
              onClick={() => consultar(searchTerm, searchTermVendedor, fechaEmisionDesde, fechaEmisionHasta, fechaVenciDesde, fechaVenciHasta)}
              className="px-6 md:px-8 py-2.5 md:py-3 bg-red-600 text-white font-bold text-sm md:text-base rounded-lg md:rounded-xl hover:bg-red-700 transition-colors shadow-sm hover:shadow-lg border border-red-700 whitespace-nowrap"
            >
              Consultar
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

export default SearchBar
