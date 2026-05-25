import axios from 'axios'

// Base URL de la API
const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

console.log('🌐 API Base URL:', BASE_URL, 'VITE_API_URL:', import.meta.env.VITE_API_URL)

// Cliente HTTP base
const api = axios.create({
    baseURL: BASE_URL,
    headers: {
        'Content-Type': 'application/json'
    }
})

// Interceptor para agregar JWT token automáticamente
api.interceptors.request.use(
    (config) => {
        const token = localStorage.getItem('token')
        if (token) {
            config.headers.Authorization = `Bearer ${token}`
        }
        return config
    },
    (error) => Promise.reject(error)
)

// Interceptor para manejar errores de autenticación
api.interceptors.response.use(
    (response) => response,
    (error) => {
        if (error.response?.status === 401) {
            // Token expirado o inválido
            localStorage.removeItem('token')
            localStorage.removeItem('user')
            window.location.href = '/login'
        }
        return Promise.reject(error)
    }
)

export default api