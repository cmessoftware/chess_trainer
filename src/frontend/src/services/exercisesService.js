/**
 * Servicio para manejar ejercicios personalizados
 * Integración con API de análisis ML y generación de ejercicios
 */

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

class ExercisesService {
    /**
     * Analizar un jugador y generar ejercicios personalizados
     * @param {Object} analysisRequest - Datos del análisis
     * @param {string} analysisRequest.player_name - Nombre del jugador
     * @param {string} analysisRequest.pgn_content - Contenido PGN opcional
     * @param {Array<string>} analysisRequest.analysis_type - Tipos de análisis
     * @returns {Promise<Object>} Resultado del análisis con ejercicios
     */
    async analyzePlayer(analysisRequest) {
        try {
            const response = await fetch(`${API_BASE_URL}/api/exercises/analyze-player`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },
                body: JSON.stringify(analysisRequest)
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('Error analyzing player:', error);
            throw new Error(`Error en análisis: ${error.message}`);
        }
    }

    /**
     * Subir archivo PGN para análisis
     * @param {string} playerName - Nombre del jugador
     * @param {File} pgnFile - Archivo PGN
     * @returns {Promise<Object>} Resultado de la importación
     */
    async uploadPGN(playerName, pgnFile) {
        try {
            const formData = new FormData();
            formData.append('file', pgnFile);

            const response = await fetch(`${API_BASE_URL}/api/exercises/upload-pgn?player_name=${encodeURIComponent(playerName)}`, {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('Error uploading PGN:', error);
            throw new Error(`Error subiendo PGN: ${error.message}`);
        }
    }

    /**
     * Obtener patrones tácticos disponibles
     * @returns {Promise<Object>} Patrones organizados por categoría
     */
    async getTacticalPatterns() {
        try {
            const response = await fetch(`${API_BASE_URL}/api/exercises/patterns`);

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('Error fetching patterns:', error);
            throw new Error(`Error obteniendo patrones: ${error.message}`);
        }
    }

    /**
     * Exportar ejercicios como estudio de Lichess
     * @param {string} playerName - Nombre del jugador
     * @returns {Promise<Object>} Datos de exportación con PGN
     */
    async exportToLichess(playerName) {
        try {
            const response = await fetch(`${API_BASE_URL}/api/exercises/export-lichess/${encodeURIComponent(playerName)}`);

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('Error exporting to Lichess:', error);
            throw new Error(`Error exportando: ${error.message}`);
        }
    }

    /**
     * Crear ejercicio personalizado manualmente
     * @param {Object} exerciseData - Datos del ejercicio
     * @returns {Promise<Object>} Ejercicio creado
     */
    async createExercise(exerciseData) {
        try {
            const response = await fetch(`${API_BASE_URL}/api/exercises/create`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(exerciseData)
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('Error creating exercise:', error);
            throw new Error(`Error creando ejercicio: ${error.message}`);
        }
    }

    /**
     * Obtener ejercicios existentes de un jugador
     * @param {string} playerName - Nombre del jugador
     * @returns {Promise<Array>} Lista de ejercicios
     */
    async getPlayerExercises(playerName) {
        try {
            const response = await fetch(`${API_BASE_URL}/api/exercises/player/${encodeURIComponent(playerName)}`);

            if (response.status === 404) {
                return []; // No hay ejercicios, devolver array vacío
            }

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('Error fetching player exercises:', error);
            return []; // En caso de error, devolver array vacío
        }
    }

    /**
     * Validar archivo PGN antes de procesarlo
     * @param {string} pgnContent - Contenido del PGN
     * @returns {Object} Resultado de la validación
     */
    validatePGN(pgnContent) {
        const validation = {
            isValid: false,
            gameCount: 0,
            errors: [],
            warnings: []
        };

        try {
            // Verificaciones básicas
            if (!pgnContent || pgnContent.trim().length === 0) {
                validation.errors.push('El archivo PGN está vacío');
                return validation;
            }

            // Contar juegos (buscar encabezados [Event])
            const gameMatches = pgnContent.match(/\[Event\s+"[^"]+"\]/g);
            validation.gameCount = gameMatches ? gameMatches.length : 0;

            if (validation.gameCount === 0) {
                validation.errors.push('No se encontraron partidas válidas en el PGN');
                return validation;
            }

            // Verificar formato básico
            if (!pgnContent.includes('[White ') && !pgnContent.includes('[Black ')) {
                validation.warnings.push('No se encontraron etiquetas de jugadores estándar');
            }

            // Buscar movimientos
            const movePattern = /\d+\.\s*\w+/;
            if (!movePattern.test(pgnContent)) {
                validation.warnings.push('No se detectaron movimientos en formato estándar');
            }

            validation.isValid = validation.errors.length === 0;

        } catch (error) {
            validation.errors.push(`Error validando PGN: ${error.message}`);
        }

        return validation;
    }

    /**
     * Generar reporte de análisis para descarga
     * @param {Object} analysisResult - Resultados del análisis
     * @param {string} playerName - Nombre del jugador
     * @returns {string} Contenido del reporte en formato Markdown
     */
    generateAnalysisReport(analysisResult, playerName) {
        const now = new Date().toLocaleString();

        let report = `# Reporte de Análisis Personalizado: ${playerName}\n\n`;
        report += `**Fecha de análisis:** ${now}\n`;
        report += `**Movimientos analizados:** ${analysisResult.analysis_summary.total_moves.toLocaleString()}\n\n`;

        // Resumen de rendimiento
        report += `## 📊 Resumen de Rendimiento\n\n`;
        report += `- **Movimientos buenos:** ${(analysisResult.analysis_summary.good_rate * 100).toFixed(1)}%\n`;
        report += `- **Tasa de errores:** ${(analysisResult.analysis_summary.error_rate * 100).toFixed(1)}%\n`;
        report += `- **Máxima racha de errores:** ${analysisResult.analysis_summary.max_error_streak}\n`;
        report += `- **Precisión del modelo:** ${(analysisResult.analysis_summary.model_accuracy * 100).toFixed(0)}%\n\n`;

        // Ejercicios recomendados
        report += `## 🎯 Ejercicios Recomendados (${analysisResult.recommended_exercises.length})\n\n`;

        analysisResult.recommended_exercises.forEach((exercise, index) => {
            report += `### ${index + 1}. ${exercise.title}\n`;
            report += `**Dificultad:** ${exercise.difficulty} | **Tipo:** ${exercise.pattern_type}\n\n`;
            report += `${exercise.description}\n\n`;
            report += `**Explicación:** ${exercise.explanation}\n\n`;

            if (exercise.target_moves.length > 0) {
                report += `**Movimientos objetivo:** ${exercise.target_moves.join(', ')}\n\n`;
            }

            if (exercise.lichess_study_url) {
                report += `**Enlace de práctica:** ${exercise.lichess_study_url}\n\n`;
            }

            report += `---\n\n`;
        });

        // Plan de estudio
        report += `## 📅 Plan de Estudio Sugerido\n\n`;
        report += `### Horario Diario:\n`;
        report += `- **Táctica:** ${analysisResult.study_plan.daily_schedule.tactics_time} minutos\n`;
        report += `- **Análisis:** ${analysisResult.study_plan.daily_schedule.analysis_time} minutos\n`;
        report += `- **Práctica de patrones:** ${analysisResult.study_plan.daily_schedule.pattern_practice} minutos\n\n`;

        report += `### Metas Semanales:\n`;
        analysisResult.study_plan.weekly_goals.forEach((goal, index) => {
            report += `${index + 1}. ${goal}\n`;
        });

        report += `\n### Áreas Prioritarias:\n`;
        analysisResult.priority_areas.forEach(area => {
            report += `- ${area.replace('_', ' ').toUpperCase()}\n`;
        });

        report += `\n---\n*Reporte generado automáticamente por Chess Trainer ML System*`;

        return report;
    }

    /**
     * Descargar archivo como texto
     * @param {string} content - Contenido del archivo
     * @param {string} filename - Nombre del archivo
     * @param {string} type - Tipo MIME del archivo
     */
    downloadFile(content, filename, type = 'text/plain') {
        const blob = new Blob([content], { type });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }
}

// Crear instancia singleton del servicio
export const exercisesService = new ExercisesService();

// Exportación por defecto para compatibilidad
export default exercisesService;