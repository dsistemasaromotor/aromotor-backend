import axios from "axios";
import { API_BASE_URL } from "./constants";
import Cookie from "js-cookie"


const apiInstance = axios.create({
    baseURL: API_BASE_URL,
    timeout: 10000,
    headers: {
        'Content-Type': "application/json",
        Accept: "application/json",
    },
})

apiInstance.interceptors.request.use(
    (config) => {

        if (config.url.includes('/set-password')) {
            return config;
        }
        
        const token = Cookie.get("access_token"); // ⬅️ lo lees de la cookie
        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
    },
    (error) => Promise.reject(error)
);

export default apiInstance