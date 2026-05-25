import React, { useState, useEffect } from 'react'
import {
    Box,
    Paper,
    Typography,
    Table,
    TableBody,
    TableCell,
    TableContainer,
    TableHead,
    TableRow,
    Chip,
    Button,
    FormControl,
    InputLabel,
    Select,
    MenuItem,
    TextField,
    LinearProgress,
    Alert,
    Card,
    CardContent,
    Pagination
} from '@mui/material'
import {
    Refresh,
    FilterList,
    Clear,
    Download,
    Visibility
} from '@mui/icons-material'
import { logService } from '../../services/logService.js'

const LogViewer = ({ module = 'chess' }) => {
    const [logs, setLogs] = useState([])
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState('')
    const [filters, setFilters] = useState({
        action: '',
        user_id: '',
        limit: 50,
        offset: 0
    })
    const [totalLogs, setTotalLogs] = useState(0)
    const [page, setPage] = useState(1)
    const [selectedLog, setSelectedLog] = useState(null)

    // Acciones disponibles para filtrar
    const chessActions = [
        'board_move',
        'game_load',
        'position_analysis',
        'move_navigation',
        'square_click'
    ]

    useEffect(() => {
        loadLogs()
    }, [filters.offset, filters.limit])

    const loadLogs = async () => {
        setLoading(true)
        setError('')

        try {
            const response = await logService.getChessLogs(
                filters.limit,
                filters.offset,
                filters.action || null
            )

            setLogs(response.logs || [])
            setTotalLogs(response.total || 0)
        } catch (error) {
            setError(`Error cargando logs: ${error.message}`)
            console.error('Error loading logs:', error)
        } finally {
            setLoading(false)
        }
    }

    const handleFilterChange = (field, value) => {
        setFilters(prev => ({
            ...prev,
            [field]: value,
            offset: 0 // Reset to first page when filtering
        }))
        setPage(1)
    }

    const handlePageChange = (event, newPage) => {
        setPage(newPage)
        setFilters(prev => ({
            ...prev,
            offset: (newPage - 1) * filters.limit
        }))
    }

    const clearFilters = () => {
        setFilters({
            action: '',
            user_id: '',
            limit: 50,
            offset: 0
        })
        setPage(1)
    }

    const applyFilters = () => {
        setFilters(prev => ({ ...prev, offset: 0 }))
        setPage(1)
        loadLogs()
    }

    const formatTimestamp = (timestamp) => {
        return new Date(timestamp).toLocaleString()
    }

    const getActionColor = (action) => {
        const colors = {
            'board_move': 'primary',
            'game_load': 'success',
            'position_analysis': 'info',
            'move_navigation': 'secondary',
            'square_click': 'default'
        }
        return colors[action] || 'default'
    }

    const formatLogData = (data) => {
        if (!data) return 'Sin datos'

        const important = []
        if (data.move) important.push(`Jugada: ${data.move}`)
        if (data.gameId) important.push(`Partida: ${data.gameId}`)
        if (data.square) important.push(`Casilla: ${data.square}`)
        if (data.evaluation !== undefined) important.push(`Eval: ${data.evaluation}`)

        return important.length > 0 ? important.join(', ') : JSON.stringify(data)
    }

    const totalPages = Math.ceil(totalLogs / filters.limit)

    return (
        <Box sx={{ p: 3 }}>
            <Paper sx={{ p: 2, mb: 2 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'between', mb: 2 }}>
                    <Typography variant="h5" sx={{ display: 'flex', alignItems: 'center' }}>
                        <Visibility sx={{ mr: 1 }} />
                        Log Viewer - {module.charAt(0).toUpperCase() + module.slice(1)}
                    </Typography>
                    <Box sx={{ display: 'flex', gap: 1, ml: 'auto' }}>
                        <Button
                            onClick={loadLogs}
                            startIcon={<Refresh />}
                            variant="outlined"
                            size="small"
                        >
                            Actualizar
                        </Button>
                    </Box>
                </Box>

                {/* Filtros */}
                <Box sx={{ display: 'flex', gap: 2, mb: 2, flexWrap: 'wrap', alignItems: 'center' }}>
                    <FormControl size="small" sx={{ minWidth: 150 }}>
                        <InputLabel>Acción</InputLabel>
                        <Select
                            value={filters.action}
                            onChange={(e) => handleFilterChange('action', e.target.value)}
                            label="Acción"
                        >
                            <MenuItem value="">Todas</MenuItem>
                            {chessActions.map(action => (
                                <MenuItem key={action} value={action}>
                                    {action}
                                </MenuItem>
                            ))}
                        </Select>
                    </FormControl>

                    <TextField
                        size="small"
                        label="Usuario"
                        value={filters.user_id}
                        onChange={(e) => handleFilterChange('user_id', e.target.value)}
                        sx={{ minWidth: 150 }}
                    />

                    <FormControl size="small" sx={{ minWidth: 100 }}>
                        <InputLabel>Límite</InputLabel>
                        <Select
                            value={filters.limit}
                            onChange={(e) => handleFilterChange('limit', e.target.value)}
                            label="Límite"
                        >
                            <MenuItem value={25}>25</MenuItem>
                            <MenuItem value={50}>50</MenuItem>
                            <MenuItem value={100}>100</MenuItem>
                        </Select>
                    </FormControl>

                    <Button
                        onClick={applyFilters}
                        startIcon={<FilterList />}
                        variant="contained"
                        size="small"
                    >
                        Filtrar
                    </Button>

                    <Button
                        onClick={clearFilters}
                        startIcon={<Clear />}
                        variant="outlined"
                        size="small"
                    >
                        Limpiar
                    </Button>
                </Box>

                {/* Información de resultados */}
                <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                    Mostrando {logs.length} de {totalLogs} registros
                </Typography>
            </Paper>

            {loading && <LinearProgress sx={{ mb: 2 }} />}

            {error && (
                <Alert severity="error" sx={{ mb: 2 }}>
                    {error}
                </Alert>
            )}

            {/* Tabla de logs */}
            <TableContainer component={Paper}>
                <Table size="small">
                    <TableHead>
                        <TableRow>
                            <TableCell>Timestamp</TableCell>
                            <TableCell>Usuario</TableCell>
                            <TableCell>Acción</TableCell>
                            <TableCell>Datos</TableCell>
                            <TableCell>ID</TableCell>
                        </TableRow>
                    </TableHead>
                    <TableBody>
                        {logs.map((log) => (
                            <TableRow
                                key={log.log_id}
                                hover
                                sx={{ cursor: 'pointer' }}
                                onClick={() => setSelectedLog(log)}
                            >
                                <TableCell>
                                    <Typography variant="body2">
                                        {formatTimestamp(log.timestamp)}
                                    </Typography>
                                </TableCell>
                                <TableCell>
                                    <Chip
                                        label={log.user_id || 'Sin usuario'}
                                        size="small"
                                        variant="outlined"
                                    />
                                </TableCell>
                                <TableCell>
                                    <Chip
                                        label={log.action}
                                        color={getActionColor(log.action)}
                                        size="small"
                                    />
                                </TableCell>
                                <TableCell>
                                    <Typography variant="body2" noWrap>
                                        {formatLogData(log.data)}
                                    </Typography>
                                </TableCell>
                                <TableCell>
                                    <Typography variant="body2" color="text.secondary">
                                        {log.log_id}
                                    </Typography>
                                </TableCell>
                            </TableRow>
                        ))}
                    </TableBody>
                </Table>
            </TableContainer>

            {/* Paginación */}
            {totalPages > 1 && (
                <Box sx={{ display: 'flex', justifyContent: 'center', mt: 2 }}>
                    <Pagination
                        count={totalPages}
                        page={page}
                        onChange={handlePageChange}
                        color="primary"
                    />
                </Box>
            )}

            {/* Detalle de log seleccionado */}
            {selectedLog && (
                <Card sx={{ mt: 2 }}>
                    <CardContent>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                            <Typography variant="h6">
                                Detalle del Log #{selectedLog.log_id}
                            </Typography>
                            <Button
                                onClick={() => setSelectedLog(null)}
                                size="small"
                            >
                                Cerrar
                            </Button>
                        </Box>

                        <Box sx={{ mb: 1 }}>
                            <Typography variant="body2" color="text.secondary">
                                <strong>Usuario:</strong> {selectedLog.user_id || 'Sin usuario'}
                            </Typography>
                        </Box>

                        <Box sx={{ mb: 1 }}>
                            <Typography variant="body2" color="text.secondary">
                                <strong>Timestamp:</strong> {formatTimestamp(selectedLog.timestamp)}
                            </Typography>
                        </Box>

                        <Box sx={{ mb: 1 }}>
                            <Typography variant="body2" color="text.secondary">
                                <strong>Acción:</strong> {selectedLog.action}
                            </Typography>
                        </Box>

                        {selectedLog.data && (
                            <Box>
                                <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                                    <strong>Datos:</strong>
                                </Typography>
                                <Paper sx={{ p: 1, bgcolor: 'grey.50' }}>
                                    <pre style={{
                                        fontSize: '12px',
                                        margin: 0,
                                        whiteSpace: 'pre-wrap',
                                        wordBreak: 'break-word'
                                    }}>
                                        {JSON.stringify(selectedLog.data, null, 2)}
                                    </pre>
                                </Paper>
                            </Box>
                        )}
                    </CardContent>
                </Card>
            )}
        </Box>
    )
}

export default LogViewer