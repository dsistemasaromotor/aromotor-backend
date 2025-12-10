import { useAuth } from "../auth";
import axios from "./axios";
import {jwtDecode} from 'jwt-decode'
import Cookie from "js-cookie";



export const login = async (email, password) => {
    try {
        const { data, status } = await axios.post(`user/token/`, {
          email,
          password,
        });
    
        if (status === 200) {
            console.log(data)
            setAuthUser(data.access, data.refresh);
        }
    
        return { data, error: null };
    } catch (error) {
        return {
          data: null,
          error: error.response.data?.detail || "Something went wrong",
        };
    }


};

export const logout = () => {
    Cookie.remove("access_token");
    Cookie.remove("refresh_token");
    useAuth.getState().setUser(null);
}

export const setUser = async () => {
    const access_token = Cookie.get("access_token")
    const refresh_token = Cookie.get("refresh_token")

    if(!access_token || !refresh_token) {
        // alert("Token no existe")
        return;
    }

    if(isAccessTokenExpired(access_token)){
        // const response = getRefreshedToken(refresh_token)
        // setAuthUser(response.access, response.refresh)
        try { 
            const response = await getRefreshedToken(); // Ahora se llama sin parámetros ✅
            setAuthUser(response.access, response.refresh);
        } catch (error) { 
            console.error("Error al refrescar el token:", error); 
            logout();  // Si falla, cierra sesión 
        }
    }else{
        setAuthUser(access_token, refresh_token)
    }
}

export const setAuthUser = (access_token, refresh_token) => {
    Cookie.set("access_token", access_token, {
        expires: 1,
        secure: true,
    })

    Cookie.set("refresh_token", refresh_token, {
        expires: 7,
        secure: true,
    })

    const user = jwtDecode(access_token) ?? null

    if(user){
        useAuth.getState().setUser(user)
    }
    
    useAuth.getState().setLoading(false)    
}

export const getRefreshedToken = async () => {
    const refresh_token = Cookie.get("refresh_token");
    const response = await axios.post(`user/token/refresh/`, {
        refresh: refresh_token,
    });
    return response.data;
}

export const isAccessTokenExpired = (access_token) => {
    try{
        const decodedToken = jwtDecode(access_token)
        return decodedToken.exp < Date.now() / 1000

    }catch(error){
        console.log(error);
        return true
    }
}