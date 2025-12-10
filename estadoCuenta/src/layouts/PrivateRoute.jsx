import {Navigate} from 'react-router-dom'
import { useAuth } from '../auth'

const PrivateRoute = ({children}) => {
    const loggedIn = useAuth((state) => state.isLoggedIn)();

    return loggedIn ? <>{children}</> : <Navigate to="/estadoCuenta/login" replace/> ;
}

export default PrivateRoute;