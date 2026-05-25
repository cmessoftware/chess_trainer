import api from './api.js'

// Tipos de usuario según el roadmap
export const USER_ROLES = {
    ADMIN: 'admin',
    ANALISTA: 'analista',
    USUARIO: 'usuario'
}

// Servicio de autenticación
export const authService = {
    // Login
    async login(username, password) {
        try {
            const response = await api.post('/auth/login', { username, password })
            const { access_token, user } = response.data

            // Guardar token y usuario en localStorage
            localStorage.setItem('token', access_token)
            localStorage.setItem('user', JSON.stringify(user))

            return { token: access_token, user }
        } catch (error) {
            throw new Error(error.response?.data?.message || 'Error en el login')
        }
    },

    // Logout
    logout() {
        localStorage.removeItem('token')
        localStorage.removeItem('user')
    },

    // Verificar si está autenticado
    isAuthenticated() {
        return !!localStorage.getItem('token')
    },

    // Obtener usuario actual
    getCurrentUser() {
        const userStr = localStorage.getItem('user')
        return userStr ? JSON.parse(userStr) : null
    },

    // Verificar rol
    hasRole(role) {
        const user = this.getCurrentUser()
        return user?.role === role
    },

    // Verificar permisos para una funcionalidad
    hasPermission(feature) {
        const user = this.getCurrentUser()
        if (!user) return false

        // Matriz de permisos según el roadmap
        const permissions = {
            [USER_ROLES.ADMIN]: ['chess_board', 'games_browser', 'analysis', 'import', 'ml_pipeline', 'admin'],
            [USER_ROLES.ANALISTA]: ['chess_board', 'games_browser', 'analysis', 'ml_pipeline'],
            [USER_ROLES.USUARIO]: ['chess_board', 'games_browser']
        }

        return permissions[user.role]?.includes(feature) || false
    }
}

export default authService