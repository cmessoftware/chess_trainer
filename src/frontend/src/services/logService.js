import api from './api.js'

class LogService {
    /**
     * Registrar un evento del tablero de ajedrez
     */
    async logChessEvent(action, data = {}) {
        try {
            const response = await api.post(
                '/logs/test/chess', // Usando endpoint de testing por ahora
                {
                    module: 'chess',
                    action: action,
                    data: {
                        ...data,
                        timestamp: new Date().toISOString(),
                        url: window.location.pathname
                    }
                }
            )

            return response.data
        } catch (error) {
            console.error('Error logging chess event:', error)
            // No lanzar error para que no bloquee la funcionalidad principal
            return null
        }
    }

    /**
     * Registrar movimiento en el tablero
     */
    async logBoardMove(move, pgn, fen) {
        return this.logChessEvent('board_move', {
            move,
            pgn,
            fen,
            moveIndex: pgn ? pgn.split(' ').length : 0
        })
    }

    /**
     * Registrar carga de partida
     */
    async logGameLoad(gameId, gameData) {
        return this.logChessEvent('game_load', {
            gameId,
            white: gameData?.white,
            black: gameData?.black,
            movesCount: gameData?.moves?.length || 0
        })
    }

    /**
     * Registrar análisis de posición
     */
    async logPositionAnalysis(fen, depth, result) {
        return this.logChessEvent('position_analysis', {
            fen,
            depth,
            bestMove: result?.best_move,
            evaluation: result?.evaluation
        })
    }

    /**
     * Registrar navegación por jugadas
     */
    async logMoveNavigation(direction, currentMove, totalMoves) {
        return this.logChessEvent('move_navigation', {
            direction, // 'previous', 'next', 'start', 'end'
            currentMove,
            totalMoves
        })
    }

    /**
     * Registrar click en casilla
     */
    async logSquareClick(square, piece, fen) {
        return this.logChessEvent('square_click', {
            square,
            piece,
            fen
        })
    }

    /**
     * Obtener logs de chess (solo admin)
     */
    async getChessLogs(limit = 50, offset = 0, action = null) {
        try {
            const params = new URLSearchParams({ limit, offset })
            if (action) params.append('action', action)

            const response = await api.get(
                `/logs/test/chess?${params.toString()}`
            )

            return response.data
        } catch (error) {
            console.error('Error getting chess logs:', error)
            throw error
        }
    }

    /**
     * Registrar un evento de importación de PGN
     */
    async logImportEvent(action, data = {}) {
        try {
            const response = await api.post(
                '/logs/test/import', // Endpoint para logs de importación
                {
                    module: 'import',
                    action: action,
                    data: {
                        ...data,
                        timestamp: new Date().toISOString(),
                        url: window.location.pathname
                    }
                }
            )

            return response.data
        } catch (error) {
            console.error('Error logging import event:', error)
            return null
        }
    }

    /**
     * Obtener logs de importación (solo admin)
     */
    async getImportLogs(limit = 50, offset = 0, action = null) {
        try {
            const params = new URLSearchParams({ limit, offset })
            if (action) params.append('action', action)

            const response = await api.get(
                `/logs/test/import?${params.toString()}`
            )

            return response.data
        } catch (error) {
            console.error('Error getting import logs:', error)
            throw error
        }
    }
}

export const logService = new LogService()
export default logService