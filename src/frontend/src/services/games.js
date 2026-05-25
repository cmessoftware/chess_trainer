import apiService from './api'
import { logger } from '../utils/helpers'

class GamesService {
    constructor() {
        this.baseUrl = '/chess/games'
    }

    /**
     * Obtener lista de partidas con paginación
     */
    async getGamesList(params = {}) {
        try {
            const {
                limit = 50,
                offset = 0,
                source = null,
                search = null
            } = params

            const searchParams = new URLSearchParams()
            searchParams.append('limit', limit.toString())
            searchParams.append('offset', offset.toString())
            if (source) searchParams.append('source', source)
            if (search) searchParams.append('search', search)

            logger.info('gamesService', 'Obteniendo lista de partidas', params)

            const finalUrl = `${this.baseUrl}?${searchParams.toString()}`
            console.log('🌐 URL de partidas:', finalUrl)

            const response = await apiService.get(finalUrl)
            console.log('🎯 Respuesta API cruda games:', response)
            console.log('🎯 Respuesta.data games:', response.data)

            return {
                success: true,
                data: response.data
            }
        } catch (error) {
            logger.error('gamesService', 'Error obteniendo lista de partidas', error)
            return {
                success: false,
                message: error.message || 'Error obteniendo lista de partidas'
            }
        }
    }

    /**
     * Obtener fuentes de partidas disponibles
     */
    async getGameSources() {
        try {
            logger.info('gamesService', 'Obteniendo fuentes de partidas')

            const sourcesUrl = `/chess/games/sources`
            console.log('🌐 URL de fuentes:', sourcesUrl)

            const response = await apiService.get(sourcesUrl)
            console.log('🎯 Respuesta API cruda sources:', response)
            console.log('🎯 Respuesta.data sources:', response.data)

            return {
                success: true,
                data: response.data?.sources || response.data || []
            }
        } catch (error) {
            logger.error('gamesService', 'Error obteniendo fuentes', error)
            return {
                success: false,
                message: error.message || 'Error obteniendo fuentes'
            }
        }
    }

    /**
     * Obtener una partida específica por ID
     */
    async getGame(gameId) {
        try {
            logger.info('gamesService', 'Obteniendo partida', { gameId })

            const response = await apiService.get(`${this.baseUrl}/${gameId}`)
            console.log('🎯 Respuesta API cruda game:', response)
            console.log('🎯 Respuesta.data game:', response.data)

            return {
                success: true,
                data: response.data
            }
        } catch (error) {
            logger.error('gamesService', 'Error obteniendo partida', error)
            return {
                success: false,
                message: error.response?.data?.detail || error.message || 'Error al obtener partida'
            }
        }
    }

    /**
     * Obtener movimientos de una partida
     */
    async getGameMoves(gameId) {
        try {
            logger.info('gamesService', 'Obteniendo movimientos de partida', { gameId })

            const response = await apiService.get(`${this.baseUrl}/${gameId}/moves`)

            return {
                success: true,
                data: response.moves || []
            }
        } catch (error) {
            logger.error('gamesService', 'Error obteniendo movimientos', error)
            return {
                success: false,
                message: error.response?.data?.detail || error.message || 'Error al obtener movimientos'
            }
        }
    }

    /**
     * Buscar partidas (funcionalidad simplificada)
     */
    async searchGames(query, page = 1, pageSize = 25) {
        try {
            logger.info('gamesService', 'Búsqueda de partidas', { query, page, pageSize })

            // Por ahora usa getGamesList
            return await this.getGamesList({
                limit: pageSize,
                offset: (page - 1) * pageSize
            })
        } catch (error) {
            logger.error('gamesService', 'Error en búsqueda', error)
            return {
                success: false,
                message: error.message || 'Error en búsqueda'
            }
        }
    }
}

// Instancia singleton
const gamesService = new GamesService()
export { gamesService }
export default gamesService