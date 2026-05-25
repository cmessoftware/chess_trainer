import React from 'react'
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { ThemeProvider, createTheme } from '@mui/material/styles'
import { CssBaseline, Container } from '@mui/material'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

// Componentes
import Navigation from './components/shared/Navigation.jsx'
import ProtectedRoute from './components/shared/ProtectedRoute.jsx'
import ErrorBoundary from './components/shared/ErrorBoundary.jsx'

// Páginas
import HomePage from './pages/HomePage.jsx'
import LoginPage from './pages/LoginPage.jsx'
import ChessBoardPage from './pages/ChessBoardPage.jsx'
import GamesPage from './pages/GamesPage.tsx'
import ImportPage from './pages/ImportPage.jsx'
import LogViewerPage from './pages/LogViewerPage.jsx'
import PersonalizedReportsPage from './pages/PersonalizedReportsPage.jsx'
import UnauthorizedPage from './pages/UnauthorizedPage.jsx'
import AdminRolesPage from './pages/AdminRolesPage.jsx'

// Utilidades
import { logger } from './utils/helpers.js'

// Configuración de React Query
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      staleTime: 5 * 60 * 1000, // 5 minutos
    },
  },
})

// Tema personalizado
const theme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
  },
  typography: {
    fontFamily: '"Roboto", "Helvetica", "Arial", sans-serif',
  },
})

function App() {
  React.useEffect(() => {
    logger.info('app', 'Aplicación iniciada')
  }, [])

  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <ErrorBoundary>
          <Router>
            <Navigation />
            <Container maxWidth="xl" sx={{ py: 2 }}>
              <Routes>
                {/* Rutas públicas */}
                <Route path="/login" element={<LoginPage />} />
                <Route path="/unauthorized" element={<UnauthorizedPage />} />

                {/* Rutas protegidas */}
                <Route
                  path="/"
                  element={
                    <ProtectedRoute>
                      <HomePage />
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/chess-board"
                  element={
                    <ProtectedRoute requiredPermission="chess_board">
                      <ChessBoardPage />
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/chess-board/:gameId"
                  element={
                    <ProtectedRoute requiredPermission="chess_board">
                      <ChessBoardPage />
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/games"
                  element={
                    <ProtectedRoute customCheck="hasAccessToGames">
                      <GamesPage />
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/import"
                  element={
                    <ProtectedRoute customCheck="hasAccessToImport">
                      <ImportPage />
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/reports"
                  element={
                    <ProtectedRoute customCheck="hasAccessToReports">
                      <PersonalizedReportsPage />
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/logs"
                  element={
                    <ProtectedRoute requiredPermission="admin">
                      <LogViewerPage />
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/admin/roles"
                  element={
                    <ProtectedRoute requiredPermission="admin">
                      <AdminRolesPage />
                    </ProtectedRoute>
                  }
                />
              </Routes>
            </Container>
          </Router>
        </ErrorBoundary>
      </ThemeProvider>
    </QueryClientProvider>
  )
}

export default App
