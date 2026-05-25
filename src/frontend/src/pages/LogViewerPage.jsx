import React from 'react'
import { Container, Typography, Box } from '@mui/material'
import LogViewer from '../components/admin/LogViewer.jsx'

const LogViewerPage = () => {
    return (
        <Container maxWidth="xl">
            <Box sx={{ py: 2 }}>
                <Typography variant="h4" gutterBottom>
                    Sistema de Logs
                </Typography>
                <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
                    Visualizador de eventos del sistema para administradores
                </Typography>

                <LogViewer module="chess" />
            </Box>
        </Container>
    )
}

export default LogViewerPage