import React, { useState, useEffect, useCallback } from 'react'
import SimpleChessBoard from './SimpleChessBoard'
import MovesList from './MovesList'
import {
    Box,
    Paper,
    Typography,
    Button,
    ButtonGroup,
    Card,
    CardContent,
    LinearProgress,
    Alert,
    Chip,
    IconButton,
    Tooltip,
    Switch,
    FormControlLabel
} from '@mui/material'
import {
    SkipPrevious,
    NavigateBefore,
    NavigateNext,
    SkipNext,
    Replay,
    Analytics,
    Info,
    SportsEsports,
    Visibility
} from '@mui/icons-material'
import { useChessGame } from '../../hooks/useChessGame.js'
import { logger } from '../../utils/helpers.js'
import { logService } from '../../services/logService.js'
import { analysisService } from '../../services/analysisService.js'
import { Chess } from 'chess.js'
import { startNewStockfishGame, tryPlayerMove, checkGameStatus, makeStockfishMove } from './StockfishGameLogic.js'

const STOCKFISH_LEVELS = {
    beginner: { name: 'Principiante', depth: 1, elo: '~800' },
    easy: { name: 'Fácil', depth: 3, elo: '~1000' },
    medium: { name: 'Intermedio', depth: 5, elo: '~1400' },
    hard: { name: 'Difícil', depth: 8, elo: '~1800' },
    expert: { name: 'Experto', depth: 12, elo: '~2200' }
}

const ChessBoard = ({ gameId = null, showAnalysis = false, initialMode = 'view' }) => {
    const {
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
        resetGame,
        isGameOver,
        isCheck,
        turn,
        gameVersion, // Para forzar re-renders del tablero
        fen
    } = useChessGame()

    const [error, setError] = useState('')
    const [analysisEnabled, setAnalysisEnabled] = useState(showAnalysis)
    const [currentAnalysis, setCurrentAnalysis] = useState(null)
    const [analyzingPosition, setAnalyzingPosition] = useState(false)
    const [selectedSquare, setSelectedSquare] = useState(null)
    const [squareInfo, setSquareInfo] = useState(null)

    // Estados para modo de juego contra Stockfish
    const [boardMode, setBoardMode] = useState(initialMode) // 'view' o 'play'
    const [playGame, setPlayGame] = useState(null) // Instancia de Chess.js para jugar
    const [playerColor, setPlayerColor] = useState('white')
    const [difficulty, setDifficulty] = useState('easy')
    const [gameStatus, setGameStatus] = useState('setup') // 'setup', 'playing', 'finished'
    const [playMoveHistory, setPlayMoveHistory] = useState([])
    const [thinking, setThinking] = useState(false)
    const [lastPlayMove, setLastPlayMove] = useState(null)
    const [gameResult, setGameResult] = useState(null)
    const [selectedPiece, setSelectedPiece] = useState(null)

    // Definir la función de análisis antes de usarla en useEffect
    const analyzeCurrentPosition = useCallback(async () => {
        if (!fen) return

        setAnalyzingPosition(true)
        try {
            const analysis = await analysisService.getQuickEvaluation(fen)
            setCurrentAnalysis(analysis)

            // Log del evento de análisis
            await logService.logPositionAnalysis(fen, 5, analysis)
        } catch (error) {
            console.error('Error analyzing position:', error)
            setCurrentAnalysis({ error: error.message })
        } finally {
            setAnalyzingPosition(false)
        }
    }, [fen])

    const loadGameData = async (id) => {
        try {
            setError('')
            await loadGame(id)
            logger.info('chess_board', 'Partida cargada en el tablero', { gameId: id })

            // Log del evento
            await logService.logGameLoad(id, gameData)
        } catch (error) {
            setError(`Error cargando partida: ${error.message}`)
            logger.error('chess_board', 'Error cargando partida en tablero', error)
        }
    }

    // Cargar partida si se proporciona un ID
    useEffect(() => {
        if (gameId) {
            loadGameData(gameId)
        }
    }, [gameId])

    // Analizar posición cuando cambie el FEN (si el análisis está habilitado)
    useEffect(() => {
        logger.debug('chess_board', 'FEN cambió - efecto de análisis', {
            fen: fen?.substring(0, 30),
            currentMoveIndex,
            gameId,
            analysisEnabled,
            analyzingPosition
        })

        if (analysisEnabled && fen && !analyzingPosition) {
            // Pequeño delay para asegurar que el tablero se haya actualizado
            const timeoutId = setTimeout(() => {
                analyzeCurrentPosition()
            }, 100)

            return () => clearTimeout(timeoutId)
        }
    }, [fen, analysisEnabled, currentMoveIndex, analyzingPosition, analyzeCurrentPosition])

    const handlePreviousMove = async () => {
        logger.info('chess_board', 'ANTES navegación anterior', {
            currentMoveIndex,
            fen: fen?.substring(0, 30),
            gameHistoryLength: gameHistory.length
        })

        previousMove()

        // Asegurar que React procese el cambio de estado
        setTimeout(() => {
            logger.info('chess_board', 'DESPUÉS navegación anterior', {
                currentMoveIndex,
                fen: fen?.substring(0, 30),
                gameHistoryLength: gameHistory.length
            })
        }, 100)

        await logService.logMoveNavigation('previous', currentMoveIndex, gameHistory.length)
    }

    const handleNextMove = async () => {
        logger.info('chess_board', 'ANTES navegación siguiente', {
            currentMoveIndex,
            fen: fen?.substring(0, 30),
            gameHistoryLength: gameHistory.length
        })

        nextMove()

        // Asegurar que React procese el cambio de estado
        setTimeout(() => {
            logger.info('chess_board', 'DESPUÉS navegación siguiente', {
                currentMoveIndex,
                fen: fen?.substring(0, 30),
                gameHistoryLength: gameHistory.length
            })
        }, 100)

        await logService.logMoveNavigation('next', currentMoveIndex, gameHistory.length)
    }

    const handleGoToStart = async () => {
        goToStart()
        await logService.logMoveNavigation('start', -1, gameHistory.length)
    }

    const handleGoToEnd = async () => {
        goToEnd()
        await logService.logMoveNavigation('end', gameHistory.length - 1, gameHistory.length)
    }

    const handleSquareClick = async (square) => {
        console.log('🔲 Square clicked:', square)
        console.log('  boardMode:', boardMode, '| gameStatus:', gameStatus, '| thinking:', thinking)
        console.log('  playGame exists:', !!playGame, '| playerColor:', playerColor)
        console.log('  selectedPiece:', selectedPiece)

        // Modo juego: permitir movimientos
        if (boardMode === 'play' && gameStatus === 'playing' && !thinking) {
            console.log('✅ Inside PLAY mode logic')

            if (!selectedPiece) {
                console.log('  No piece selected, trying to select...')

                // Seleccionar pieza del jugador
                const piece = playGame?.get(square)
                console.log('  Piece at square:', piece)

                if (piece && piece.color === (playerColor === 'white' ? 'w' : 'b')) {
                    console.log('  ✅ Selecting piece at', square)
                    setSelectedPiece(square)
                    setSelectedSquare(square)
                } else {
                    console.log('  ❌ No valid piece to select')
                }
            } else {
                console.log('  Piece already selected, attempting move from', selectedPiece, 'to', square)

                // Intentar mover
                if (selectedPiece === square) {
                    // Deseleccionar si clickea la misma
                    console.log('  Deselecting same square')
                    setSelectedPiece(null)
                    setSelectedSquare(null)
                } else {
                    const result = tryPlayerMove(playGame, selectedPiece, square)
                    console.log('  Move result:', result)

                    if (result.success) {
                        console.log('  ✅ Move successful!')
                        setLastPlayMove({ from: selectedPiece, to: square })
                        setPlayMoveHistory([...playMoveHistory, result.move.san])
                        setSelectedPiece(null)
                        setSelectedSquare(null)

                        // Verificar fin del juego
                        const gameOver = checkGameStatus(playGame)
                        if (gameOver.isOver) {
                            setGameStatus('finished')
                            setGameResult(gameOver)
                        } else {
                            // Turno de Stockfish
                            setThinking(true)
                            makeStockfishMove(playGame, difficulty, (result) => {
                                if (result.success) {
                                    setLastPlayMove({ from: result.move.from, to: result.move.to })
                                    setPlayMoveHistory([...playMoveHistory, result.move.san])

                                    const gameOver = checkGameStatus(playGame)
                                    if (gameOver.isOver) {
                                        setGameStatus('finished')
                                        setGameResult(gameOver)
                                    }
                                }
                                setThinking(false)
                            })
                        }
                    } else {
                        console.log('  ❌ Move invalid')
                    }
                }
            }
            return
        }

        console.log('📖 VIEW mode logic activated')

        // Modo visualización: solo mostrar info
        setSelectedSquare(square)

        // Obtener información de la casilla (pieza, etc.)
        const piece = game?.get(square)
        setSquareInfo({
            square,
            piece: piece ? `${piece.color}${piece.type}` : null,
            fen
        })

        // Log del evento
        await logService.logSquareClick(square, piece, fen)
    }

    const toggleAnalysis = () => {
        setAnalysisEnabled(!analysisEnabled)
        if (!analysisEnabled && fen) {
            analyzeCurrentPosition()
        }
    }

    // Funciones para modo de juego
    const startNewGame = () => {
        console.log('🎮 Starting new game...')
        console.log('  playerColor:', playerColor, '| difficulty:', difficulty)

        const result = startNewStockfishGame(playerColor, difficulty)
        console.log('  startNewStockfishGame result:', result)
        console.log('  result.game exists:', !!result.game)
        console.log('  result.game FEN:', result.game?.fen())

        setPlayGame(result.game)
        setPlayMoveHistory([])
        setLastPlayMove(null)
        setGameResult(null)
        setGameStatus('playing')
        setSelectedPiece(null)

        console.log('  ✅ Game status set to: playing')

        logger.info('chess_board play', 'Nueva partida contra Stockfish', { playerColor, difficulty })

        // Si el jugador es negras, Stockfish mueve primero
        if (playerColor === 'black') {
            console.log('  Player is black, Stockfish moves first...')
            setThinking(true)
            setTimeout(() => {
                makeStockfishMove(result.game, difficulty, (moveResult) => {
                    if (moveResult.success) {
                        setLastPlayMove({ from: moveResult.move.from, to: moveResult.move.to })
                        setPlayMoveHistory([moveResult.move.san])
                    }
                    setThinking(false)
                })
            }, 500)
        } else {
            console.log('  Player is white, waiting for player move...')
        }
    }

    const switchMode = (newMode) => {
        console.log('🔄 Switching mode to:', newMode)
        console.log('  Current gameStatus:', gameStatus)

        setBoardMode(newMode)

        if (newMode === 'play' && gameStatus === 'setup') {
            console.log('  Switched to PLAY mode, waiting for game setup')
            // No hacer nada, esperar que configure
        } else if (newMode === 'view') {
            console.log('  Switched to VIEW mode, resetting play state')
            // Reset play state
            setGameStatus('setup')
            setPlayGame(null)
            setPlayMoveHistory([])
        }
    }

    const boardWidth = Math.min(window.innerWidth - 200, 400) // Tablero más pequeño

    // Obtener información del último movimiento
    const getLastMove = () => {
        if (gameHistory.length > 0 && currentMoveIndex >= 0) {
            const move = gameHistory[currentMoveIndex]
            if (move && move.move) {
                // Si es notación UCI (e2e4), usar directamente
                if (move.move.length >= 4) {
                    return {
                        from: move.move.substring(0, 2),
                        to: move.move.substring(2, 4)
                    }
                }
                // Si es notación SAN, intentar extraer info
                return null // Por ahora, solo soportamos UCI
            }
        }
        return null
    }

    const lastMove = getLastMove()

    return (
        <Box sx={{
            display: 'flex',
            flexDirection: { xs: 'column', md: 'row' },
            gap: 3,
            alignItems: 'flex-start',
            justifyContent: 'center',
            maxWidth: 1200,
            mx: 'auto'
        }}>
            {/* Tablero */}
            <Paper elevation={2} sx={{ p: 2, maxWidth: 450 }}>
                <Typography variant="h6" gutterBottom align="center">
                    CHESS TRAINER
                    {gameData && boardMode === 'view' && (
                        <Typography variant="body2" color="text.secondary" align="center">
                            {gameData.white || 'Blancas'} vs {gameData.black || 'Negras'}
                        </Typography>
                    )}
                </Typography>

                {/* Selector de modo */}
                <Box sx={{ mb: 2, display: 'flex', justifyContent: 'center', gap: 1 }}>
                    <Button
                        variant={boardMode === 'view' ? 'contained' : 'outlined'}
                        startIcon={<Visibility />}
                        onClick={() => switchMode('view')}
                        size="small"
                    >
                        Ver Partida
                    </Button>
                    <Button
                        variant={boardMode === 'play' ? 'contained' : 'outlined'}
                        color="error"
                        startIcon={<SportsEsports />}
                        onClick={() => switchMode('play')}
                        size="small"
                    >
                        Jugar vs Stockfish
                    </Button>
                </Box>

                {/* Configuración de juego (solo en modo play) */}
                {boardMode === 'play' && gameStatus === 'setup' && (
                    <Card sx={{ mb: 2, bgcolor: 'warning.50' }}>
                        <CardContent>
                            <Typography variant="subtitle2" gutterBottom>
                                ⚙️ Configuración de Partida
                            </Typography>
                            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                                <Box>
                                    <Typography variant="caption">Color:</Typography>
                                    <ButtonGroup fullWidth size="small">
                                        <Button
                                            variant={playerColor === 'white' ? 'contained' : 'outlined'}
                                            onClick={() => setPlayerColor('white')}
                                        >
                                            ♔ Blancas
                                        </Button>
                                        <Button
                                            variant={playerColor === 'black' ? 'contained' : 'outlined'}
                                            onClick={() => setPlayerColor('black')}
                                        >
                                            ♚ Negras
                                        </Button>
                                    </ButtonGroup>
                                </Box>
                                <Box>
                                    <Typography variant="caption">Dificultad:</Typography>
                                    <ButtonGroup fullWidth size="small" orientation="vertical">
                                        {Object.entries(STOCKFISH_LEVELS).map(([key, level]) => (
                                            <Button
                                                key={key}
                                                variant={difficulty === key ? 'contained' : 'outlined'}
                                                onClick={() => setDifficulty(key)}
                                            >
                                                {level.name} {level.elo}
                                            </Button>
                                        ))}
                                    </ButtonGroup>
                                </Box>
                                <Button
                                    variant="contained"
                                    color="success"
                                    fullWidth
                                    onClick={startNewGame}
                                >
                                    🚀 Comenzar
                                </Button>
                            </Box>
                        </CardContent>
                    </Card>
                )}

                {/* Alerta de estado del juego */}
                {boardMode === 'play' && gameStatus === 'playing' && thinking && (
                    <Alert severity="info" sx={{ mb: 2 }}>
                        🤔 Stockfish está pensando...
                    </Alert>
                )}

                {boardMode === 'play' && gameResult && (
                    <Alert severity={gameResult.type === 'checkmate' ? 'success' : 'info'} sx={{ mb: 2 }}>
                        {gameResult.message}
                    </Alert>
                )}

                {loading && <LinearProgress sx={{ mb: 2 }} />}

                {error && (
                    <Alert severity="error" sx={{ mb: 2 }}>
                        {error}
                    </Alert>
                )}

                <Box sx={{ mb: 2, display: 'flex', justifyContent: 'center' }}>
                    <SimpleChessBoard
                        fen={boardMode === 'play' && playGame ? playGame.fen() : fen}
                        width={boardWidth}
                        onSquareClick={handleSquareClick}
                        lastMove={boardMode === 'play' ? lastPlayMove : lastMove}
                        selectedSquare={selectedSquare}
                        isCheck={boardMode === 'play' && playGame ? playGame.isCheck() : isCheck}
                        turn={boardMode === 'play' && playGame ? playGame.turn() : turn}
                    />
                </Box>

                {/* Debug info - temporal */}
                <Box sx={{ mb: 2, p: 1, bgcolor: 'grey.100', fontSize: '0.75rem' }}>
                    <Typography variant="caption" display="block">
                        <strong>USING:</strong> SimpleChessBoard (Custom)
                    </Typography>
                    <Typography variant="caption" display="block">
                        <strong>FEN:</strong> {fen}
                    </Typography>
                    <Typography variant="caption" display="block">
                        <strong>Movimiento:</strong> {currentMoveIndex + 1} / {gameHistory.length} | <strong>GameVersion:</strong> {gameVersion}
                    </Typography>
                </Box>

                {/* Panel de análisis */}
                {analysisEnabled && (
                    <Card sx={{ mb: 2, bgcolor: 'grey.50' }}>
                        <CardContent>
                            <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                                <Analytics sx={{ mr: 1 }} />
                                <Typography variant="h6">Análisis</Typography>
                                {analyzingPosition && <LinearProgress sx={{ ml: 2, flex: 1 }} />}
                            </Box>

                            {currentAnalysis && !currentAnalysis.error && (
                                <Box>
                                    {currentAnalysis.evaluation !== null && (
                                        <Chip
                                            label={`Evaluación: ${currentAnalysis.evaluation > 0 ? '+' : ''}${currentAnalysis.evaluation.toFixed(2)}`}
                                            color={currentAnalysis.evaluation > 0 ? 'success' : currentAnalysis.evaluation < 0 ? 'error' : 'default'}
                                            sx={{ mr: 1, mb: 1 }}
                                        />
                                    )}
                                    {currentAnalysis.bestMove && (
                                        <Chip
                                            label={`Mejor jugada: ${currentAnalysis.bestMove}`}
                                            variant="outlined"
                                            sx={{ mr: 1, mb: 1 }}
                                        />
                                    )}
                                    {currentAnalysis.isQuick && (
                                        <Chip
                                            label="Análisis rápido"
                                            size="small"
                                            color="info"
                                            sx={{ mr: 1, mb: 1 }}
                                        />
                                    )}
                                </Box>
                            )}

                            {currentAnalysis?.error && (
                                <Alert severity="warning" size="small">
                                    Error en análisis: {currentAnalysis.error}
                                </Alert>
                            )}
                        </CardContent>
                    </Card>
                )}

                {/* Información de casilla seleccionada */}
                {squareInfo && (
                    <Card sx={{ mb: 2, bgcolor: 'info.50' }}>
                        <CardContent>
                            <Box sx={{ display: 'flex', alignItems: 'center' }}>
                                <Info sx={{ mr: 1 }} />
                                <Typography variant="h6">Casilla {squareInfo.square}</Typography>
                            </Box>
                            <Typography variant="body2" color="text.secondary">
                                {squareInfo.piece ? `Pieza: ${squareInfo.piece}` : 'Casilla vacía'}
                            </Typography>
                        </CardContent>
                    </Card>
                )}

                {/* Controles de navegación (solo modo visualización) */}
                {boardMode === 'view' && (
                    <Box sx={{ display: 'flex', justifyContent: 'center', mb: 2 }}>
                        <ButtonGroup variant="outlined" size="small">
                            <Button
                                onClick={handleGoToStart}
                                disabled={currentMoveIndex <= -1}
                                startIcon={<SkipPrevious />}
                            >
                                Inicio
                            </Button>
                            <Button
                                onClick={handlePreviousMove}
                                disabled={currentMoveIndex <= -1}
                                startIcon={<NavigateBefore />}
                            >
                                Anterior
                            </Button>
                            <Button
                                onClick={handleNextMove}
                                disabled={currentMoveIndex >= gameHistory.length - 1}
                                startIcon={<NavigateNext />}
                            >
                                Siguiente
                            </Button>
                            <Button
                                onClick={handleGoToEnd}
                                disabled={currentMoveIndex >= gameHistory.length - 1}
                                startIcon={<SkipNext />}
                            >
                                Final
                            </Button>
                        </ButtonGroup>
                    </Box>
                )}

                {/* Controles para modo juego */}
                {boardMode === 'play' && gameStatus !== 'setup' && (
                    <Box sx={{ display: 'flex', justifyContent: 'center', mb: 2, gap: 1 }}>
                        <Button
                            variant="contained"
                            onClick={startNewGame}
                            startIcon={<Replay />}
                            size="small"
                        >
                            Nueva Partida
                        </Button>
                        <Button
                            variant="outlined"
                            onClick={() => setGameStatus('setup')}
                            size="small"
                        >
                            Configurar
                        </Button>
                    </Box>
                )}

                {/* Controles adicionales */}
                <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', gap: 2, mb: 2 }}>
                    <FormControlLabel
                        control={
                            <Switch
                                checked={analysisEnabled}
                                onChange={toggleAnalysis}
                                size="small"
                            />
                        }
                        label="Análisis automático"
                    />

                    <Tooltip title="Analizar posición actual">
                        <IconButton
                            onClick={analyzeCurrentPosition}
                            disabled={analyzingPosition || !fen}
                            size="small"
                        >
                            <Analytics />
                        </IconButton>
                    </Tooltip>

                    <Button
                        onClick={resetGame}
                        startIcon={<Replay />}
                        size="small"
                        variant="text"
                    >
                        Reiniciar
                    </Button>
                </Box>
            </Paper>

            {/* Panel de información */}
            <Paper elevation={2} sx={{ p: 2, minWidth: 280, maxWidth: 320 }}>
                <Typography variant="h6" gutterBottom>
                    Información de la Partida
                </Typography>

                {/* Información básica de la partida */}
                {gameData && (
                    <Box sx={{ mb: 2 }}>
                        <Typography variant="body2" sx={{ mb: 1 }}>
                            <strong>Game Id:</strong> {gameData.id}
                        </Typography>
                        <Typography variant="body2" sx={{ mb: 1 }}>
                            <strong>Evento:</strong> {gameData.event || 'Sin evento'}
                        </Typography>
                        <Typography variant="body2" sx={{ mb: 1 }}>
                            <strong>Ronda:</strong> {gameData.round || 'Sin ronda'}
                        </Typography>
                        <Typography variant="body2" sx={{ mb: 1 }}>
                            <strong>Jugador Blancas:</strong> {gameData.white || 'Desconocido'}
                        </Typography>
                        <Typography variant="body2" sx={{ mb: 1 }}>
                            <strong>Jugador Negras:</strong> {gameData.black || 'Desconocido'}
                        </Typography>
                        <Typography variant="body2" sx={{ mb: 1 }}>
                            <strong>Resultado:</strong> {gameData.result || 'Sin resultado'}
                        </Typography>
                    </Box>
                )}

                <Card variant="outlined" sx={{ mb: 2 }}>
                    <CardContent sx={{ '&:last-child': { pb: 2 } }}>
                        <Typography variant="body2" color="text.secondary">
                            <strong>Turno:</strong> {turn === 'w' ? 'Blancas' : 'Negras'}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                            <strong>Movimiento:</strong> {currentMoveIndex + 1} / {gameHistory.length}
                        </Typography>
                        {isCheck && (
                            <Typography variant="body2" color="warning.main">
                                ⚠️ Jaque
                            </Typography>
                        )}
                        {isGameOver && (
                            <Typography variant="body2" color="error.main">
                                🏁 Fin del juego
                            </Typography>
                        )}
                    </CardContent>
                </Card>

                {/* Lista de movimientos mejorada */}
                <MovesList
                    gameHistory={gameHistory}
                    currentMoveIndex={currentMoveIndex}
                    onMoveClick={goToMove}
                    gameData={gameData}
                />
            </Paper>

            {/* Sidebar derecho - Info adicional */}
            <Box sx={{ flex: '0 0 300px', minWidth: 250 }}>
                {squareInfo && (
                    <Paper sx={{ p: 2, mb: 2 }}>
                        <Typography variant="h6" gutterBottom>
                            Info de Casilla
                        </Typography>
                        <Typography variant="body2">
                            <strong>Casilla:</strong> {squareInfo.square}
                        </Typography>
                        <Typography variant="body2">
                            <strong>Pieza:</strong> {squareInfo.piece || 'Vacía'}
                        </Typography>
                    </Paper>
                )}
            </Box>
        </Box>
    )
}

export default ChessBoard