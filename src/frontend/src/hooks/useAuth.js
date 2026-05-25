import { useState, useEffect } from 'react'
import { logger } from '../utils/helpers.js'
import { API_ENDPOINTS } from '../config/api.js'

// Base roles mapping (mantener para referencia)
const BASE_ROLES = {
    ADMIN: 'admin',
    BASIC_GAMER: 'basic_gamer',
    ANALYSIS_BOARD: 'analysis_board',
    EXERCISE_CREATOR: 'exercise_creator',
    STATS_VIEWER: 'stats_viewer',
    TACTICS_TRAINER: 'tactics_trainer',
    PGN_UPLOADER: 'pgn_uploader',
    EDA_ANALYST: 'eda_analyst'
};

const ROLE_PERMISSIONS = {
    admin: ['ALL'],
    basic_gamer: ['chess_board', 'play_stockfish', 'view_own_games', 'import_pgn', 'personal_upload', 'generate_features'],
    analysis_board: ['chess_board', 'analysis_engine', 'deep_analysis'],
    exercise_creator: ['create_exercises', 'edit_exercises', 'view_exercises'],
    stats_viewer: ['view_stats', 'advanced_stats', 'reports'],
    tactics_trainer: ['tactics_training', 'view_exercises', 'progress_tracking'],
    pgn_uploader: ['bulk_upload', 'import_pgn', 'manage_sources'],
    eda_analyst: ['eda_analysis', 'data_mining', 'pattern_analysis']
};

// Calculate permissions from roles
const calculatePermissions = (roles) => {
    const permissions = new Set();

    for (const role of roles) {
        const rolePerms = ROLE_PERMISSIONS[role] || [];
        if (rolePerms.includes('ALL')) {
            // Admin has all permissions
            Object.values(ROLE_PERMISSIONS).flat().forEach(perm => {
                if (perm !== 'ALL') permissions.add(perm);
            });
            break;
        }
        rolePerms.forEach(perm => permissions.add(perm));
    }

    return Array.from(permissions);
};

export const useAuth = () => {
    const [user, setUser] = useState(null)
    const [loading, setLoading] = useState(true) // Iniciar como true durante la carga inicial
    const [isAuthenticated, setIsAuthenticated] = useState(false) // false por defecto hasta verificar token
    const [token, setToken] = useState(localStorage.getItem('token'))

    useEffect(() => {
        // Verify token on app load
        const initializeAuth = async () => {
            setLoading(true); // Establecer loading al inicio
            const storedToken = localStorage.getItem('token');

            if (storedToken) {
                try {
                    // Verify token with backend
                    const response = await fetch(API_ENDPOINTS.AUTH_VERIFY, {
                        method: 'POST',
                        headers: {
                            'Authorization': `Bearer ${storedToken}`,
                            'Content-Type': 'application/json'
                        }
                    });

                    if (response.ok) {
                        const data = await response.json();
                        const userData = data.user;
                        const permissions = data.permissions || [];

                        // Build user with backend permissions
                        const userWithPermissions = {
                            ...userData,
                            permissions: permissions
                        };

                        setUser(userWithPermissions);
                        setToken(storedToken);
                        setIsAuthenticated(true);
                        setLoading(false); // Finalizar carga
                        logger.info('auth', 'Usuario verificado desde token almacenado', { user: userWithPermissions });
                        return;
                    } else {
                        // Token invalid, remove it
                        localStorage.removeItem('token');
                        setToken(null);
                    }
                } catch (error) {
                    logger.error('auth', 'Error verificando token almacenado', error);
                    localStorage.removeItem('token');
                    setToken(null);
                }
            }

            // No hay token válido, usuario no autenticado
            setUser(null);
            setIsAuthenticated(false);
            setLoading(false);
            logger.info('auth', 'No hay sesión activa');
        };

        initializeAuth();
    }, [])

    const login = async (username, password) => {
        try {
            setLoading(true);

            // Real authentication with backend
            const response = await fetch(API_ENDPOINTS.AUTH_LOGIN, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    username: username,
                    password: password
                })
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || 'Credenciales inválidas');
            }

            const data = await response.json();
            const { access_token, user: userData } = data;

            // Calculate permissions
            const calculatedPermissions = calculatePermissions(userData.roles || []);
            // Ensure admin users get ALL permission for route access
            const isAdmin = userData.roles && userData.roles.includes('admin');
            const userWithPermissions = {
                ...userData,
                permissions: isAdmin ? ['ALL', ...calculatedPermissions] : calculatedPermissions
            };

            // Store token and user data
            localStorage.setItem('token', access_token);

            // ⚠️ CRÍTICO: Establecer loading a false PRIMERO para evitar race conditions
            setLoading(false);

            // Luego actualizar el resto del estado
            setToken(access_token);
            setUser(userWithPermissions);
            setIsAuthenticated(true);

            logger.info('auth', 'Login exitoso', { user: userWithPermissions });
            console.log('✅ Login successful, loading set to false', { user: userWithPermissions.username, loading: false });
            return { success: true, user: userWithPermissions };

        } catch (error) {
            logger.error('auth', 'Error en login', error);
            setIsAuthenticated(false);
            setLoading(false); // Asegurar que loading se establezca a false en error también
            console.log('❌ Login failed, loading set to false');
            return { success: false, error: error.message };
        }
    }

    const logout = async () => {
        try {
            if (token) {
                // Try to logout on backend
                await fetch(API_ENDPOINTS.AUTH_LOGOUT, {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${token}`,
                    }
                });
            }
        } catch (error) {
            logger.error('auth', 'Error en logout', error);
        } finally {
            // Clear local state
            localStorage.removeItem('token');
            setToken(null);
            setUser(null);
            setIsAuthenticated(false);
            logger.info('auth', 'Logout realizado');
        }
    }

    const hasRole = (role) => {
        if (user?.role === role) return true; // Legacy compatibility
        return user?.roles?.includes(role) || false; // New system
    }

    const hasAnyRole = (roles) => {
        if (!Array.isArray(roles)) return hasRole(roles);
        return roles.some(role => hasRole(role));
    }

    const hasPermissionForRoute = (route) => {
        // Mapeo de rutas a permisos requeridos
        const routePermissions = {
            '/games': ['view_own_games', 'view_all_games', 'chess_board'],
            '/import': ['personal_analysis', 'bulk_upload', 'import_pgn'],
            '/reports': ['own_reports', 'view_stats', 'reports'],
            '/chess-board': ['chess_board'],
            '/admin/roles': ['ALL'] // Admin only
        };

        const requiredPerms = routePermissions[route];
        if (!requiredPerms) return true; // Ruta sin restricciones

        return requiredPerms.some(perm => hasPermission(perm));
    }

    const hasPermission = (permission) => {
        if (user?.permissions?.includes('ALL') || user?.permissions?.includes(permission)) {
            return true;
        }

        // Legacy compatibility
        if (user?.role === 'admin') return true;

        return user?.permissions?.includes(permission) || false;
    }

    // New methods for combinatorial role system
    const getUserRoles = () => {
        return user?.roles || [];
    }

    const getUserPermissions = () => {
        return user?.permissions || [];
    }

    const hasAllRoles = (roles) => {
        const userRoles = getUserRoles();
        return roles.every(role => userRoles.includes(role));
    }

    const hasAllPermissions = (permissions) => {
        const userPermissions = getUserPermissions();
        return permissions.every(perm => userPermissions.includes(perm));
    }

    return {
        user,
        token,
        loading,
        isAuthenticated,
        login,
        logout,
        hasRole,
        hasAnyRole,
        hasPermission,
        hasPermissionForRoute,
        getUserRoles,
        getUserPermissions,
        hasAllRoles,
        hasAllPermissions,
        // Legacy methods for backward compatibility
        hasAccessToImport: () => hasPermissionForRoute('/import'),
        hasAccessToGames: () => hasPermissionForRoute('/games'),
        hasAccessToReports: () => hasPermissionForRoute('/reports')
    }
}