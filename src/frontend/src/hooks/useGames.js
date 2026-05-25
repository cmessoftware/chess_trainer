import { useState, useEffect } from 'react'
import { gamesService } from '../services/games'
import { logger } from '../utils/helpers'

export const useGames = (options = {}) => {
    const { page = 1, pageSize = 25, searchTerm = '' } = options

    const [games, setGames] = useState([])
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState('')
    const [totalCount, setTotalCount] = useState(0)

    const searchGames = async (term = '', pageNum = 1, pageSize = 25) => {
        try {
            setLoading(true)
            setError('')

            logger.info('useGames', 'Buscando partidas', {
                searchTerm: term,
                page: pageNum,
                pageSize
            })

            const response = await gamesService.searchGames({
                search: term,
                page: pageNum,
                page_size: pageSize
            })

            if (response.success) {
                setGames(response.data.games || [])
                setTotalCount(response.data.total || 0)

                logger.info('useGames', 'Partidas cargadas exitosamente', {
                    count: response.data.games?.length,
                    total: response.data.total
                })
            } else {
                throw new Error(response.message || 'Error desconocido')
            }
        } catch (err) {
            logger.error('useGames', 'Error buscando partidas', err)
            setError(err.message || 'Error al cargar partidas')
            setGames([])
            setTotalCount(0)
        } finally {
            setLoading(false)
        }
    }

    const getGame = async (gameId) => {
        try {
            setLoading(true)
            setError('')

            logger.info('useGames', 'Obteniendo partida', { gameId })

            const response = await gamesService.getGame(gameId)

            if (response.success) {
                logger.info('useGames', 'Partida obtenida exitosamente', { gameId })
                return response.data
            } else {
                throw new Error(response.message || 'Error desconocido')
            }
        } catch (err) {
            logger.error('useGames', 'Error obteniendo partida', err)
            setError(err.message || 'Error al obtener partida')
            throw err
        } finally {
            setLoading(false)
        }
    }

    const refetch = () => {
        searchGames(searchTerm, page, pageSize)
    }

    // Auto-fetch on mount and dependencies change
    useEffect(() => {
        if (page && pageSize) {
            searchGames(searchTerm, page, pageSize)
        }
    }, []) // Solo en mount inicial

    return {
        games,
        loading,
        error,
        totalCount,
        searchGames,
        getGame,
        refetch
    }
}