import React from 'react'
import { useParams, useNavigate, useLocation } from 'react-router-dom'
import { Container, Typography, Paper, Box, Button } from '@mui/material'
import { ArrowBack } from '@mui/icons-material'
import ChessBoard from '../components/chess/ChessBoard.jsx'

const ChessBoardPage = () => {
    const { gameId } = useParams()
    const navigate = useNavigate()
    const location = useLocation()
    
    // Obtener modo desde el estado de navegación o query params
    const initialMode = location.state?.mode || new URLSearchParams(location.search).get('mode') || 'view'

    const handleBackToGames = () => {
        navigate('/games')
    }

    return (
        <Container maxWidth="lg">
            <Box sx={{ mb: 2 }}>
                <Button
                    startIcon={<ArrowBack />}
                    onClick={handleBackToGames}
                    sx={{ mb: 2 }}
                >
                    Volver a Partidas
                </Button>

                <Typography variant="h4" gutterBottom align="center">
                    Chess Trainer
                </Typography>

                {gameId && (
                    <Typography variant="body1" color="text.secondary" align="center" sx={{ mb: 3 }}>
                        Analizando partida #{gameId}
                    </Typography>
                )}

                {!gameId && (
                    <Typography variant="body1" color="text.secondary" align="center" sx={{ mb: 3 }}>
                        Tablero de práctica y análisis
                    </Typography>
                )}
            </Box>

            {/* Tablero centrado */}
            <Box sx={{
                display: 'flex',
                justifyContent: 'center',
                alignItems: 'flex-start',
                minHeight: '70vh'
            }}>
                <ChessBoard gameId={gameId} initialMode={initialMode} />
            </Box>
        </Container>
    )
}

export default ChessBoardPage