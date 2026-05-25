import api from './api.js'
import { logService } from './logService.js'

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

class ImportService {
    /**
     * Subir un archivo PGN al servidor
     * @param {FormData} formData - Datos del archivo
     * @param {Function} onProgress - Callback para progreso de upload
     * @returns {Promise<string>} - Job ID del upload
     */
    async uploadPGN(formData, onProgress) {
        try {
            const response = await api.post(
                `/api/upload/pgn`,
                formData,
                {
                    headers: {
                        'Content-Type': 'multipart/form-data',
                    },
                    onUploadProgress: (progressEvent) => {
                        if (onProgress && progressEvent.total) {
                            const percentCompleted = Math.round(
                                (progressEvent.loaded * 100) / progressEvent.total
                            )
                            onProgress(percentCompleted)
                        }
                    },
                }
            )

            // Log del upload exitoso (DISABLED - endpoint doesn't exist)
            // await logService.logImportEvent('file_upload_completed', {
            //     jobId: response.data.job_id,
            //     filename: formData.get('file')?.name,
            //     size: formData.get('file')?.size
            // })

            return response.data.job_id
        } catch (error) {
            console.error('Error uploading PGN file:', error)

            // Log del error (DISABLED - endpoint doesn't exist)
            // await logService.logImportEvent('file_upload_failed', {
            //     error: error.message,
            //     filename: formData.get('file')?.name
            // })

            throw error
        }
    }

    /**
     * Obtener el estado de un job de upload
     * @param {string} jobId - ID del job
     * @returns {Promise<Object>} - Estado del job
     */
    async getUploadStatus(jobId) {
        try {
            const response = await api.get(`/api/upload/status/${jobId}`)
            return response.data
        } catch (error) {
            console.error('Error getting upload status:', error)
            throw error
        }
    }

    /**
     * Iniciar importación masiva usando el script paralelo
     * @param {Array} fileIds - IDs de archivos a importar
     * @param {string} source - Fuente de datos (personal, elite, etc.)
     * @returns {Promise<Object>} - Información del job de importación
     */
    async startBatchImport(fileIds, source = 'personal') {
        try {
            const response = await api.post(`/api/import/pgn/batch`, {
                fileIds,
                source,
                useParallelScript: true // Indica que use import_pgns_parallel.py
            })

            // Log del inicio de importación
            await logService.logImportEvent('batch_import_started', {
                jobId: response.data.jobId,
                fileCount: fileIds.length,
                source
            })

            return response.data
        } catch (error) {
            console.error('Error starting batch import:', error)

            await logService.logImportEvent('batch_import_failed', {
                error: error.message,
                fileIds,
                source
            })

            throw error
        }
    }

    /**
     * Importación personal simple para usuarios básicos
     * Sube e importa el PGN directamente marcando al usuario
     * @param {FormData} formData - Datos del archivo
     * @param {Function} onProgress - Callback para progreso de upload
     * @returns {Promise<Object>} - Resultado de la importación
     */
    async importPersonalPGN(formData, onProgress) {
        try {
            const response = await api.post(
                `/api/import/pgn/personal`,
                formData,
                {
                    headers: {
                        'Content-Type': 'multipart/form-data',
                    },
                    onUploadProgress: (progressEvent) => {
                        if (onProgress && progressEvent.total) {
                            const percentCompleted = Math.round(
                                (progressEvent.loaded * 100) / progressEvent.total
                            )
                            onProgress(percentCompleted)
                        }
                    },
                }
            )

            // Log disabled - endpoint doesn't exist
            // await logService.logImportEvent('personal_import_completed', {
            //     filename: formData.get('file')?.name,
            //     imported: response.data.imported,
            //     skipped: response.data.skipped
            // })

            return response.data
        } catch (error) {
            console.error('Error importing personal PGN:', error)

            // Log disabled - endpoint doesn't exist
            // await logService.logImportEvent('personal_import_failed', {
            //     error: error.message,
            //     filename: formData.get('file')?.name
            // })

            throw error
        }
    }

    /**
     * Obtener preview de partidas de un archivo
     * @param {string} jobId - ID del archivo subido
     * @param {number} limit - Número máximo de partidas para preview
     * @returns {Promise<Array>} - Lista de partidas para preview
     */
    async getPreview(jobId, limit = 10) {
        try {
            const response = await api.get(
                `/api/import/preview/${jobId}?limit=${limit}`
            )
            return response.data.games
        } catch (error) {
            console.error('Error getting preview:', error)
            throw error
        }
    }

    /**
     * Obtener historial de importaciones
     * @param {number} page - Página
     * @param {number} limit - Límite de resultados
     * @returns {Promise<Object>} - Historial paginado
     */
    async getImportHistory(page = 1, limit = 20) {
        try {
            const response = await api.get(
                `/api/import/history?page=${page}&limit=${limit}`
            )
            return response.data
        } catch (error) {
            console.error('Error getting import history:', error)
            throw error
        }
    }

    /**
     * Cancelar un job de importación
     * @param {string} jobId - ID del job
     * @returns {Promise<boolean>} - True si se canceló exitosamente
     */
    async cancelImportJob(jobId) {
        try {
            const response = await api.post(`/api/import/cancel/${jobId}`)

            await logService.logImportEvent('import_job_cancelled', {
                jobId
            })

            return response.data.success
        } catch (error) {
            console.error('Error canceling import job:', error)
            throw error
        }
    }

    /**
     * Obtener estadísticas de importación
     * @returns {Promise<Object>} - Estadísticas generales
     */
    async getImportStats() {
        try {
            const response = await api.get(`/api/import/stats`)
            return response.data
        } catch (error) {
            console.error('Error getting import stats:', error)
            throw error
        }
    }

    /**
     * Validar archivo PGN antes de subir
     * @param {File} file - Archivo a validar
     * @returns {Promise<Object>} - Resultado de validación
     */
    async validatePGNFile(file) {
        try {
            const formData = new FormData()
            formData.append('file', file)

            const response = await api.post(
                `/api/import/validate`,
                formData,
                {
                    headers: {
                        'Content-Type': 'multipart/form-data',
                    }
                }
            )

            return {
                isValid: response.data.valid,
                gameCount: response.data.gameCount,
                errors: response.data.errors || [],
                warnings: response.data.warnings || []
            }
        } catch (error) {
            console.error('Error validating PGN file:', error)
            return {
                isValid: false,
                gameCount: 0,
                errors: [error.message],
                warnings: []
            }
        }
    }
}

// Crear instancia singleton
export const importService = new ImportService()
export default importService