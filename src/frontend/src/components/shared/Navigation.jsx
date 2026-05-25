import React from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import {
    AppBar,
    Toolbar,
    Typography,
    Button,
    Box,
    Menu,
    MenuItem,
    IconButton,
    Tabs,
    Tab,
    Chip
} from '@mui/material'
import { AccountCircle, ExitToApp, Home, Games, SportsEsports, CloudUpload, Assessment, SwapHoriz, Security } from '@mui/icons-material'
import { useAuth } from '../../hooks/useAuth.js'
import { logger } from '../../utils/helpers.js'
import NotificationBell from './NotificationBell.jsx'

const Navigation = () => {
    const { user, logout, isAuthenticated } = useAuth()
    const [anchorEl, setAnchorEl] = React.useState(null)
    const navigate = useNavigate()
    const location = useLocation()

    const handleMenu = (event) => {
        setAnchorEl(event.currentTarget)
    }

    const handleClose = () => {
        setAnchorEl(null)
    }

    const handleLogout = () => {
        logger.info('navigation', 'Usuario haciendo logout')
        logout()
        handleClose()
        navigate('/login')  // Redirigir a login después del logout
    }

    const handleTabChange = (event, newValue) => {
        navigate(newValue)
    }

    const getCurrentTab = () => {
        const path = location.pathname
        if (path === '/') return '/'
        if (path.startsWith('/games')) return '/games'
        if (path.startsWith('/chess-board')) return '/chess-board'
        if (path.startsWith('/import')) return '/import'
        if (path.startsWith('/reports')) return '/reports'
        return false
    }

    return (
        <AppBar position="static" sx={{ mb: 2 }}>
            <Toolbar>
                <Typography variant="h6" component="div" sx={{ mr: 4 }}>
                    Chess Trainer
                </Typography>

                {isAuthenticated && (
                    <Box sx={{ flexGrow: 1 }}>
                        <Tabs
                            value={getCurrentTab()}
                            onChange={handleTabChange}
                            textColor="inherit"
                            indicatorColor="secondary"
                            sx={{
                                '& .MuiTab-root': {
                                    color: 'rgba(255, 255, 255, 0.7)',
                                    '&.Mui-selected': {
                                        color: 'white'
                                    }
                                }
                            }}
                        >
                            <Tab
                                label="Inicio"
                                value="/"
                                icon={<Home />}
                                iconPosition="start"
                                sx={{ minHeight: 48 }}
                            />
                            <Tab
                                label="Partidas"
                                value="/games"
                                icon={<Games />}
                                iconPosition="start"
                                sx={{ minHeight: 48 }}
                            />
                            <Tab
                                label="Tablero"
                                value="/chess-board"
                                icon={<SportsEsports />}
                                iconPosition="start"
                                sx={{ minHeight: 48 }}
                            />
                            <Tab
                                label="Importar"
                                value="/import"
                                icon={<CloudUpload />}
                                iconPosition="start"
                                sx={{ minHeight: 48 }}
                            />
                            <Tab
                                label="Reportes"
                                value="/reports"
                                icon={<Assessment />}
                                iconPosition="start"
                                sx={{ minHeight: 48 }}
                            />
                        </Tabs>
                    </Box>
                )}

                {isAuthenticated ? (
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                        <Typography variant="body2">
                            {user?.username}
                        </Typography>

                        {/* Role Indicator */}
                        <Chip
                            icon={<SwapHoriz />}
                            label={user?.roles?.join(', ') || 'Sin roles'}
                            color="primary"
                            variant="outlined"
                            sx={{ color: 'white', borderColor: 'white' }}
                        />

                        {/* Campanita de notificaciones */}
                        <NotificationBell />

                        <IconButton
                            size="large"
                            aria-label="account of current user"
                            aria-controls="menu-appbar"
                            aria-haspopup="true"
                            onClick={handleMenu}
                            color="inherit"
                        >
                            <AccountCircle />
                        </IconButton>
                        <Menu
                            id="menu-appbar"
                            anchorEl={anchorEl}
                            anchorOrigin={{
                                vertical: 'top',
                                horizontal: 'right',
                            }}
                            keepMounted
                            transformOrigin={{
                                vertical: 'top',
                                horizontal: 'right',
                            }}
                            open={Boolean(anchorEl)}
                            onClose={handleClose}
                        >
                            <MenuItem disabled>
                                <strong>Usuario: {user?.username}</strong>
                            </MenuItem>
                            <MenuItem disabled>
                                <strong>Roles: {user?.roles?.join(', ') || 'N/A'}</strong>
                            </MenuItem>
                            <MenuItem disabled>
                                Permisos: {user?.permissions?.length || 0} permisos activos
                            </MenuItem>
                            {user?.roles?.includes('admin') && (
                                <MenuItem onClick={() => { handleClose(); navigate('/admin/roles'); }}>
                                    <Security sx={{ mr: 1 }} />
                                    Administrar Roles
                                </MenuItem>
                            )}
                            <MenuItem onClick={handleLogout}>
                                <ExitToApp sx={{ mr: 1 }} />
                                Cerrar Sesión
                            </MenuItem>
                        </Menu>
                    </Box>
                ) : (
                    <Button color="inherit" href="/login">
                        Iniciar Sesión
                    </Button>
                )}
            </Toolbar>
        </AppBar>
    )
}

export default Navigation