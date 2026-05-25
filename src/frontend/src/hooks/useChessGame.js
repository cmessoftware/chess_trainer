import { useState, useCallback, useMemo } from 'react'
import { Chess } from 'chess.js'
import { gamesService } from '../services/games.js'
import { logger } from '../utils/helpers.js'

export const useChessGame = () => {
    const [game, setGame] = useState(new Chess())
    const [gameHistory, setGameHistory] = useState([])
    const [currentMoveIndex, setCurrentMoveIndex] = useState(-1)
    const [loading, setLoading] = useState(false)
    const [gameData, setGameData] = useState(null)
    const [gameVersion, setGameVersion] = useState(0) // Para forzar re-renders
    const [currentFen, setCurrentFen] = useState(new Chess().fen()) // Estado separado para FEN

    // Cargar una partida desde el backend
    const loadGame = useCallback(async (gameId) => {
        try {
            setLoading(true)
            logger.info('chess', 'Cargando partida', { gameId })

            const response = await gamesService.getGame(gameId)
            if (!response.success) {
                throw new Error(response.message)
            }

            const data = response.data
            const newGame = new Chess()
            const sanHistory = [] // Historial en notación SAN
            const uciHistory = [] // Historial original UCI

            // Cargar los movimientos en el motor de ajedrez y generar SAN
            if (data.moves && data.moves.length > 0) {
                data.moves.forEach(move => {
                    try {
                        // Convertir UCI a SAN antes de hacer el movimiento
                        const sanMove = newGame.move(move)
                        if (sanMove) {
                            sanHistory.push(sanMove.san)
                            uciHistory.push(move)
                        }
                    } catch (moveError) {
                        logger.warn('chess', 'Movimiento inválido ignorado', { move, moveError })
                    }
                })
            }

            // Resetear al inicio para navegación
            const finalGame = new Chess()

            setGame(finalGame)
            setGameData({ ...data, sanMoves: sanHistory, uciMoves: uciHistory })
            setGameHistory(uciHistory) // Mantener UCI para el motor
            setCurrentMoveIndex(-1) // Empezar al inicio
            setCurrentFen(finalGame.fen()) // Actualizar FEN explícitamente
            setGameVersion(prev => prev + 1) // Forzar re-render

            logger.info('chess', 'Partida cargada exitosamente', {
                gameId,
                movesCount: sanHistory.length,
                sanMoves: sanHistory.slice(0, 5),
                uciMoves: uciHistory.slice(0, 5)
            })

            return data
        } catch (error) {
            logger.error('chess', 'Error cargando partida', error)
            throw error
        } finally {
            setLoading(false)
        }
    }, [])

    // Navegar a un movimiento específico
    const goToMove = useCallback((moveIndex) => {
        try {
            logger.info('chess', 'Navegando a movimiento', {
                moveIndex,
                totalMoves: gameHistory.length,
                currentIndex: currentMoveIndex
            })

            // Crear una nueva instancia del juego
            const newGame = new Chess()

            // Aplicar movimientos hasta el índice deseado
            if (moveIndex >= 0 && gameHistory.length > 0) {
                for (let i = 0; i <= moveIndex && i < gameHistory.length; i++) {
                    const moveResult = newGame.move(gameHistory[i])
                    if (!moveResult) {
                        logger.warn('chess', 'Error aplicando movimiento', { move: gameHistory[i], index: i })
                        break
                    }
                }
            }

            const newFen = newGame.fen()

            // Actualizar estados con nuevo FEN y versión
            setGame(newGame)
            setCurrentMoveIndex(moveIndex)
            setCurrentFen(newFen)
            setGameVersion(prev => prev + 1)

            logger.info('chess', 'Navegación completada', {
                moveIndex,
                oldFen: currentFen?.substring(0, 30),
                newFen: newFen.substring(0, 30),
                totalMoves: gameHistory.length,
                currentMove: moveIndex >= 0 ? gameHistory[moveIndex] : 'posición inicial'
            })

            // Pequeño delay para asegurar que React procese el cambio de estado
            setTimeout(() => {
                logger.debug('chess', 'Post-navegación check', {
                    moveIndex,
                    fen: newFen.substring(0, 30),
                    gameVersionChanged: true
                })
            }, 10)

        } catch (error) {
            logger.error('chess', 'Error navegando a movimiento', error)
        }
    }, [gameHistory, currentMoveIndex, currentFen])

    // Movimiento anterior
    const previousMove = useCallback(() => {
        if (currentMoveIndex > -1) {
            goToMove(currentMoveIndex - 1)
        }
    }, [currentMoveIndex, goToMove])

    // Siguiente movimiento  
    const nextMove = useCallback(() => {
        if (currentMoveIndex < gameHistory.length - 1) {
            goToMove(currentMoveIndex + 1)
        }
    }, [currentMoveIndex, gameHistory.length, goToMove])

    // Ir al inicio
    const goToStart = useCallback(() => {
        goToMove(-1)
    }, [goToMove])

    // Ir al final
    const goToEnd = useCallback(() => {
        if (gameHistory.length > 0) {
            goToMove(gameHistory.length - 1)
        }
    }, [gameHistory.length, goToMove])

    // Hacer un movimiento (para análisis interactivo)
    const makeMove = useCallback((moveStr) => {
        try {
            const newGame = new Chess(game.fen())
            const move = newGame.move(moveStr)

            if (move) {
                setGame(newGame)
                setCurrentFen(newGame.fen()) // Actualizar FEN explícitamente
                setGameVersion(prev => prev + 1) // Forzar re-render
                logger.debug('chess', 'Movimiento realizado', { move: moveStr, fen: newGame.fen() })
                return move
            } else {
                logger.warn('chess', 'Movimiento inválido', { move: moveStr })
                return null
            }
        } catch (error) {
            logger.error('chess', 'Error realizando movimiento', error)
            return null
        }
    }, [game])

    // Resetear el juego
    const resetGame = useCallback(() => {
        const newGame = new Chess()
        setGame(newGame)
        setGameHistory([])
        setCurrentMoveIndex(-1)
        setGameData(null)
        setCurrentFen(newGame.fen()) // Actualizar FEN explícitamente
        setGameVersion(prev => prev + 1) // Forzar re-render
        logger.info('chess', 'Juego reseteado')
    }, [])

    // Calcular propiedades reactivas usando gameVersion para forzar actualización
    const fen = currentFen // Usar el estado separado directamente
    const isGameOver = useMemo(() => game.isGameOver(), [game, gameVersion])
    const isCheck = useMemo(() => game.isCheck(), [game, gameVersion])
    const isCheckmate = useMemo(() => game.isCheckmate(), [game, gameVersion])
    const isDraw = useMemo(() => game.isDraw(), [game, gameVersion])
    const turn = useMemo(() => game.turn(), [game, gameVersion])

    return {
        game,
        gameHistory,
        currentMoveIndex,
        loading,
        gameData,
        loadGame,
        goToMove,
        previousMove,
        nextMove,
        goToStart,
        goToEnd,
        makeMove,
        resetGame,
        gameVersion, // Añadir para forzar re-renders
        // Propiedades útiles del juego (reactivas)
        isGameOver,
        isCheck,
        isCheckmate,
        isDraw,
        turn,
        fen
    }
}