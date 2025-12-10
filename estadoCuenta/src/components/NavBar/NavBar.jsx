import { useEffect, useState, useRef} from "react"
import Cookie from "js-cookie"
import {jwtDecode} from 'jwt-decode'
import { logout } from "../../utils/auth";
import { useNavigate } from "react-router-dom";

const decodeToken = (token) => {
  try {
    return jwtDecode(token);
  } catch (error) {
    console.error("Error decoding JWT:", error);
    return null;
  }
};


const NavBar = () =>{

    const [fullName, setFullName] =  useState("");
    const [isDropdownOpen, setIsDropdownOpen] = useState(false);
    const navigate = useNavigate();
    const dropdownRef = useRef(null);

    useEffect(() => {

        const getUsername = () => {
            const accessToken = Cookie.get("access_token");

            if (!accessToken) {
                console.error("No se encontró el token de acceso");
                return;
            }

            const user = decodeToken(accessToken);
            if(user?.full_name){
                setFullName(user.full_name);
            }else{
                console.warn("full_name no se encontró en el token")
            }
        };

        getUsername();
    }, []);


    useEffect(() => {
        if (isDropdownOpen) {
            const handleClickOutside = (event) => {
                if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
                    setIsDropdownOpen(false);
                }
            };
            document.addEventListener('mousedown', handleClickOutside);
            return () => {
                document.removeEventListener('mousedown', handleClickOutside);
            };
        }
    }, [isDropdownOpen]);

    
    return (
        <nav className="sticky top-0 z-50 bg-white border-b border-gray-200 shadow-sm">
            <div className="max-full mx-auto px-6 h-16 flex items-center justify-between">
                <div className="flex items-center gap-4">
                    <button className="w-10 h-10 bg-gray-100 hover:bg-gray-200 rounded-lg flex items-center justify-center transition-colors duration-200"
                        onClick={() => {
                            navigate("/estadoCuenta/home");
                        }}
                    >
                        <svg className="w-5 h-5 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z" />
                        </svg>
                    </button>
                    <div className="w-10 h-10 bg-gradient-to-br from-red-600 to-red-700 rounded-lg flex items-center justify-center">
                        <span className="text-white font-bold text-lg italic">A</span>
                    </div>
                    <div>
                        <h1 className="text-xl font-bold text-gray-900">Estados de Cuenta</h1>
                        <p className="text-xs text-gray-500">Impor Export Aromotor Cia Ltda</p>
                    </div>
                </div>

                <div className="relative">
                    <button 
                        className="text-right flex items-center gap-2"
                        onClick={() => setIsDropdownOpen(!isDropdownOpen)}
                    >
                        <p className="text-sm font-medium text-gray-900">{fullName}</p>
                        <svg className="w-4 h-4 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                        </svg>
                    </button>
                    {isDropdownOpen && (
                        <div ref={dropdownRef} className="absolute right-0 mt-2 w-48 bg-white border-sm border-gray-200 rounded-lg shadow-lg z-10">
                            <div className="py-1 px-1">
                                {/* Aquí puedes añadir más opciones si lo deseas, por ejemplo: */}
                                {/* <button className="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100">
                                    Perfil
                                </button> */}
                                <button
                                    className="block w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-red-50 hover:text-red-700 rounded-md transition-colors duration-200 flex items-center gap-2 font-medium border border-gray-100"
                                    onClick={() => {
                                        logout();
                                        navigate("/estadoCuenta/login");
                                        setIsDropdownOpen(false);
                                    }}
                                    >
                                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
                                    </svg>
                                    Cerrar Sesión
                                </button>
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </nav>
    )
}

export default NavBar
