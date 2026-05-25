import React, { useState, useEffect } from 'react'
import {
    IconButton,
    Badge,
    Popover,
    List,
    ListItem,
    ListItemText,
    ListItemIcon,
    Typography,
    Box,
    Chip,
    Divider,
    Button
} from '@mui/material'
import {
    Notifications,
    CheckCircle,
    Error,
    Info,
    Warning,
    HourglassEmpty,
    Delete,
    Clear
} from '@mui/icons-material'
import { notificationService } from '../../services/notificationService.js'
import { logger } from '../../utils/helpers.js'

const NotificationBell = () => {
    const [anchorEl, setAnchorEl] = useState(null)
    const [notifications, setNotifications] = useState([])
    const [unreadCount, setUnreadCount] = useState(0)

    useEffect(() => {
        // Cargar notificaciones al montar
        loadNotifications()

        // Polling cada 10 segundos para verificar nuevas notificaciones
        const interval = setInterval(() => {
            loadNotifications()
        }, 10000)

        return () => clearInterval(interval)
    }, [])

    const loadNotifications = async () => {
        try {
            const data = await notificationService.getNotifications()
            // Asegurar que data sea un array
            if (Array.isArray(data)) {
                setNotifications(data)
                setUnreadCount(data.filter(n => !n.read).length)
            } else {
                // Si no es un array, usar array vacío
                setNotifications([])
                setUnreadCount(0)
            }
        } catch (error) {
            logger.error('notifications', 'Error cargando notificaciones', { error })
            // En caso de error, asegurar que notifications siga siendo un array
            setNotifications([])
            setUnreadCount(0)
        }
    }

    const handleClick = (event) => {
        setAnchorEl(event.currentTarget)
    }

    const handleClose = () => {
        setAnchorEl(null)
    }

    const handleMarkAsRead = async (notificationId) => {
        try {
            await notificationService.markAsRead(notificationId)
            await loadNotifications()
        } catch (error) {
            logger.error('notifications', 'Error marcando como leída', { error })
        }
    }

    const handleMarkAllAsRead = async () => {
        try {
            await notificationService.markAllAsRead()
            await loadNotifications()
        } catch (error) {
            logger.error('notifications', 'Error marcando todas como leídas', { error })
        }
    }

    const handleDelete = async (notificationId) => {
        try {
            await notificationService.deleteNotification(notificationId)
            await loadNotifications()
        } catch (error) {
            logger.error('notifications', 'Error eliminando notificación', { error })
        }
    }

    const handleClearAll = async () => {
        try {
            await notificationService.clearAll()
            await loadNotifications()
        } catch (error) {
            logger.error('notifications', 'Error limpiando notificaciones', { error })
        }
    }

    const getIcon = (type) => {
        switch (type) {
            case 'success':
                return <CheckCircle color="success" />
            case 'error':
                return <Error color="error" />
            case 'warning':
                return <Warning color="warning" />
            case 'info':
                return <Info color="info" />
            case 'processing':
                return <HourglassEmpty color="primary" />
            default:
                return <Info />
        }
    }

    const getStatusChip = (status) => {
        switch (status) {
            case 'completed':
                return <Chip label="Completado" size="small" color="success" />
            case 'failed':
                return <Chip label="Error" size="small" color="error" />
            case 'processing':
                return <Chip label="En proceso" size="small" color="primary" />
            case 'queued':
                return <Chip label="En cola" size="small" color="default" />
            default:
                return null
        }
    }

    const formatTime = (timestamp) => {
        const date = new Date(timestamp)
        const now = new Date()
        const diff = Math.floor((now - date) / 1000) // segundos

        if (diff < 60) return 'Hace un momento'
        if (diff < 3600) return `Hace ${Math.floor(diff / 60)} min`
        if (diff < 86400) return `Hace ${Math.floor(diff / 3600)} h`
        return date.toLocaleDateString()
    }

    const open = Boolean(anchorEl)

    return (
        <>
            <IconButton
                color="inherit"
                onClick={handleClick}
                sx={{ ml: 2 }}
            >
                <Badge badgeContent={unreadCount} color="error">
                    <Notifications />
                </Badge>
            </IconButton>

            <Popover
                open={open}
                anchorEl={anchorEl}
                onClose={handleClose}
                anchorOrigin={{
                    vertical: 'bottom',
                    horizontal: 'right',
                }}
                transformOrigin={{
                    vertical: 'top',
                    horizontal: 'right',
                }}
            >
                <Box sx={{ width: 400, maxHeight: 600 }}>
                    {/* Header */}
                    <Box sx={{ p: 2, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <Typography variant="h6">
                            Notificaciones
                        </Typography>
                        {notifications.length > 0 && (
                            <Box>
                                <Button
                                    size="small"
                                    onClick={handleMarkAllAsRead}
                                    disabled={unreadCount === 0}
                                >
                                    Marcar todas
                                </Button>
                                <Button
                                    size="small"
                                    onClick={handleClearAll}
                                    color="error"
                                    startIcon={<Clear />}
                                >
                                    Limpiar
                                </Button>
                            </Box>
                        )}
                    </Box>

                    <Divider />

                    {/* Lista de notificaciones */}
                    {notifications.length === 0 ? (
                        <Box sx={{ p: 4, textAlign: 'center' }}>
                            <Typography variant="body2" color="text.secondary">
                                No hay notificaciones
                            </Typography>
                        </Box>
                    ) : (
                        <List sx={{ maxHeight: 500, overflow: 'auto' }}>
                            {notifications.map((notification, index) => (
                                <React.Fragment key={notification.id}>
                                    <ListItem
                                        sx={{
                                            backgroundColor: notification.read ? 'transparent' : 'action.hover',
                                            cursor: 'pointer',
                                            '&:hover': {
                                                backgroundColor: 'action.selected'
                                            }
                                        }}
                                        onClick={() => !notification.read && handleMarkAsRead(notification.id)}
                                        secondaryAction={
                                            <IconButton
                                                edge="end"
                                                size="small"
                                                onClick={(e) => {
                                                    e.stopPropagation()
                                                    handleDelete(notification.id)
                                                }}
                                            >
                                                <Delete fontSize="small" />
                                            </IconButton>
                                        }
                                    >
                                        <ListItemIcon>
                                            {getIcon(notification.type)}
                                        </ListItemIcon>
                                        <ListItemText
                                            primary={
                                                <Box display="flex" justifyContent="space-between" alignItems="center">
                                                    <Typography variant="subtitle2">
                                                        {notification.title}
                                                    </Typography>
                                                    {getStatusChip(notification.status)}
                                                </Box>
                                            }
                                            secondary={
                                                <>
                                                    <Typography variant="body2" color="text.secondary">
                                                        {notification.message}
                                                    </Typography>
                                                    <Typography variant="caption" color="text.secondary">
                                                        {formatTime(notification.timestamp)}
                                                    </Typography>
                                                    {notification.metadata && (
                                                        <Box sx={{ mt: 0.5 }}>
                                                            {notification.metadata.games && (
                                                                <Typography variant="caption" display="block">
                                                                    Partidas: {notification.metadata.games}
                                                                </Typography>
                                                            )}
                                                            {notification.metadata.duration && (
                                                                <Typography variant="caption" display="block">
                                                                    Duración: {notification.metadata.duration}
                                                                </Typography>
                                                            )}
                                                        </Box>
                                                    )}
                                                </>
                                            }
                                        />
                                    </ListItem>
                                    {index < notifications.length - 1 && <Divider />}
                                </React.Fragment>
                            ))}
                        </List>
                    )}
                </Box>
            </Popover>
        </>
    )
}

export default NotificationBell
