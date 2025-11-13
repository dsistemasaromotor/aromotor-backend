import { Search} from "lucide-react"
import { useSearch } from "../../hooks/useSearch"

const SearchBar = ({ consultar }) => {

    const { searchTerm, setSearchTerm } = useSearch()

    return(
        <div className="mb-8">
          <div className="flex gap-4">
            <div className="relative flex-1">
              <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
              <input
                type="text"
                placeholder="Buscar por cliente..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-12 pr-4 py-3 bg-white border-2 border-gray-200 rounded-xl focus:outline-none focus:border-red-600 focus:ring-2 focus:ring-red-100 transition-all text-gray-900 placeholder-gray-400 shadow-sm"
              />
            </div>
            <button
              onClick={() => consultar(searchTerm)}
              className="px-8 py-3 bg-red-600 text-white font-bold rounded-xl hover:bg-red-700 transition-colors shadow-sm hover:shadow-lg border border-red-700"
            >
              Consultar
            </button>
          </div>
        </div>
    )
}

export default SearchBar