import React, { useState, useEffect } from 'react'
import {
    Container,
    Typography,
    Paper,
    Box,
    TextField,
    Button,
    Table,
    TableBody,
    TableCell,
    TableContainer,
    TableHead,
    TableRow,
    TablePagination,
    Chip,
    Alert,
    CircularProgress,
    InputAdornment,
    FormControl,
    InputLabel,
    Select,
    MenuItem
} from '@mui/material'
import {
    Search,
    Visibility,
    FilterList
} from '@mui/icons-material'
import { useNavigate } from 'react-router-dom'
import { gamesService } from '../services/games'
import { useAuth } from '../hooks/useAuth.js'

const GamesPage = () => {
    const navigate = useNavigate()
    const { hasPermission } = useAuth()
    const [games, setGames] = useState([])
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState('')
    const [totalCount, setTotalCount] = useState(0)
    const [page, setPage] = useState(0)
    const [rowsPerPage, setRowsPerPage] = useState(25)
    const [searchTerm, setSearchTerm] = useState('')
    const [sources, setSources] = useState([])
    const [selectedSource, setSelectedSource] = useState('')

    // Cargar fuentes disponibles
    useEffect(() => {
        const loadSources = async () => {
            try {
                console.log('🔍 Cargando fuentes...')
                const response = await gamesService.getGameSources()
                console.log('📦 Respuesta de fuentes:', response)
                if (response.success) {
                    console.log('✅ Fuentes cargadas:', response.data)
                    setSources(response.data)
                } else {
                    console.error('❌ Error en respuesta de fuentes:', response.message)
                }
            } catch (err) {
                console.error('💥 Error loading sources:', err)
            }
        }
        loadSources()
    }, [])

    // Cargar partidas
    const loadGames = async () => {
        setLoading(true)
        setError('')
        console.log('🎯 Cargando partidas con parámetros:', {
            limit: rowsPerPage,
            offset: page * rowsPerPage,
            source: selectedSource || null,
            search: searchTerm || null
        })
        try {
            const response = await gamesService.getGamesList({
                limit: rowsPerPage,
                offset: page * rowsPerPage,
                source: selectedSource || null,
                search: searchTerm || null
            })

            console.log('🎲 Respuesta de partidas:', response)
            if (response.success) {
                console.log('✅ Partidas encontradas:', response.data.games?.length, 'Total:', response.data.total)
                setGames(response.data.games || [])
                setTotalCount(response.data.total || 0)
            } else {
                console.error('❌ Error en respuesta de partidas:', response.message)
                setError(response.message || 'Error cargando partidas')
                setGames([]) // Asegurar que games sea siempre un array
            }
        } catch (err) {
            console.error('💥 Error de conexión:', err)
            setError('Error de conexión')
            setGames([]) // Asegurar que games sea siempre un array
        } finally {
            setLoading(false)
        }
    }

    useEffect(() => {
        loadGames()
    }, [page, rowsPerPage, selectedSource, searchTerm])

    const handleSearch = async () => {
        setPage(0)
        await loadGames()
    }

    const handleChangePage = (event, newPage) => {
        setPage(newPage)
    }

    const handleChangeRowsPerPage = (event) => {
        setRowsPerPage(parseInt(event.target.value, 10))
        setPage(0)
    }

    const handleViewGame = (gameId) => {
        navigate(`/chess-board/${gameId}`)
    }

    const getResultColor = (result) => {
        switch (result) {
            case '1-0': return 'success'
            case '0-1': return 'error'
            case '1/2-1/2': return 'warning'
            default: return 'default'
        }
    }

    const getResultText = (result) => {
        switch (result) {
            case '1-0': return 'Blancas ganan'
            case '0-1': return 'Negras ganan'
            case '1/2-1/2': return 'Tablas'
            default: return result || 'Sin resultado'
        }
    }

    return (
        <Container maxWidth="xl">
            <Box sx={{ mb: 4 }}>
                <Typography variant="h4" gutterBottom>
                    Navegador de Partidas
                </Typography>
                <Typography variant="body1" color="text.secondary">
                    Explora y analiza partidas de ajedrez de la base de datos
                </Typography>
            </Box>

            {/* Alerta para usuarios con permiso limitado */}
            {hasPermission('view_own_games') && !hasPermission('view_all_games') && (
                <Alert severity="info" sx={{ mb: 3 }}>
                    📋 Mostrando solo tus propias partidas. Como usuario, solo puedes ver las partidas donde has jugado.
                </Alert>
            )}

            {/* Panel de búsqueda */}
            <Paper elevation={2} sx={{ p: 3, mb: 3 }}>
                <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
                    <FilterList sx={{ mr: 1 }} />
                    Filtros de búsqueda
                </Typography>

                <Box sx={{ display: 'flex', gap: 2, alignItems: 'end', flexWrap: 'wrap' }}>
                    <TextField
                        label="Buscar partidas"
                        variant="outlined"
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                        onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                        sx={{ minWidth: 300 }}
                        InputProps={{
                            startAdornment: (
                                <InputAdornment position="start">
                                    <Search />
                                </InputAdornment>
                            ),
                        }}
                    />

                    <FormControl sx={{ minWidth: 200 }}>
                        <InputLabel>Fuente</InputLabel>
                        <Select
                            value={selectedSource}
                            onChange={(e) => setSelectedSource(e.target.value)}
                            label="Fuente"
                        >
                            <MenuItem value="">Todas las fuentes</MenuItem>
                            {sources.map((source) => (
                                <MenuItem key={source} value={source}>
                                    {source}
                                </MenuItem>
                            ))}
                        </Select>
                    </FormControl>

                    <Button
                        variant="contained"
                        onClick={handleSearch}
                        startIcon={<Search />}
                    >
                        Buscar
                    </Button>
                </Box>
            </Paper>

            {/* Mostrar error si existe */}
            {error && (
                <Alert severity="error" sx={{ mb: 3 }}>
                    {error}
                </Alert>
            )}

            {/* Tabla de partidas */}
            <Paper elevation={2}>
                {loading ? (
                    <Box sx={{ display: 'flex', justifyContent: 'center', py: 8 }}>
                        <CircularProgress />
                    </Box>
                ) : (
                    <TableContainer>
                        <Table>
                            <TableHead>
                                <TableRow>
                                    <TableCell><strong>Blancas</strong></TableCell>
                                    <TableCell><strong>Negras</strong></TableCell>
                                    <TableCell><strong>Resultado</strong></TableCell>
                                    <TableCell><strong>ELO Blancas</strong></TableCell>
                                    <TableCell><strong>ELO Negras</strong></TableCell>
                                    <TableCell><strong>ECO</strong></TableCell>
                                    <TableCell><strong>Apertura</strong></TableCell>
                                    <TableCell><strong>Evento</strong></TableCell>
                                    <TableCell><strong>Fecha</strong></TableCell>
                                    <TableCell><strong>Fuente</strong></TableCell>
                                    <TableCell align="center"><strong>Acciones</strong></TableCell>
                                </TableRow>
                            </TableHead>
                            <TableBody>
                                {(games || []).map((game) => (
                                    <TableRow
                                        key={game.game_id}
                                        hover
                                        sx={{ cursor: 'pointer' }}
                                        onClick={() => handleViewGame(game.game_id)}
                                    >
                                        <TableCell>
                                            <Typography variant="body2" sx={{ fontWeight: 500 }}>
                                                {game.white_player || 'Desconocido'}
                                            </Typography>
                                        </TableCell>
                                        <TableCell>
                                            <Typography variant="body2" sx={{ fontWeight: 500 }}>
                                                {game.black_player || 'Desconocido'}
                                            </Typography>
                                        </TableCell>
                                        <TableCell>
                                            <Chip
                                                label={getResultText(game.result)}
                                                color={getResultColor(game.result)}
                                                size="small"
                                            />
                                        </TableCell>
                                        <TableCell>
                                            <Typography variant="body2">
                                                {game.white_elo || '-'}
                                            </Typography>
                                        </TableCell>
                                        <TableCell>
                                            <Typography variant="body2">
                                                {game.black_elo || '-'}
                                            </Typography>
                                        </TableCell>
                                        <TableCell>
                                            <Typography variant="body2" fontFamily="monospace">
                                                {game.eco || '-'}
                                            </Typography>
                                        </TableCell>
                                        <TableCell>
                                            <Typography variant="body2" noWrap sx={{ maxWidth: 200 }}>
                                                {game.opening || '-'}
                                            </Typography>
                                        </TableCell>
                                        <TableCell>
                                            <Typography variant="body2" noWrap sx={{ maxWidth: 150 }}>
                                                {game.event || 'Sin evento'}
                                            </Typography>
                                        </TableCell>
                                        <TableCell>
                                            <Typography variant="body2">
                                                {game.date ? new Date(game.date).toLocaleDateString() : 'Sin fecha'}
                                            </Typography>
                                        </TableCell>
                                        <TableCell>
                                            <Typography variant="body2">
                                                {game.source || '-'}
                                            </Typography>
                                        </TableCell>
                                        <TableCell align="center">
                                            <Button
                                                size="small"
                                                variant="outlined"
                                                startIcon={<Visibility />}
                                                onClick={(e) => {
                                                    e.stopPropagation()
                                                    handleViewGame(game.game_id)
                                                }}
                                            >
                                                Ver
                                            </Button>
                                        </TableCell>
                                    </TableRow>
                                ))}
                            </TableBody>
                        </Table>
                    </TableContainer>
                )}

                {/* Paginación */}
                <TablePagination
                    rowsPerPageOptions={[10, 25, 50, 100]}
                    component="div"
                    count={totalCount}
                    rowsPerPage={rowsPerPage}
                    page={page}
                    onPageChange={handleChangePage}
                    onRowsPerPageChange={handleChangeRowsPerPage}
                    labelRowsPerPage="Partidas por página:"
                    labelDisplayedRows={({ from, to, count }) =>
                        `${from}-${to} de ${count !== -1 ? count : `más de ${to}`}`
                    }
                />
            </Paper>
        </Container>
    )
}

export default GamesPage