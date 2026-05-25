import React from 'react'
import { useNavigate } from 'react-router-dom'
import { Container, Typography, Paper, Box, Button } from '@mui/material'
import { SportsTennis, Analytics, Upload } from '@mui/icons-material'
import { useAuth } from '../hooks/useAuth.js'
import { logger } from '../utils/helpers.js'

const HomePage = () => {
    const { user, hasPermission } = useAuth()
    const navigate = useNavigate()

    React.useEffect(() => {
        logger.info('home', 'Usuario accedió a página principal', { user: user?.username })
    }, [user])

    return (
        <Container maxWidth="lg">
            <Typography variant="h3" gutterBottom align="center">
                Bienvenido a Chess Trainer
            </Typography>

            <Typography variant="h6" color="text.secondary" align="center" sx={{ mb: 4 }}>
                Hola, {user?.username}! Tu rol: {user?.role}
            </Typography>

            <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: 3 }}>
                {/* Tablero de Ajedrez */}
                {hasPermission('chess_board') && (
                    <Paper elevation={3} sx={{ p: 3, textAlign: 'center' }}>
                        <SportsTennis sx={{ fontSize: 48, color: 'primary.main', mb: 2 }} />
                        <Typography variant="h5" gutterBottom>
                            Tablero de Ajedrez
                        </Typography>
                        <Typography variant="body1" color="text.secondary" sx={{ mb: 2 }}>
                            Analiza partidas y juega contra Stockfish en el mismo tablero unificado
                        </Typography>
                        <Button
                            variant="contained"
                            onClick={() => navigate('/chess-board')}
                            sx={{ mt: 1 }}
                        >
                            Ir al Tablero
                        </Button>
                    </Paper>
                )}

                {/* Navegador de Partidas */}
                {(hasPermission('view_own_games') || hasPermission('view_all_games')) && (
                    <Paper elevation={3} sx={{ p: 3, textAlign: 'center' }}>
                        <Analytics sx={{ fontSize: 48, color: 'secondary.main', mb: 2 }} />
                        <Typography variant="h5" gutterBottom>
                            Navegador de Partidas
                        </Typography>
                        <Typography variant="body1" color="text.secondary" sx={{ mb: 2 }}>
                            Explora tu colección de partidas con filtros avanzados
                        </Typography>
                        <Button
                            variant="contained"
                            onClick={() => navigate('/games')}
                            sx={{ mt: 1 }}
                        >
                            Explorar Partidas
                        </Button>
                    </Paper>
                )}

                {/* Importación */}
                {(hasPermission('import_pgn') || hasPermission('bulk_upload')) && (
                    <Paper elevation={3} sx={{ p: 3, textAlign: 'center' }}>
                        <Upload sx={{ fontSize: 48, color: 'success.main', mb: 2 }} />
                        <Typography variant="h5" gutterBottom>
                            Importar Partidas
                        </Typography>
                        <Typography variant="body1" color="text.secondary" sx={{ mb: 2 }}>
                            Sube archivos PGN para expandir tu base de datos
                        </Typography>
                        <Button
                            variant="contained"
                            onClick={() => navigate('/import')}
                            sx={{ mt: 1 }}
                        >
                            Importar PGN
                        </Button>
                    </Paper>
                )}
            </Box>

            {/* Información adicional para diferentes roles */}
            <Paper elevation={1} sx={{ p: 3, mt: 4, backgroundColor: 'grey.50' }}>
                <Typography variant="h6" gutterBottom>
                    Tu Nivel de Acceso: {user?.role}
                </Typography>

                {user?.role === 'admin' && (
                    <Typography variant="body2" color="text.secondary">
                        Como administrador, tienes acceso completo a todas las funcionalidades del sistema,
                        incluyendo la administración de usuarios y el pipeline de ML.
                    </Typography>
                )}

                {user?.role === 'analista' && (
                    <Typography variant="body2" color="text.secondary">
                        Como analista, puedes acceder al tablero, navegador de partidas, análisis avanzado
                        y el pipeline de machine learning.
                    </Typography>
                )}

                {user?.role === 'user' && (
                    <Typography variant="body2" color="text.secondary">
                        Como usuario, puedes acceder al tablero de ajedrez (con modo de juego contra Stockfish integrado),
                        ver tus propias partidas en el navegador, y analizar tus juegos para mejorar.
                    </Typography>
                )}
            </Paper>
        </Container>
    )
}

export default HomePage