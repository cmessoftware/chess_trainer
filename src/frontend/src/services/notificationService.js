import axios from 'axios'
import { logger } from '../utils/helpers.js'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

/**
 * Servicio para gestionar notificaciones del sistema
 */
export const notificationService = {
    /**
     * Obtener todas las notificaciones del usuario
     */
    async getNotifications(unreadOnly = false, limit = 20) {
        try {
            const endpoint = unreadOnly
                ? `${API_BASE_URL}/api/features/notifications/unread`
                : `${API_BASE_URL}/api/features/notifications`

            const response = await axios.get(endpoint, {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`
                }
            })
            // El backend devuelve directamente un array
            return Array.isArray(response.data) ? response.data : []
        } catch (error) {
            logger.error('notificationService', 'Error obteniendo notificaciones', { error })
            // Retornar array vacío en caso de error para evitar crashes
            return []
        }
    },

    /**
     * Obtener notificaciones no leídas
     */
    async getUnreadNotifications() {
        try {
            return await this.getNotifications(true)
        } catch (error) {
            logger.error('notificationService', 'Error obteniendo notificaciones no leídas', { error })
            throw error
        }
    },

    /**
     * Obtener conteo de notificaciones no leídas
     */
    async getUnreadCount() {
        try {
            const response = await axios.get(`${API_BASE_URL}/api/features/notifications/unread`, {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`
                }
            })
            // El backend devuelve un array, contamos cuántos elementos tiene
            return Array.isArray(response.data) ? response.data.length : 0
        } catch (error) {
            logger.error('notificationService', 'Error obteniendo conteo no leídas', { error })
            return 0
        }
    },

    /**
     * Marcar notificación como leída
     */
    async markAsRead(notificationId) {
        try {
            const response = await axios.put(
                `${API_BASE_URL}/api/features/notifications/${notificationId}/read`,
                {},
                {
                    headers: {
                        'Authorization': `Bearer ${localStorage.getItem('token')}`
                    }
                }
            )
            return response.data
        } catch (error) {
            logger.error('notificationService', 'Error marcando notificación como leída', { error })
            throw error
        }
    },

    /**
     * Marcar todas las notificaciones como leídas
     */
    async markAllAsRead() {
        try {
            const response = await axios.put(
                `${API_BASE_URL}/api/features/notifications/read-all`,
                {},
                {
                    headers: {
                        'Authorization': `Bearer ${localStorage.getItem('token')}`
                    }
                }
            )
            return response.data
        } catch (error) {
            logger.error('notificationService', 'Error marcando todas como leídas', { error })
            throw error
        }
    },

    /**
     * Eliminar una notificación
     */
    async deleteNotification(notificationId) {
        try {
            const response = await axios.delete(
                `${API_BASE_URL}/api/features/notifications/${notificationId}`,
                {
                    headers: {
                        'Authorization': `Bearer ${localStorage.getItem('token')}`
                    }
                }
            )
            return response.data
        } catch (error) {
            logger.error('notificationService', 'Error eliminando notificación', { error })
            throw error
        }
    },

    /**
     * Crear notificación (uso interno)
     */
    async createNotification(title, message, type = 'info', metadata = {}) {
        try {
            logger.warn('notificationService', 'createNotification no implementado en backend - las notificaciones se crean automáticamente durante procesos')
            // Las notificaciones se crean automáticamente en el backend durante procesos
            // Este método queda como stub para compatibilidad
            return { success: false, message: 'Use proceso de features para generar notificaciones' }
        } catch (error) {
            logger.error('notificationService', 'Error creando notificación', { error })
            throw error
        }
    },

    /**
     * Mostrar notificación del sistema (interfaz simplificada)
     */
    async showNotification(title, message, type = 'info', duration = 5000) {
        try {
            // Crear notificación en el backend
            const result = await this.createNotification(title, message, type);

            // Mostrar notificación del navegador si está soportado
            if ('Notification' in window && Notification.permission === 'granted') {
                new Notification(title, {
                    body: message,
                    icon: '/favicon.ico',
                    badge: '/favicon.ico'
                });
            }

            // Disparar evento personalizado para componentes que escuchan
            window.dispatchEvent(new CustomEvent('notification', {
                detail: { title, message, type, duration }
            }));

            return result;
        } catch (error) {
            logger.error('notificationService', 'Error mostrando notificación', { error });

            // Fallback: al menos disparar evento
            window.dispatchEvent(new CustomEvent('notification', {
                detail: { title, message, type: 'error', duration }
            }));

            throw error;
        }
    },

    /**
     * Suscribirse a notificaciones en tiempo real (WebSocket)
     * Implementación futura con WebSocket
     */
    subscribeToNotifications(callback) {
        // TODO: Implementar WebSocket para notificaciones en tiempo real
        logger.info('notificationService', 'Suscripción a notificaciones (WebSocket pendiente)')

        // Por ahora usar polling
        const interval = setInterval(async () => {
            try {
                const unread = await this.getUnreadNotifications()
                if (unread.length > 0) {
                    callback(unread)
                }
            } catch (error) {
                logger.error('notificationService', 'Error en polling de notificaciones', { error })
            }
        }, 15000) // Cada 15 segundos

        return () => clearInterval(interval)
    }
}

export default notificationService
