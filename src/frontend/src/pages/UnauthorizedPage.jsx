import React from 'react'
import { Container, Typography, Paper, Box, Button } from '@mui/material'
import { ArrowBack, Lock } from '@mui/icons-material'

const UnauthorizedPage = () => {
    return (
        <Container maxWidth="sm">
            <Box
                sx={{
                    marginTop: 8,
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                }}
            >
                <Paper elevation={3} sx={{ padding: 4, width: '100%', textAlign: 'center' }}>
                    <Lock sx={{ fontSize: 64, color: 'error.main', mb: 2 }} />

                    <Typography variant="h4" gutterBottom>
                        Acceso Denegado
                    </Typography>

                    <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
                        No tienes permisos para acceder a esta funcionalidad.
                        Contacta al administrador si crees que esto es un error.
                    </Typography>

                    <Button
                        variant="contained"
                        startIcon={<ArrowBack />}
                        href="/"
                    >
                        Volver al Inicio
                    </Button>
                </Paper>
            </Box>
        </Container>
    )
}

export default UnauthorizedPage