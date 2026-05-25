import axios from 'axios'
import { logger } from '../utils/helpers.js'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

/**
 * Servicio para gestionar extracción de features
 */
export const featuresService = {
    /**
     * Iniciar extracción de features
     * @param {string} batchId - ID del batch a procesar (requerido si no se provee sinceMinutes)
     * @param {string} source - Fuente opcional (personal, elite, etc.)
     * @param {number} sinceMinutes - Procesar solo últimos N minutos
     * @param {number} maxGames - Máximo de partidas a procesar
     * @param {number} workers - Número de workers paralelos
     */
    async startFeatureExtraction(batchId = null, source = null, sinceMinutes = null, maxGames = 1000, workers = 4) {
        try {
            const payload = {
                max_games: maxGames,
                workers
            }

            // Agregar filtros opcionales
            if (batchId) payload.batch_id = batchId
            if (source) payload.source = source
            if (sinceMinutes) payload.since_minutes = sinceMinutes

            const response = await axios.post(
                `${API_BASE_URL}/api/features/extract`,
                payload,
                {
                    headers: {
                        'Authorization': `Bearer ${localStorage.getItem('token')}`
                    }
                }
            )
            logger.info('featuresService', 'Extracción de features iniciada', response.data)
            return response.data
        } catch (error) {
            logger.error('featuresService', 'Error iniciando extracción', { error })
            throw error
        }
    },

    /**
     * Obtener estado de un job de extracción
     */
    async getExtractionStatus(jobId) {
        try {
            const response = await axios.get(
                `${API_BASE_URL}/api/features/status/${jobId}`,
                {
                    headers: {
                        'Authorization': `Bearer ${localStorage.getItem('token')}`
                    }
                }
            )
            return response.data
        } catch (error) {
            logger.error('featuresService', 'Error obteniendo estado', { error })
            throw error
        }
    },

    /**
     * Listar todos los jobs de extracción
     */
    async listExtractionJobs() {
        try {
            const response = await axios.get(
                `${API_BASE_URL}/api/features/jobs`,
                {
                    headers: {
                        'Authorization': `Bearer ${localStorage.getItem('token')}`
                    }
                }
            )
            return response.data
        } catch (error) {
            logger.error('featuresService', 'Error listando jobs', { error })
            throw error
        }
    }
}

export default featuresService
