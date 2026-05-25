import React, { useState, useEffect } from 'react';
import {
    Card,
    CardContent,
    CardHeader,
    Button,
    TextField,
    FormLabel,
    Checkbox,
    Select,
    MenuItem,
    FormControl,
    InputLabel,
    Chip,
    Alert,
    LinearProgress,
    Typography,
    Box,
    Grid,
    FormControlLabel,
    CircularProgress
} from '@mui/material';
import {
    Download as DownloadIcon,
    Error as AlertCircleIcon,
    CheckCircle as CheckCircleIcon,
    Schedule as ClockIcon,
    Description as FileTextIcon,
    Upload as UploadIcon
} from '@mui/icons-material';
import { notificationService } from '../services/notificationService';
import { importService } from '../services/importService';

const PersonalizedReportsPage = () => {
    // Estados para el formulario
    const [playerName, setPlayerName] = useState('');
    const [minGames, setMinGames] = useState(50);
    const [includeSurvivorship, setIncludeSurvivorship] = useState(true);
    const [includeStreakAnalysis, setIncludeStreakAnalysis] = useState(true);
    const [includePgnGames, setIncludePgnGames] = useState(true);
    const [generatePdf, setGeneratePdf] = useState(true);
    const [outputFormat, setOutputFormat] = useState('markdown');

    // Estados para PGN upload
    const [uploadFiles, setUploadFiles] = useState([]);
    const [isUploadMode, setIsUploadMode] = useState(false);

    // Estados para el proceso
    const [isGenerating, setIsGenerating] = useState(false);
    const [currentJobId, setCurrentJobId] = useState(null);
    const [jobStatus, setJobStatus] = useState(null);
    const [error, setError] = useState(null);

    // Estados para listado de reportes
    const [recentReports, setRecentReports] = useState([]);
    const [loadingReports, setLoadingReports] = useState(false);

    // Cargar reportes recientes al montar
    useEffect(() => {
        loadRecentReports();

        // Polling para actualizar estado del job si hay uno activo
        let pollInterval;
        if (currentJobId && isGenerating) {
            pollInterval = setInterval(() => {
                checkJobStatus(currentJobId);
            }, 3000); // Cada 3 segundos
        }

        return () => {
            if (pollInterval) clearInterval(pollInterval);
        };
    }, [currentJobId, isGenerating]);

    const loadRecentReports = async () => {
        setLoadingReports(true);
        try {
            const response = await fetch('/api/reports/list');
            if (response.ok) {
                const data = await response.json();
                setRecentReports(data.reports || []);
            }
        } catch (error) {
            console.error('Error cargando reportes:', error);
        } finally {
            setLoadingReports(false);
        }
    };

    const handleFileUpload = (event) => {
        const files = Array.from(event.target.files);
        setUploadFiles(files);
    };

    const generateReportFromExisting = async () => {
        if (!playerName.trim()) {
            setError('Por favor ingresa el nombre del jugador');
            return;
        }

        setIsGenerating(true);
        setError(null);

        try {
            const requestData = {
                player_name: playerName.trim(),
                min_games: minGames,
                include_survivorship: includeSurvivorship,
                include_streak_analysis: includeStreakAnalysis,
                include_pgn_games: includePgnGames,
                generate_pdf: generatePdf,
                output_format: outputFormat
            };

            const response = await fetch('/api/reports/generate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(requestData)
            });

            if (response.ok) {
                const data = await response.json();
                setCurrentJobId(data.job_id);
                setJobStatus({
                    job_id: data.job_id,
                    status: 'pending',
                    player_name: playerName,
                    progress_percentage: 0,
                    created_at: new Date().toISOString()
                });

                // Mostrar notificación
                await notificationService.showNotification(
                    'Generando Reporte',
                    `Iniciando análisis para ${playerName}. Tiempo estimado: ${data.estimated_time_minutes} minutos.`,
                    'info'
                );
            } else {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Error generando reporte');
            }
        } catch (error) {
            setError(error.message);
            setIsGenerating(false);
        }
    };

    const generateReportFromUpload = async () => {
        if (!playerName.trim()) {
            setError('Por favor ingresa el nombre del jugador');
            return;
        }

        if (uploadFiles.length === 0) {
            setError('Por favor selecciona archivos PGN');
            return;
        }

        setIsGenerating(true);
        setError(null);

        try {
            // Primero subir los archivos PGN
            const uploadPromises = uploadFiles.map(file =>
                importService.uploadPGN(file, playerName, {
                    onProgress: (progress) => {
                        console.log(`Subiendo ${file.name}: ${progress}%`);
                    }
                })
            );

            const uploadResults = await Promise.all(uploadPromises);
            const uploadedPaths = uploadResults.map(result => result.file_path);

            // Luego generar reporte desde archivos subidos
            const requestData = {
                player_name: playerName.trim(),
                pgn_files: uploadedPaths,
                source: 'uploaded',
                min_games: minGames,
                include_survivorship: includeSurvivorship
            };

            const response = await fetch('/api/reports/generate-from-upload', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(requestData)
            });

            if (response.ok) {
                const data = await response.json();
                setCurrentJobId(data.job_id);
                setJobStatus({
                    job_id: data.job_id,
                    status: 'pending',
                    player_name: playerName,
                    progress_percentage: 0,
                    created_at: new Date().toISOString()
                });

                await notificationService.showNotification(
                    'Procesando Upload',
                    `Importando y analizando ${uploadFiles.length} archivos PGN para ${playerName}.`,
                    'info'
                );
            } else {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Error procesando archivos');
            }
        } catch (error) {
            setError(error.message);
            setIsGenerating(false);
        }
    };

    const checkJobStatus = async (jobId) => {
        try {
            const response = await fetch(`/api/reports/status/${jobId}`);
            if (response.ok) {
                const status = await response.json();
                setJobStatus(status);

                if (status.status === 'completed') {
                    setIsGenerating(false);
                    await notificationService.showNotification(
                        'Reporte Completado',
                        `El reporte de ${status.player_name} está listo para descargar.`,
                        'success'
                    );
                    loadRecentReports(); // Recargar lista
                } else if (status.status === 'failed') {
                    setIsGenerating(false);
                    setError(status.error_message || 'Error desconocido');
                    await notificationService.showNotification(
                        'Error en Reporte',
                        `Error generando reporte de ${status.player_name}: ${status.error_message}`,
                        'error'
                    );
                }
            }
        } catch (error) {
            console.error('Error verificando estado:', error);
        }
    };

    const downloadReport = async (jobId) => {
        try {
            const response = await fetch(`/api/reports/download/${jobId}`);
            if (response.ok) {
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const link = document.createElement('a');
                link.href = url;
                link.download = `reporte_${jobStatus?.player_name || 'jugador'}.md`;
                document.body.appendChild(link);
                link.click();
                link.remove();
                window.URL.revokeObjectURL(url);
            } else {
                setError('Error descargando reporte');
            }
        } catch (error) {
            setError('Error descargando reporte: ' + error.message);
        }
    };

    const downloadPdfReport = async (jobId) => {
        try {
            const response = await fetch(`/api/reports/download/${jobId}/pdf`);
            if (response.ok) {
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const link = document.createElement('a');
                link.href = url;
                link.download = `reporte_${jobStatus?.player_name || 'jugador'}.pdf`;
                document.body.appendChild(link);
                link.click();
                link.remove();
                window.URL.revokeObjectURL(url);
            } else {
                setError('Error descargando PDF');
            }
        } catch (error) {
            setError('Error descargando PDF: ' + error.message);
        }
    };

    const downloadStreakAnalysis = async (jobId) => {
        try {
            const response = await fetch(`/api/reports/download/${jobId}/streak-analysis`);
            if (response.ok) {
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const link = document.createElement('a');
                link.href = url;
                link.download = `analisis_rachas_${jobStatus?.player_name || 'jugador'}.md`;
                document.body.appendChild(link);
                link.click();
                link.remove();
                window.URL.revokeObjectURL(url);
            } else {
                setError('Error descargando análisis de rachas');
            }
        } catch (error) {
            setError('Error descargando análisis de rachas: ' + error.message);
        }
    };

    const downloadPgnGames = async (jobId) => {
        try {
            const response = await fetch(`/api/reports/download/${jobId}/pgn-games`);
            if (response.ok) {
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const link = document.createElement('a');
                link.href = url;
                link.download = `partidas_rachas_${jobStatus?.player_name || 'jugador'}.md`;
                document.body.appendChild(link);
                link.click();
                link.remove();
                window.URL.revokeObjectURL(url);
            } else {
                setError('Error descargando PGNs');
            }
        } catch (error) {
            setError('Error descargando PGNs: ' + error.message);
        }
    };

    const resetForm = () => {
        setPlayerName('');
        setUploadFiles([]);
        setIsGenerating(false);
        setCurrentJobId(null);
        setJobStatus(null);
        setError(null);
    };

    const getStatusIcon = (status) => {
        switch (status) {
            case 'completed':
                return <CheckCircleIcon sx={{ fontSize: 16, color: 'success.main' }} />;
            case 'failed':
                return <AlertCircleIcon sx={{ fontSize: 16, color: 'error.main' }} />;
            case 'processing':
                return <CircularProgress size={16} sx={{ color: 'primary.main' }} />;
            default:
                return <ClockIcon sx={{ fontSize: 16, color: 'warning.main' }} />;
        }
    };

    const getStatusColor = (status) => {
        switch (status) {
            case 'completed':
                return 'success';
            case 'failed':
                return 'error';
            case 'processing':
                return 'primary';
            default:
                return 'warning';
        }
    };

    return (
        <Box sx={{ maxWidth: 1200, margin: '0 auto', padding: 3 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 3 }}>
                <Typography variant="h4" component="h1" fontWeight="bold">
                    Reportes Personalizados
                </Typography>
                <Button variant="outlined" onClick={loadRecentReports}>
                    Actualizar Lista
                </Button>
            </Box>

            <Grid container spacing={3}>
                {/* Formulario de generación */}
                <Grid item xs={12} md={6}>
                    <Card>
                        <CardHeader>
                            <Typography variant="h6" component="div" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                <FileTextIcon />
                                Generar Nuevo Reporte
                            </Typography>
                        </CardHeader>
                        <CardContent sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                            {/* Toggle entre modes */}
                            <Box sx={{ display: 'flex', gap: 1 }}>
                                <Button
                                    variant={!isUploadMode ? "contained" : "outlined"}
                                    onClick={() => setIsUploadMode(false)}
                                    size="small"
                                >
                                    Jugador Existente
                                </Button>
                                <Button
                                    variant={isUploadMode ? "contained" : "outlined"}
                                    onClick={() => setIsUploadMode(true)}
                                    size="small"
                                    startIcon={<UploadIcon />}
                                >
                                    Subir PGNs
                                </Button>
                            </Box>

                            {/* Campos comunes */}
                            <Box>
                                <FormLabel>Nombre del Jugador</FormLabel>
                                <TextField
                                    fullWidth
                                    value={playerName}
                                    onChange={(e) => setPlayerName(e.target.value)}
                                    placeholder="Ej: Magnus_Carlsen, hikaru, etc."
                                    disabled={isGenerating}
                                    size="small"
                                />
                            </Box>

                            {/* Upload de archivos si está en modo upload */}
                            {isUploadMode && (
                                <Box>
                                    <FormLabel>Archivos PGN</FormLabel>
                                    <TextField
                                        type="file"
                                        fullWidth
                                        inputProps={{ multiple: true, accept: '.pgn' }}
                                        onChange={handleFileUpload}
                                        disabled={isGenerating}
                                        size="small"
                                    />
                                    {uploadFiles.length > 0 && (
                                        <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                                            {uploadFiles.length} archivo(s) seleccionado(s)
                                        </Typography>
                                    )}
                                </Box>
                            )}

                            {/* Opciones de análisis */}
                            <Grid container spacing={2}>
                                <Grid item xs={6}>
                                    <FormLabel>Mínimo de Partidas</FormLabel>
                                    <TextField
                                        type="number"
                                        fullWidth
                                        value={minGames}
                                        onChange={(e) => setMinGames(parseInt(e.target.value) || 50)}
                                        inputProps={{ min: 10, max: 5000 }}
                                        disabled={isGenerating}
                                        size="small"
                                    />
                                </Grid>

                                <Grid item xs={6}>
                                    <FormControl fullWidth size="small">
                                        <InputLabel>Formato de Salida</InputLabel>
                                        <Select
                                            value={outputFormat}
                                            onChange={(e) => setOutputFormat(e.target.value)}
                                            disabled={isGenerating}
                                            label="Formato de Salida"
                                        >
                                            <MenuItem value="markdown">Markdown (.md)</MenuItem>
                                            <MenuItem value="pdf">PDF (.pdf)</MenuItem>
                                        </Select>
                                    </FormControl>
                                </Grid>
                            </Grid>

                            {/* Opciones adicionales */}
                            <Box>
                                <Typography variant="subtitle2" color="text.secondary" sx={{ mt: 2, mb: 1 }}>
                                    Opciones de Análisis
                                </Typography>

                                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                                    <FormControlLabel
                                        control={
                                            <Checkbox
                                                checked={includeSurvivorship}
                                                onChange={(e) => setIncludeSurvivorship(e.target.checked)}
                                                disabled={isGenerating}
                                            />
                                        }
                                        label="Incluir Análisis de Survivorship Bias"
                                    />

                                    <FormControlLabel
                                        control={
                                            <Checkbox
                                                checked={includeStreakAnalysis}
                                                onChange={(e) => setIncludeStreakAnalysis(e.target.checked)}
                                                disabled={isGenerating}
                                            />
                                        }
                                        label="🔥 Incluir Análisis Detallado de Rachas de Errores"
                                    />

                                    <FormControlLabel
                                        control={
                                            <Checkbox
                                                checked={includePgnGames}
                                                onChange={(e) => setIncludePgnGames(e.target.checked)}
                                                disabled={isGenerating}
                                            />
                                        }
                                        label="🎮 Incluir PGNs de Partidas con Rachas"
                                    />

                                    <FormControlLabel
                                        control={
                                            <Checkbox
                                                checked={generatePdf}
                                                onChange={(e) => setGeneratePdf(e.target.checked)}
                                                disabled={isGenerating}
                                            />
                                        }
                                        label="📄 Generar PDF Automáticamente"
                                    />
                                </Box>
                            </Box>

                            {/* Botón de generación */}
                            <Button
                                onClick={isUploadMode ? generateReportFromUpload : generateReportFromExisting}
                                disabled={isGenerating || !playerName.trim()}
                                variant="contained"
                                fullWidth
                                startIcon={isGenerating ? <CircularProgress size={20} color="inherit" /> : null}
                            >
                                {isGenerating ?
                                    'Generando...' :
                                    `Generar Reporte ${isUploadMode ? 'desde Upload' : 'Existente'}`
                                }
                            </Button>

                            {/* Mostrar error */}
                            {error && (
                                <Alert severity="error" icon={<AlertCircleIcon />}>
                                    {error}
                                </Alert>
                            )}
                        </CardContent>
                    </Card>
                </Grid>

                {/* Estado del job actual */}
                {jobStatus && (
                    <Grid item xs={12} md={6}>
                        <Card>
                            <CardHeader>
                                <Typography variant="h6" component="div" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                    {getStatusIcon(jobStatus.status)}
                                    Estado del Reporte
                                </Typography>
                            </CardHeader>
                            <CardContent sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                                <Box>
                                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                                        <Typography variant="body1" fontWeight="medium">
                                            {jobStatus.player_name}
                                        </Typography>
                                        <Chip
                                            label={jobStatus.status}
                                            color={getStatusColor(jobStatus.status)}
                                            size="small"
                                        />
                                    </Box>

                                    {jobStatus.progress_percentage > 0 && (
                                        <LinearProgress
                                            variant="determinate"
                                            value={jobStatus.progress_percentage}
                                            sx={{ mb: 1 }}
                                        />
                                    )}

                                    <Typography variant="body2" color="text.secondary">
                                        Iniciado: {new Date(jobStatus.created_at).toLocaleString()}
                                    </Typography>

                                    {jobStatus.status === 'completed' && (
                                        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1, mt: 2 }}>
                                            <Grid container spacing={1}>
                                                <Grid item xs={6}>
                                                    <Button
                                                        onClick={() => downloadReport(jobStatus.job_id)}
                                                        size="small"
                                                        variant="outlined"
                                                        fullWidth
                                                        startIcon={<DownloadIcon />}
                                                    >
                                                        Markdown
                                                    </Button>
                                                </Grid>

                                                {jobStatus.pdf_report_path && (
                                                    <Grid item xs={6}>
                                                        <Button
                                                            onClick={() => downloadPdfReport(jobStatus.job_id)}
                                                            size="small"
                                                            variant="outlined"
                                                            fullWidth
                                                            startIcon={<FileTextIcon />}
                                                        >
                                                            PDF
                                                        </Button>
                                                    </Grid>
                                                )}
                                            </Grid>

                                            {jobStatus.streak_analysis_path && (
                                                <Button
                                                    onClick={() => downloadStreakAnalysis(jobStatus.job_id)}
                                                    size="small"
                                                    variant="outlined"
                                                    fullWidth
                                                >
                                                    🔥 Análisis de Rachas
                                                </Button>
                                            )}

                                            {jobStatus.pgn_games_path && (
                                                <Button
                                                    onClick={() => downloadPgnGames(jobStatus.job_id)}
                                                    size="small"
                                                    variant="outlined"
                                                    fullWidth
                                                >
                                                    🎮 PGNs de Partidas
                                                </Button>
                                            )}

                                            {/* Resumen del análisis */}
                                            {jobStatus.analysis_summary && (
                                                <Box sx={{ mt: 2, p: 2, bgcolor: 'grey.50', borderRadius: 1, border: '1px solid', borderColor: 'grey.200' }}>
                                                    <Typography variant="subtitle2" fontWeight="medium" sx={{ mb: 1 }}>
                                                        📊 Resumen del Análisis
                                                    </Typography>
                                                    {jobStatus.analysis_summary.max_error_streak && (
                                                        <Typography variant="body2">
                                                            🔥 Racha máxima: {jobStatus.analysis_summary.max_error_streak} errores
                                                        </Typography>
                                                    )}
                                                    {jobStatus.analysis_summary.total_streaks && (
                                                        <Typography variant="body2">
                                                            📈 Total de rachas: {jobStatus.analysis_summary.total_streaks}
                                                        </Typography>
                                                    )}
                                                    <Typography variant="body2">
                                                        ✅ Análisis completados: {jobStatus.analysis_summary.analyses_completed?.join(', ')}
                                                    </Typography>
                                                </Box>
                                            )}
                                        </Box>
                                    )}

                                    {jobStatus.status === 'failed' && (
                                        <Alert severity="error" sx={{ mt: 2 }}>
                                            {jobStatus.error_message}
                                        </Alert>
                                    )}
                                </Box>

                                <Button variant="outlined" onClick={resetForm} fullWidth>
                                    Nuevo Reporte
                                </Button>
                            </CardContent>
                        </Card>
                    </Grid>
                )}
            </Grid>

            {/* Reportes recientes */}
            <Card sx={{ mt: 3 }}>
                <CardHeader>
                    <Typography variant="h6">Reportes Recientes</Typography>
                </CardHeader>
                <CardContent>
                    {loadingReports ? (
                        <Box sx={{ display: 'flex', justifyContent: 'center', p: 2 }}>
                            <CircularProgress />
                        </Box>
                    ) : recentReports.length > 0 ? (
                        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                            {recentReports.map((report) => (
                                <Box key={report.job_id} sx={{
                                    display: 'flex',
                                    alignItems: 'center',
                                    justifyContent: 'space-between',
                                    p: 2,
                                    border: '1px solid',
                                    borderColor: 'grey.200',
                                    borderRadius: 1
                                }}>
                                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                                        {getStatusIcon(report.status)}
                                        <Box>
                                            <Typography variant="body1" fontWeight="medium">
                                                {report.player_name}
                                            </Typography>
                                            <Typography variant="body2" color="text.secondary">
                                                {new Date(report.created_at).toLocaleDateString()}
                                            </Typography>
                                        </Box>
                                    </Box>

                                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                        <Chip
                                            label={report.status}
                                            color={getStatusColor(report.status)}
                                            size="small"
                                        />
                                        {report.status === 'completed' && (
                                            <Button
                                                size="small"
                                                variant="outlined"
                                                onClick={() => downloadReport(report.job_id)}
                                            >
                                                <DownloadIcon />
                                            </Button>
                                        )}
                                    </Box>
                                </Box>
                            ))}
                        </Box>
                    ) : (
                        <Box sx={{ textAlign: 'center', color: 'text.secondary', py: 4 }}>
                            <Typography>No hay reportes generados aún</Typography>
                        </Box>
                    )}
                </CardContent>
            </Card>
        </Box>
    );
};

export default PersonalizedReportsPage;