import React from 'react'
import { Navigate } from 'react-router-dom'
import { CircularProgress, Box } from '@mui/material'
import { useAuth } from '../../hooks/useAuth.js'

const ProtectedRoute = ({ children, requiredPermission = null, customCheck = null }) => {
    const { isAuthenticated, loading, hasPermission, user } = useAuth()

    console.log('🔒 ProtectedRoute:', { isAuthenticated, loading, user: user?.username, requiredPermission, customCheck })

    // Check if user is admin (has ALL permissions)
    const isAdmin = () => {
        return user?.permissions?.includes('ALL') || user?.role === 'admin' || user?.roles?.includes('admin')
    }

    // Custom permission checks
    const hasAccessToGames = () => {
        if (isAdmin()) return true;
        return user?.permissions?.includes('view_own_games') ||
            user?.permissions?.includes('chess_board') ||
            user?.permissions?.includes('play_stockfish')
    }

    const hasAccessToImport = () => {
        if (isAdmin()) return true;
        return user?.permissions?.includes('bulk_upload') ||
            user?.permissions?.includes('import_pgn') ||
            user?.permissions?.includes('manage_sources')
    }

    const hasAccessToReports = () => {
        if (isAdmin()) return true;
        return user?.permissions?.includes('view_stats') ||
            user?.permissions?.includes('advanced_stats') ||
            user?.permissions?.includes('reports') ||
            user?.permissions?.includes('eda_analysis')
    }

    if (loading) {
        return (
            <Box display="flex" justifyContent="center" alignItems="center" minHeight="50vh">
                <CircularProgress />
            </Box>
        )
    }

    if (!isAuthenticated) {
        return <Navigate to="/login" replace />
    }

    // Check custom permission logic
    if (customCheck) {
        let hasAccess = false
        switch (customCheck) {
            case 'hasAccessToGames':
                hasAccess = hasAccessToGames()
                break
            case 'hasAccessToImport':
                hasAccess = hasAccessToImport()
                break
            case 'hasAccessToReports':
                hasAccess = hasAccessToReports()
                break
            default:
                hasAccess = true
        }

        if (!hasAccess) {
            return <Navigate to="/unauthorized" replace />
        }
    }

    // Check standard permission
    if (requiredPermission && !hasPermission(requiredPermission)) {
        return <Navigate to="/unauthorized" replace />
    }

    return children
}

export default ProtectedRoute