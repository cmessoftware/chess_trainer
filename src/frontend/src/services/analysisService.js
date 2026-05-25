import axios from 'axios'

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

class AnalysisService {
    /**
     * Analizar una posición de ajedrez
     */
    async analyzePosition(fen, depth = 10) {
        try {
            const response = await axios.post(
                `${API_BASE}/chess/position-analysis`,
                {
                    fen: fen,
                    depth: depth
                }
            )

            return response.data
        } catch (error) {
            console.error('Error analyzing position:', error)
            throw error
        }
    }

    /**
     * Validar un movimiento
     */
    async validateMove(move) {
        try {
            const response = await axios.post(
                `${API_BASE}/chess/validate-move`,
                {
                    move: move
                }
            )

            return response.data
        } catch (error) {
            console.error('Error validating move:', error)
            throw error
        }
    }

    /**
     * Obtener análisis de una partida completa
     */
    async analyzeGame(gameId) {
        try {
            const response = await axios.post(
                `${API_BASE}/chess/analyze-game`,
                {
                    gameId: gameId
                }
            )

            return response.data
        } catch (error) {
            console.error('Error analyzing game:', error)
            throw error
        }
    }

    /**
     * Obtener evaluación rápida de posición
     */
    async getQuickEvaluation(fen) {
        try {
            // Análisis rápido con profundidad baja
            const analysis = await this.analyzePosition(fen, 5)
            return {
                evaluation: analysis.evaluation,
                bestMove: analysis.best_move,
                isQuick: true
            }
        } catch (error) {
            console.error('Error getting quick evaluation:', error)
            return {
                evaluation: null,
                bestMove: null,
                error: error.message
            }
        }
    }
}

export const analysisService = new AnalysisService()
export default analysisService