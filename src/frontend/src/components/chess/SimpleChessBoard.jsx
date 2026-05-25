import React from 'react'
import { Box, Typography } from '@mui/material'

/**
 * Componente de tablero de ajedrez simple que renderiza la posición FEN como texto
 */
const SimpleChessBoard = ({
    fen,
    width = 400,
    onSquareClick,
    lastMove = null,
    selectedSquare = null,
    isCheck = false,
    turn = 'w'
}) => {
    // Función para parsear FEN y obtener la posición del tablero
    const parseFEN = (fenString) => {
        if (!fenString) return null

        const [boardPart] = fenString.split(' ')
        const ranks = boardPart.split('/')

        return ranks.map(rank => {
            let squares = []
            for (let char of rank) {
                if (isNaN(char)) {
                    // Es una pieza
                    squares.push(char)
                } else {
                    // Es un número (casillas vacías)
                    for (let i = 0; i < parseInt(char); i++) {
                        squares.push('')
                    }
                }
            }
            return squares
        })
    }

    // Convertir pieza FEN a símbolo Unicode
    const pieceToSymbol = (piece) => {
        const pieces = {
            'K': '♔', 'Q': '♕', 'R': '♖', 'B': '♗', 'N': '♘', 'P': '♙',
            'k': '♚', 'q': '♛', 'r': '♜', 'b': '♝', 'n': '♞', 'p': '♟'
        }
        return pieces[piece] || ''
    }

    // Función para determinar el color del rey en jaque
    const findKingSquare = (boardPosition, color) => {
        const king = color === 'w' ? 'K' : 'k'
        for (let rankIndex = 0; rankIndex < 8; rankIndex++) {
            for (let fileIndex = 0; fileIndex < 8; fileIndex++) {
                if (boardPosition[rankIndex][fileIndex] === king) {
                    return String.fromCharCode(97 + fileIndex) + (8 - rankIndex)
                }
            }
        }
        return null
    }

    const boardPosition = parseFEN(fen)
    const kingSquare = isCheck ? findKingSquare(boardPosition, turn) : null

    if (!boardPosition) {
        return (
            <Box sx={{
                width,
                height: width,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                border: '2px solid #8B4513',
                bgcolor: '#F5DEB3'
            }}>
                <Typography variant="h6">Cargando posición...</Typography>
            </Box>
        )
    }

    const squareSize = width / 8

    return (
        <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
            {/* Status info */}
            <Box sx={{ mb: 1, display: 'flex', gap: 1, alignItems: 'center' }}>
                <Typography variant="caption" sx={{ fontFamily: 'monospace' }}>
                    {turn === 'w' ? '⚪' : '⚫'} {turn === 'w' ? 'Blancas' : 'Negras'}
                </Typography>
                {isCheck && (
                    <Typography variant="caption" sx={{ color: 'error.main', fontWeight: 'bold' }}>
                        JAQUE
                    </Typography>
                )}
                {lastMove && (
                    <Typography variant="caption" sx={{ color: 'primary.main' }}>
                        Último: {lastMove.from}→{lastMove.to}
                    </Typography>
                )}
            </Box>

            {/* Board */}
            <Box sx={{
                width,
                height: width,
                border: '3px solid #8B4513',
                display: 'grid',
                gridTemplateRows: 'repeat(8, 1fr)',
                gridTemplateColumns: 'repeat(8, 1fr)'
            }}>
                {boardPosition.map((rank, rankIndex) =>
                    rank.map((piece, fileIndex) => {
                        const isLight = (rankIndex + fileIndex) % 2 === 0
                        const square = String.fromCharCode(97 + fileIndex) + (8 - rankIndex)

                        // Determinar estilos especiales
                        const isLastMoveFrom = lastMove?.from === square
                        const isLastMoveTo = lastMove?.to === square
                        const isSelected = selectedSquare === square
                        const isKingInCheck = kingSquare === square

                        let bgcolor = isLight ? '#F0D9B5' : '#B58863'
                        let border = 'none'

                        if (isKingInCheck) {
                            bgcolor = '#FF6B6B'  // Rojo para jaque
                        } else if (isLastMoveFrom || isLastMoveTo) {
                            bgcolor = isLight ? '#FFE66D' : '#FF8B42'  // Amarillo/Naranja para último movimiento
                        } else if (isSelected) {
                            bgcolor = isLight ? '#87CEEB' : '#4682B4'  // Azul para seleccionado
                        }

                        if (isSelected) {
                            border = '3px solid #1976d2'
                        } else if (isLastMoveFrom || isLastMoveTo) {
                            border = '2px solid #f57c00'
                        }

                        return (
                            <Box
                                key={`${rankIndex}-${fileIndex}`}
                                onClick={() => onSquareClick?.(square)}
                                sx={{
                                    width: squareSize,
                                    height: squareSize,
                                    bgcolor,
                                    border,
                                    boxSizing: 'border-box',
                                    display: 'flex',
                                    alignItems: 'center',
                                    justifyContent: 'center',
                                    fontSize: `${squareSize * 0.7}px`,
                                    cursor: onSquareClick ? 'pointer' : 'default',
                                    userSelect: 'none',
                                    transition: 'all 0.2s ease-in-out',
                                    position: 'relative',
                                    '&:hover': onSquareClick ? {
                                        transform: 'scale(0.95)',
                                        boxShadow: '0 2px 8px rgba(0,0,0,0.3)',
                                        zIndex: 1
                                    } : {}
                                }}
                            >
                                {pieceToSymbol(piece)}
                                {/* Indicador de última jugada */}
                                {(isLastMoveFrom || isLastMoveTo) && (
                                    <Box
                                        sx={{
                                            position: 'absolute',
                                            top: 2,
                                            left: 2,
                                            width: 8,
                                            height: 8,
                                            borderRadius: '50%',
                                            bgcolor: isLastMoveFrom ? 'warning.main' : 'success.main',
                                            opacity: 0.8
                                        }}
                                    />
                                )}
                            </Box>
                        )
                    })
                )}
            </Box>
        </Box>
    )
}

export default SimpleChessBoard