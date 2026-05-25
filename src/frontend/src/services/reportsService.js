import axios from 'axios';
import { logService } from './logService';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

class ReportsService {
    constructor() {
        this.baseURL = `${API_BASE_URL}/api/reports`;

        // Configurar interceptor para logs
        axios.interceptors.request.use((config) => {
            if (config.url?.includes('/api/reports')) {
                logService.log('info', `Reports API Request: ${config.method?.toUpperCase()} ${config.url}`, {
                    data: config.data,
                    params: config.params
                });
            }
            return config;
        });

        axios.interceptors.response.use(
            (response) => {
                if (response.config.url?.includes('/api/reports')) {
                    logService.log('info', `Reports API Response: ${response.status}`, {
                        url: response.config.url,
                        data: response.data
                    });
                }
                return response;
            },
            (error) => {
                if (error.config?.url?.includes('/api/reports')) {
                    logService.log('error', `Reports API Error: ${error.message}`, {
                        url: error.config.url,
                        status: error.response?.status,
                        data: error.response?.data
                    });
                }
                return Promise.reject(error);
            }
        );
    }

    /**
     * Generar reporte para jugador existente en BD
     * @param {Object} options - Opciones del reporte
     * @param {string} options.playerName - Nombre del jugador
     * @param {number} options.minGames - Mínimo de partidas
     * @param {boolean} options.includeSurvivorship - Incluir análisis survivorship
     * @param {boolean} options.includeStreakAnalysis - Incluir análisis de rachas de errores
     * @param {boolean} options.includePgnGames - Incluir PGNs de partidas con rachas
     * @param {boolean} options.generatePdf - Generar PDF automáticamente
     * @param {string} options.outputFormat - Formato de salida (markdown, pdf)
     * @returns {Promise<Object>} Job ID y información del proceso
     */
    async generateExistingPlayerReport(options) {
        try {
            const response = await axios.post(`${this.baseURL}/generate`, {
                player_name: options.playerName,
                min_games: options.minGames || 50,
                include_survivorship: options.includeSurvivorship !== false,
                include_streak_analysis: options.includeStreakAnalysis !== false,
                include_pgn_games: options.includePgnGames !== false,
                generate_pdf: options.generatePdf !== false,
                output_format: options.outputFormat || 'markdown'
            });

            return {
                success: true,
                data: response.data
            };
        } catch (error) {
            return {
                success: false,
                error: error.response?.data?.detail || error.message,
                status: error.response?.status
            };
        }
    }

    /**
     * Generar reporte desde archivos PGN subidos
     * @param {Object} options - Opciones del reporte
     * @param {string} options.playerName - Nombre del jugador
     * @param {Array<string>} options.pgnFiles - Rutas de archivos PGN
     * @param {string} options.source - Fuente de los archivos
     * @param {number} options.minGames - Mínimo de partidas
     * @param {boolean} options.includeSurvivorship - Incluir análisis survivorship
     * @param {boolean} options.includeStreakAnalysis - Incluir análisis de rachas
     * @param {boolean} options.includePgnGames - Incluir PGNs de partidas
     * @param {boolean} options.generatePdf - Generar PDF automáticamente
     * @returns {Promise<Object>} Job ID y información del proceso
     */
    async generateUploadedPlayerReport(options) {
        try {
            const response = await axios.post(`${this.baseURL}/generate-from-upload`, {
                player_name: options.playerName,
                pgn_files: options.pgnFiles,
                source: options.source || 'uploaded',
                min_games: options.minGames || 20,
                include_survivorship: options.includeSurvivorship !== false,
                include_streak_analysis: options.includeStreakAnalysis !== false,
                include_pgn_games: options.includePgnGames !== false,
                generate_pdf: options.generatePdf !== false
            });

            return {
                success: true,
                data: response.data
            };
        } catch (error) {
            return {
                success: false,
                error: error.response?.data?.detail || error.message,
                status: error.response?.status
            };
        }
    }

    /**
     * Obtener estado de un job de reporte
     * @param {string} jobId - ID del job
     * @returns {Promise<Object>} Estado del job
     */
    async getJobStatus(jobId) {
        try {
            const response = await axios.get(`${this.baseURL}/status/${jobId}`);
            return {
                success: true,
                data: response.data
            };
        } catch (error) {
            return {
                success: false,
                error: error.response?.data?.detail || error.message,
                status: error.response?.status
            };
        }
    }

    /**
     * Descargar reporte generado
     * @param {string} jobId - ID del job
     * @returns {Promise<Blob>} Archivo del reporte
     */
    async downloadReport(jobId) {
        try {
            const response = await axios.get(`${this.baseURL}/download/${jobId}`, {
                responseType: 'blob'
            });

            return {
                success: true,
                blob: response.data,
                filename: this.extractFilename(response.headers['content-disposition']) || 'reporte.md'
            };
        } catch (error) {
            return {
                success: false,
                error: error.response?.data?.detail || error.message,
                status: error.response?.status
            };
        }
    }

    /**
     * Obtener lista de reportes recientes
     * @returns {Promise<Object>} Lista de reportes
     */
    async getRecentReports() {
        try {
            const response = await axios.get(`${this.baseURL}/list`);
            return {
                success: true,
                data: response.data
            };
        } catch (error) {
            return {
                success: false,
                error: error.response?.data?.detail || error.message,
                status: error.response?.status
            };
        }
    }

    /**
     * Polling automático del estado de un job
     * @param {string} jobId - ID del job
     * @param {Function} onUpdate - Callback para actualizaciones
     * @param {Function} onComplete - Callback cuando se completa
     * @param {Function} onError - Callback para errores
     * @param {number} intervalMs - Intervalo de polling en ms
     * @returns {Function} Función para cancelar el polling
     */
    startJobPolling(jobId, onUpdate, onComplete, onError, intervalMs = 3000) {
        let isActive = true;

        const poll = async () => {
            if (!isActive) return;

            const result = await this.getJobStatus(jobId);

            if (result.success) {
                const status = result.data;

                if (onUpdate) {
                    onUpdate(status);
                }

                if (status.status === 'completed') {
                    isActive = false;
                    if (onComplete) {
                        onComplete(status);
                    }
                } else if (status.status === 'failed') {
                    isActive = false;
                    if (onError) {
                        onError(status.error_message || 'Job failed');
                    }
                } else {
                    // Continuar polling
                    setTimeout(poll, intervalMs);
                }
            } else {
                isActive = false;
                if (onError) {
                    onError(result.error);
                }
            }
        };

        // Iniciar polling
        poll();

        // Retornar función de cancelación
        return () => {
            isActive = false;
        };
    }

    /**
     * Verificar si un jugador existe en la BD
     * @param {string} playerName - Nombre del jugador
     * @returns {Promise<Object>} Información del jugador
     */
    async verifyPlayerExists(playerName) {
        try {
            // Usar endpoint general de chess para verificar
            const response = await axios.get(`${API_BASE_URL}/chess/player/${playerName}/stats`);

            return {
                success: true,
                exists: true,
                data: response.data
            };
        } catch (error) {
            if (error.response?.status === 404) {
                return {
                    success: true,
                    exists: false
                };
            }

            return {
                success: false,
                error: error.message,
                exists: false
            };
        }
    }

    /**
     * Obtener progreso estimado basado en número de partidas
     * @param {number} gamesCount - Número de partidas
     * @returns {Object} Tiempo estimado y configuración de progreso
     */
    getProgressEstimate(gamesCount) {
        let estimatedMinutes;
        let progressSteps;

        if (gamesCount < 100) {
            estimatedMinutes = 1;
            progressSteps = ['Verificando datos', 'Análisis básico', 'Survivorship bias', 'Finalizando'];
        } else if (gamesCount < 1000) {
            estimatedMinutes = 3;
            progressSteps = ['Verificando datos', 'Extrayendo features', 'Análisis táctico', 'Survivorship bias', 'Generando reporte'];
        } else if (gamesCount < 3000) {
            estimatedMinutes = 8;
            progressSteps = ['Verificando datos', 'Procesando partidas', 'Extrayendo features', 'Análisis táctico', 'Survivorship bias', 'ML analysis', 'Generando reporte'];
        } else {
            estimatedMinutes = 15;
            progressSteps = ['Verificando datos', 'Procesando lote 1', 'Procesando lote 2', 'Extrayendo features', 'Análisis táctico avanzado', 'Survivorship bias', 'ML analysis', 'Patrones avanzados', 'Generando reporte'];
        }

        return {
            estimatedMinutes,
            progressSteps,
            stepDuration: Math.floor((estimatedMinutes * 60 * 1000) / progressSteps.length)
        };
    }

    /**
     * Extraer filename del header Content-Disposition
     * @param {string} contentDisposition - Header Content-Disposition
     * @returns {string|null} Nombre del archivo
     */
    extractFilename(contentDisposition) {
        if (!contentDisposition) return null;

        const matches = /filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/.exec(contentDisposition);
        if (matches != null && matches[1]) {
            return matches[1].replace(/['"]/g, '');
        }

        return null;
    }

    /**
     * Formatear tamaño de archivo
     * @param {number} bytes - Tamaño en bytes
     * @returns {string} Tamaño formateado
     */
    formatFileSize(bytes) {
        if (bytes === 0) return '0 B';

        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));

        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    /**
     * Validar nombre de jugador
     * @param {string} playerName - Nombre del jugador
     * @returns {Object} Resultado de validación
     */
    validatePlayerName(playerName) {
        if (!playerName || !playerName.trim()) {
            return {
                valid: false,
                error: 'El nombre del jugador es requerido'
            };
        }

        const name = playerName.trim();

        if (name.length < 2) {
            return {
                valid: false,
                error: 'El nombre debe tener al menos 2 caracteres'
            };
        }

        if (name.length > 50) {
            return {
                valid: false,
                error: 'El nombre no puede tener más de 50 caracteres'
            };
        }

        // Permitir letras, números, guiones y guiones bajos
        const validPattern = /^[a-zA-Z0-9_-]+$/;
        if (!validPattern.test(name)) {
            return {
                valid: false,
                error: 'El nombre solo puede contener letras, números, guiones y guiones bajos'
            };
        }

        return {
            valid: true,
            clean: name
        };
    }

    /**
     * Validar archivos PGN
     * @param {FileList|Array} files - Archivos a validar
     * @returns {Object} Resultado de validación
     */
    validatePGNFiles(files) {
        const fileArray = Array.from(files);

        if (fileArray.length === 0) {
            return {
                valid: false,
                error: 'Selecciona al menos un archivo PGN'
            };
        }

        if (fileArray.length > 10) {
            return {
                valid: false,
                error: 'Máximo 10 archivos por upload'
            };
        }

        const maxSize = 50 * 1024 * 1024; // 50MB por archivo
        const totalMaxSize = 200 * 1024 * 1024; // 200MB total
        let totalSize = 0;

        for (const file of fileArray) {
            if (!file.name.toLowerCase().endsWith('.pgn')) {
                return {
                    valid: false,
                    error: `${file.name} no es un archivo PGN válido`
                };
            }

            if (file.size > maxSize) {
                return {
                    valid: false,
                    error: `${file.name} es demasiado grande (máximo 50MB por archivo)`
                };
            }

            totalSize += file.size;
        }

        if (totalSize > totalMaxSize) {
            return {
                valid: false,
                error: 'El tamaño total de archivos excede 200MB'
            };
        }

        return {
            valid: true,
            files: fileArray,
            totalSize
        };
    }

    /**
     * Descargar reporte en formato PDF
     * @param {string} jobId - ID del job
     * @returns {Promise<void>} Descarga directa del archivo
     */
    async downloadPdfReport(jobId) {
        try {
            const response = await axios.get(`${this.baseURL}/download/${jobId}/pdf`, {
                responseType: 'blob'
            });

            // Crear link de descarga
            const blob = new Blob([response.data], { type: 'application/pdf' });
            const url = window.URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = url;
            link.download = `reporte_${jobId}.pdf`;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            window.URL.revokeObjectURL(url);

            return { success: true };
        } catch (error) {
            return {
                success: false,
                error: error.response?.data?.detail || error.message
            };
        }
    }

    /**
     * Descargar análisis detallado de rachas
     * @param {string} jobId - ID del job
     * @returns {Promise<void>} Descarga directa del archivo
     */
    async downloadStreakAnalysis(jobId) {
        try {
            const response = await axios.get(`${this.baseURL}/download/${jobId}/streak-analysis`, {
                responseType: 'blob'
            });

            const blob = new Blob([response.data], { type: 'text/markdown' });
            const url = window.URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = url;
            link.download = `analisis_rachas_${jobId}.md`;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            window.URL.revokeObjectURL(url);

            return { success: true };
        } catch (error) {
            return {
                success: false,
                error: error.response?.data?.detail || error.message
            };
        }
    }

    /**
     * Descargar PGNs de partidas con rachas
     * @param {string} jobId - ID del job
     * @returns {Promise<void>} Descarga directa del archivo
     */
    async downloadPgnGames(jobId) {
        try {
            const response = await axios.get(`${this.baseURL}/download/${jobId}/pgn-games`, {
                responseType: 'blob'
            });

            const blob = new Blob([response.data], { type: 'text/markdown' });
            const url = window.URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = url;
            link.download = `partidas_rachas_${jobId}.md`;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            window.URL.revokeObjectURL(url);

            return { success: true };
        } catch (error) {
            return {
                success: false,
                error: error.response?.data?.detail || error.message
            };
        }
    }

    /**
     * Obtener resumen de análisis de un job completado
     * @param {string} jobId - ID del job
     * @returns {Promise<Object>} Resumen del análisis
     */
    async getAnalysisSummary(jobId) {
        try {
            const statusResult = await this.getJobStatus(jobId);
            if (statusResult.success && statusResult.data.status === 'completed') {
                return {
                    success: true,
                    summary: statusResult.data.analysis_summary || {}
                };
            }

            return {
                success: false,
                error: 'Job no completado o no encontrado'
            };
        } catch (error) {
            return {
                success: false,
                error: error.message
            };
        }
    }
}

// Crear instancia singleton
export const reportsService = new ReportsService();
export default reportsService;