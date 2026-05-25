import api from './api.js'

// Servicio para interactuar con el tablero de ajedrez
export const chessService = {
    // Cargar una partida específica
    async loadGame(gameId) {
        try {
            const response = await api.get(`/chess/games/${gameId}`)
            return response.data
        } catch (error) {
            throw new Error(`Error cargando partida: ${error.response?.data?.message || error.message}`)
        }
    },

    // Obtener movimientos de una partida
    async getGameMoves(gameId) {
        try {
            const response = await api.get(`/chess/games/${gameId}/moves`)
            return response.data
        } catch (error) {
            throw new Error(`Error obteniendo movimientos: ${error.response?.data?.message || error.message}`)
        }
    },

    // Analizar una posición
    async analyzePosition(fen, depth = 10) {
        try {
            const response = await api.post('/chess/analyze', { fen, depth })
            return response.data
        } catch (error) {
            throw new Error(`Error en análisis: ${error.response?.data?.message || error.message}`)
        }
    },

    // Validar un movimiento
    async validateMove(gameId, move) {
        try {
            const response = await api.post(`/chess/games/${gameId}/validate-move`, { move })
            return response.data
        } catch (error) {
            throw new Error(`Movimiento inválido: ${error.response?.data?.message || error.message}`)
        }
    }
}

export default chessService