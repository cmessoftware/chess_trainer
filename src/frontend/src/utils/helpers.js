// Utilidades para logging progresivo según el roadmap
export const logger = {
    // Niveles de logging
    levels: {
        DEBUG: 'debug',
        INFO: 'info',
        WARN: 'warn',
        ERROR: 'error'
    },

    // Log con contexto de funcionalidad
    log(level, feature, message, data = null) {
        const timestamp = new Date().toISOString()
        const logEntry = {
            timestamp,
            level,
            feature,
            message,
            data
        }

        // En desarrollo, mostrar en consola
        if (import.meta.env.DEV) {
            console.log(`[${timestamp}] ${level.toUpperCase()} - ${feature}: ${message}`, data || '')
        }

        // En producción, enviar al backend o servicio de logs
        if (import.meta.env.PROD) {
            this.sendToBackend(logEntry)
        }
    },

    // Métodos de conveniencia
    debug(feature, message, data) {
        this.log(this.levels.DEBUG, feature, message, data)
    },

    info(feature, message, data) {
        this.log(this.levels.INFO, feature, message, data)
    },

    warn(feature, message, data) {
        this.log(this.levels.WARN, feature, message, data)
    },

    error(feature, message, error) {
        this.log(this.levels.ERROR, feature, message, {
            message: error?.message,
            stack: error?.stack,
            name: error?.name
        })
    },

    // Enviar logs al backend (implementar cuando sea necesario)
    async sendToBackend(logEntry) {
        try {
            // TODO: Implementar endpoint de logs en FastAPI
            // await api.post('/logs', logEntry)
        } catch (error) {
            console.error('Error enviando log al backend:', error)
        }
    }
}

// Utilidad para formatear fechas
export const formatDate = (date) => {
    return new Intl.DateTimeFormat('es-ES', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
    }).format(new Date(date))
}

// Utilidad para debounce
export const debounce = (func, wait) => {
    let timeout
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout)
            func(...args)
        }
        clearTimeout(timeout)
        timeout = setTimeout(later, wait)
    }
}

// Utilidad para manejar errores de forma consistente
export const handleError = (error, feature) => {
    logger.error(feature, 'Error capturado', error)

    // Determinar mensaje de usuario amigable
    if (error.response?.status === 401) {
        return 'Tu sesión ha expirado. Por favor inicia sesión nuevamente.'
    } else if (error.response?.status === 403) {
        return 'No tienes permisos para realizar esta acción.'
    } else if (error.response?.status === 404) {
        return 'El recurso solicitado no fue encontrado.'
    } else if (error.response?.status >= 500) {
        return 'Error interno del servidor. Intenta nuevamente más tarde.'
    } else {
        return error.message || 'Ha ocurrido un error inesperado.'
    }
}