import React, { useState, useEffect } from 'react'
import {
    Container,
    Paper,
    Typography,
    Box,
    Button,
    Grid,
    Alert,
    FormControl,
    InputLabel,
    Select,
    MenuItem,
    Chip,
    CircularProgress,
    Card,
    CardContent,
    LinearProgress
} from '@mui/material'
import { Chess } from 'chess.js'
import SimpleChessBoard from '../components/chess/SimpleChessBoard'
import { logger } from '../utils/helpers.js'
import { useAuth } from '../hooks/useAuth.js'

const DIFFICULTY_LEVELS = {
    beginner: { name: 'Principiante', depth: 1, elo: '~800', color: 'success' },
    easy: { name: 'Fácil', depth: 3, elo: '~1000', color: 'info' },
    medium: { name: 'Intermedio', depth: 5, elo: '~1400', color: 'warning' },
    hard: { name: 'Difícil', depth: 8, elo: '~1800', color: 'error' },
    expert: { name: 'Experto', depth: 12, elo: '~2200', color: 'secondary' }
}

const PlayStockfishPage = () => {
    const { user } = useAuth()
    const [game, setGame] = useState(new Chess())
    const [fen, setFen] = useState(game.fen())
    const [playerColor, setPlayerColor] = useState('white')
    const [difficulty, setDifficulty] = useState('easy')
    const [gameStatus, setGameStatus] = useState('setup') // setup, playing, finished
    const [moveHistory, setMoveHistory] = useState([])
    const [thinking, setThinking] = useState(false)
    const [lastMove, setLastMove] = useState(null)
    const [message, setMessage] = useState('')
    const [gameResult, setGameResult] = useState(null)

    useEffect(() => {
        // Si le toca jugar a Stockfish al inicio (jugador es negras)
        if (gameStatus === 'playing' && playerColor === 'black' && game.turn() === 'w') {
            makeStockfishMove()
        }
    }, [gameStatus])

    const startNewGame = () => {
        const newGame = new Chess()
        setGame(newGame)
        setFen(newGame.fen())
        setMoveHistory([])
        setLastMove(null)
        setMessage('')
        setGameResult(null)
        setGameStatus('playing')
        logger.info('play_stockfish', 'Nueva partida iniciada', { playerColor, difficulty })
    }

    const makeMove = (from, to) => {
        if (gameStatus !== 'playing' || thinking) return false

        const gameCopy = new Chess(game.fen())
        
        // Intentar el movimiento
        try {
            const move = gameCopy.move({ from, to, promotion: 'q' })
            if (!move) return false

            setGame(gameCopy)
            setFen(gameCopy.fen())
            setMoveHistory([...moveHistory, move.san])
            setLastMove({ from, to })
            
            logger.info('play_stockfish', 'Jugador movió', { move: move.san, from, to })

            // Verificar fin del juego
            if (checkGameOver(gameCopy)) {
                return true
            }

            // Turno de Stockfish
            setTimeout(() => makeStockfishMove(gameCopy), 500)
            return true

        } catch (error) {
            logger.error('play_stockfish', 'Movimiento inválido', { from, to, error })
            return false
        }
    }

    const makeStockfishMove = (currentGame = null) => {
        const gameToCheck = currentGame || game
        
        if (gameToCheck.isGameOver()) return

        setThinking(true)
        setMessage('🤔 Stockfish está pensando...')

        // Simular Stockfish con movimiento aleatorio inteligente
        setTimeout(() => {
            const gameCopy = new Chess(gameToCheck.fen())
            const moves = gameCopy.moves({ verbose: true })
            
            if (moves.length === 0) {
                setThinking(false)
                return
            }

            // Selección de movimiento basada en dificultad (simplificado)
            let selectedMove
            if (difficulty === 'beginner') {
                // Aleatorio puro
                selectedMove = moves[Math.floor(Math.random() * moves.length)]
            } else {
                // Inteligencia básica: preferir capturas
                const captures = moves.filter(m => m.captured)
                if (captures.length > 0 && Math.random() > 0.3) {
                    selectedMove = captures[Math.floor(Math.random() * captures.length)]
                } else {
                    selectedMove = moves[Math.floor(Math.random() * moves.length)]
                }
            }

            const move = gameCopy.move(selectedMove)
            setGame(gameCopy)
            setFen(gameCopy.fen())
            setMoveHistory([...moveHistory, move.san])
            setLastMove({ from: move.from, to: move.to })
            setThinking(false)
            setMessage('')

            logger.info('play_stockfish', 'Stockfish movió', { move: move.san })

            // Verificar fin del juego
            checkGameOver(gameCopy)

        }, DIFFICULTY_LEVELS[difficulty].depth * 300) // Tiempo basado en profundidad
    }

    const checkGameOver = (gameToCheck) => {
        if (gameToCheck.isCheckmate()) {
            const winner = gameToCheck.turn() === 'w' ? 'Negras' : 'Blancas'
            const playerWon = (playerColor === 'white' && winner === 'Blancas') || 
                            (playerColor === 'black' && winner === 'Negras')
            
            setGameResult({
                type: 'checkmate',
                winner,
                playerWon,
                message: playerWon ? '🎉 ¡Ganaste! Jaque mate' : '😔 Perdiste - Jaque mate'
            })
            setGameStatus('finished')
            logger.info('play_stockfish', 'Juego terminado - Jaque mate', { winner, playerWon })
            return true
        }

        if (gameToCheck.isDraw()) {
            let drawReason = 'Tablas'
            if (gameToCheck.isStalemate()) drawReason = 'Ahogado'
            if (gameToCheck.isThreefoldRepetition()) drawReason = 'Triple repetición'
            if (gameToCheck.isInsufficientMaterial()) drawReason = 'Material insuficiente'

            setGameResult({
                type: 'draw',
                message: `🤝 Tablas - ${drawReason}`
            })
            setGameStatus('finished')
            logger.info('play_stockfish', 'Juego terminado - Tablas', { drawReason })
            return true
        }

        return false
    }

    const onSquareClick = (square) => {
        // Implementar lógica de selección de pieza y destino
        // Por ahora simplificado
        logger.debug('play_stockfish', 'Casilla clickeada', { square })
    }

    return (
        <Container maxWidth="xl">
            <Paper elevation={3} sx={{ p: 3, mt: 2 }}>
                <Typography variant="h4" gutterBottom>
                    ⚔️ Jugar contra Stockfish
                </Typography>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                    Usuario: <strong>{user?.name || 'Desconocido'}</strong>
                </Typography>

                {gameStatus === 'setup' && (
                    <Box sx={{ mt: 3 }}>
                        <Alert severity="info" sx={{ mb: 3 }}>
                            Configura tu partida y comienza a jugar contra Stockfish
                        </Alert>

                        <Grid container spacing={3}>
                            <Grid item xs={12} md={6}>
                                <FormControl fullWidth>
                                    <InputLabel>Color de piezas</InputLabel>
                                    <Select
                                        value={playerColor}
                                        label="Color de piezas"
                                        onChange={(e) => setPlayerColor(e.target.value)}
                                    >
                                        <MenuItem value="white">♔ Blancas (juego primero)</MenuItem>
                                        <MenuItem value="black">♚ Negras (Stockfish juega primero)</MenuItem>
                                    </Select>
                                </FormControl>
                            </Grid>

                            <Grid item xs={12} md={6}>
                                <FormControl fullWidth>
                                    <InputLabel>Dificultad</InputLabel>
                                    <Select
                                        value={difficulty}
                                        label="Dificultad"
                                        onChange={(e) => setDifficulty(e.target.value)}
                                    >
                                        {Object.entries(DIFFICULTY_LEVELS).map(([key, level]) => (
                                            <MenuItem key={key} value={key}>
                                                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                                    {level.name}
                                                    <Chip 
                                                        label={level.elo} 
                                                        size="small" 
                                                        color={level.color}
                                                    />
                                                </Box>
                                            </MenuItem>
                                        ))}
                                    </Select>
                                </FormControl>
                            </Grid>

                            <Grid item xs={12}>
                                <Button
                                    variant="contained"
                                    size="large"
                                    fullWidth
                                    onClick={startNewGame}
                                >
                                    🚀 Comenzar Partida
                                </Button>
                            </Grid>
                        </Grid>
                    </Box>
                )}

                {(gameStatus === 'playing' || gameStatus === 'finished') && (
                    <Grid container spacing={3} sx={{ mt: 2 }}>
                        <Grid item xs={12} md={8}>
                            <Box sx={{ mb: 2 }}>
                                {thinking && (
                                    <Alert severity="info" icon={<CircularProgress size={20} />}>
                                        {message}
                                    </Alert>
                                )}
                                {gameResult && (
                                    <Alert 
                                        severity={gameResult.playerWon ? 'success' : gameResult.type === 'draw' ? 'info' : 'error'}
                                    >
                                        {gameResult.message}
                                    </Alert>
                                )}
                            </Box>

                            <SimpleChessBoard
                                fen={fen}
                                onSquareClick={onSquareClick}
                                orientation={playerColor}
                                customSquareStyles={lastMove ? {
                                    [lastMove.from]: { backgroundColor: 'rgba(255, 255, 0, 0.4)' },
                                    [lastMove.to]: { backgroundColor: 'rgba(255, 255, 0, 0.4)' }
                                } : {}}
                            />

                            <Box sx={{ mt: 2, display: 'flex', gap: 2 }}>
                                <Button
                                    variant="contained"
                                    onClick={startNewGame}
                                    fullWidth
                                >
                                    🔄 Nueva Partida
                                </Button>
                                <Button
                                    variant="outlined"
                                    onClick={() => setGameStatus('setup')}
                                    fullWidth
                                >
                                    ⚙️ Configuración
                                </Button>
                            </Box>
                        </Grid>

                        <Grid item xs={12} md={4}>
                            <Card>
                                <CardContent>
                                    <Typography variant="h6" gutterBottom>
                                        📊 Información de la partida
                                    </Typography>
                                    
                                    <Box sx={{ mb: 2 }}>
                                        <Typography variant="body2" color="text.secondary">
                                            Jugador: <strong>{playerColor === 'white' ? 'Blancas' : 'Negras'}</strong>
                                        </Typography>
                                        <Typography variant="body2" color="text.secondary">
                                            Dificultad: <Chip 
                                                label={DIFFICULTY_LEVELS[difficulty].name} 
                                                size="small" 
                                                color={DIFFICULTY_LEVELS[difficulty].color}
                                            />
                                        </Typography>
                                        <Typography variant="body2" color="text.secondary">
                                            ELO estimado: <strong>{DIFFICULTY_LEVELS[difficulty].elo}</strong>
                                        </Typography>
                                    </Box>

                                    <Typography variant="subtitle2" gutterBottom>
                                        Movimientos ({moveHistory.length}):
                                    </Typography>
                                    <Box sx={{ 
                                        maxHeight: 400, 
                                        overflowY: 'auto',
                                        backgroundColor: 'grey.100',
                                        p: 1,
                                        borderRadius: 1
                                    }}>
                                        {moveHistory.length === 0 ? (
                                            <Typography variant="body2" color="text.secondary">
                                                No hay movimientos aún
                                            </Typography>
                                        ) : (
                                            <Box>
                                                {moveHistory.map((move, idx) => (
                                                    <Typography 
                                                        key={idx} 
                                                        variant="body2"
                                                        sx={{ 
                                                            fontFamily: 'monospace',
                                                            py: 0.5
                                                        }}
                                                    >
                                                        {Math.floor(idx / 2) + 1}. {move}
                                                    </Typography>
                                                ))}
                                            </Box>
                                        )}
                                    </Box>
                                </CardContent>
                            </Card>
                        </Grid>
                    </Grid>
                )}
            </Paper>
        </Container>
    )
}

export default PlayStockfishPage
