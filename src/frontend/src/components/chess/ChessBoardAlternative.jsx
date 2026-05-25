import React, { useState, useEffect, useMemo } from 'react'
import { Box, Typography, Paper } from '@mui/material'
import { Chessboard } from 'react-chessboard'

/**
 * Componente simplificado que fuerza actualización solo cuando el FEN realmente cambia
 */
const ChessBoardAlternative = ({ fen, onSquareClick, customSquareStyles = {}, boardWidth = 400 }) => {
    const [renderKey, setRenderKey] = useState(0)
    
    // Solo actualizar cuando el FEN realmente cambie
    useEffect(() => {
        if (fen) {
            console.log(`[ChessBoardAlternative] FEN received: ${fen}`)
            setRenderKey(prev => prev + 1)
        }
    }, [fen])

    // Memoizar las props para evitar re-renders innecesarios
    const boardProps = useMemo(() => ({
        position: fen,
        boardWidth,
        arePiecesDraggable: false,
        boardOrientation: "white",
        animationDuration: 0,
        onSquareClick,
        customSquareStyles
    }), [fen, boardWidth, onSquareClick, customSquareStyles])

    if (!fen) {
        return (
            <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: boardWidth, width: boardWidth }}>
                <Typography variant="h6" color="text.secondary">
                    Cargando tablero...
                </Typography>
            </Box>
        )
    }

    return (
        <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
            {/* Debug info minimalista */}
            <Paper sx={{ p: 1, mb: 1, bgcolor: 'info.light', fontSize: '0.75rem' }}>
                <Typography variant="caption">
                    <strong>Render:</strong> {renderKey} | <strong>FEN:</strong> {fen?.substring(0, 30)}...
                </Typography>
            </Paper>

            {/* Chessboard con key simple basada en FEN */}
            <Chessboard
                key={`simple-board-${fen}`}
                {...boardProps}
            />
        </Box>
    )
}

export default ChessBoardAlternative