import React from 'react'
import {
    Box,
    Typography,
    Paper,
    Button,
    Chip
} from '@mui/material'

const MovesList = ({
    gameHistory = [],
    currentMoveIndex = -1,
    onMoveClick,
    gameData = null
}) => {
    const formatMoveNumber = (index) => Math.floor(index / 2) + 1
    const isWhiteMove = (index) => index % 2 === 0

    return (
        <Paper sx={{ p: 2, maxHeight: 400, overflow: 'auto' }}>
            <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                📋 Movimientos
                <Chip
                    label={`${gameHistory.length} jugadas`}
                    size="small"
                    color="primary"
                    variant="outlined"
                />
            </Typography>

            {/* Game info */}
            {gameData && (
                <Box sx={{ mb: 2, p: 1, bgcolor: 'grey.50', borderRadius: 1 }}>
                    <Typography variant="caption" display="block">
                        <strong>Blancas:</strong> {gameData.white_player || 'N/A'}
                        {gameData.white_elo && ` (${gameData.white_elo})`}
                    </Typography>
                    <Typography variant="caption" display="block">
                        <strong>Negras:</strong> {gameData.black_player || 'N/A'}
                        {gameData.black_elo && ` (${gameData.black_elo})`}
                    </Typography>
                    {gameData.result && (
                        <Typography variant="caption" display="block">
                            <strong>Resultado:</strong> {gameData.result}
                        </Typography>
                    )}
                </Box>
            )}

            {!(gameData?.sanMoves?.length) ? (
                <Typography variant="body2" color="text.secondary" align="center">
                    No hay movimientos disponibles
                </Typography>
            ) : (
                <Box>
                    {/* Initial position button */}
                    <Button
                        variant={currentMoveIndex === -1 ? "contained" : "text"}
                        size="small"
                        onClick={() => onMoveClick?.(-1)}
                        sx={{
                            mb: 1,
                            mr: 1,
                            minWidth: 'auto',
                            fontSize: '0.75rem'
                        }}
                    >
                        Inicio
                    </Button>

                    {/* Moves grouped by pairs */}
                    {Array.from({ length: Math.ceil((gameData?.sanMoves || []).length / 2) }).map((_, pairIndex) => {
                        const whiteIndex = pairIndex * 2
                        const blackIndex = pairIndex * 2 + 1
                        const whiteMove = gameData?.sanMoves?.[whiteIndex]
                        const blackMove = gameData?.sanMoves?.[blackIndex]

                        return (
                            <Box key={pairIndex} sx={{ mb: 0.5, display: 'flex', alignItems: 'center', gap: 0.5 }}>
                                {/* Move number */}
                                <Typography
                                    variant="caption"
                                    sx={{
                                        minWidth: 30,
                                        fontWeight: 'bold',
                                        color: 'text.secondary'
                                    }}
                                >
                                    {pairIndex + 1}.
                                </Typography>

                                {/* White move */}
                                {whiteMove && (
                                    <Button
                                        variant={currentMoveIndex === whiteIndex ? "contained" : "outlined"}
                                        size="small"
                                        onClick={() => onMoveClick?.(whiteIndex)}
                                        sx={{
                                            minWidth: 60,
                                            fontSize: '0.75rem',
                                            textTransform: 'none'
                                        }}
                                    >
                                        {whiteMove}
                                    </Button>
                                )}

                                {/* Black move */}
                                {blackMove && (
                                    <Button
                                        variant={currentMoveIndex === blackIndex ? "contained" : "outlined"}
                                        size="small"
                                        onClick={() => onMoveClick?.(blackIndex)}
                                        sx={{
                                            minWidth: 60,
                                            fontSize: '0.75rem',
                                            textTransform: 'none'
                                        }}
                                    >
                                        {blackMove}
                                    </Button>
                                )}
                            </Box>
                        )
                    })}
                </Box>
            )}
        </Paper>
    )
}

export default MovesList