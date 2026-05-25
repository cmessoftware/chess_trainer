import React from 'react'
import { Alert, Snackbar } from '@mui/material'

const ErrorBoundary = ({ children }) => {
    const [error, setError] = React.useState(null)
    const [open, setOpen] = React.useState(false)

    React.useEffect(() => {
        const handleError = (error) => {
            setError(error.message)
            setOpen(true)
        }

        window.addEventListener('unhandledrejection', handleError)
        return () => window.removeEventListener('unhandledrejection', handleError)
    }, [])

    const handleClose = () => {
        setOpen(false)
        setError(null)
    }

    return (
        <>
            {children}
            <Snackbar open={open} autoHideDuration={6000} onClose={handleClose}>
                <Alert onClose={handleClose} severity="error" sx={{ width: '100%' }}>
                    {error}
                </Alert>
            </Snackbar>
        </>
    )
}

export default ErrorBoundary