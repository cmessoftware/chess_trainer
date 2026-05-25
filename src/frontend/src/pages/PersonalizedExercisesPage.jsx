import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Textarea } from '../components/ui/textarea';
import { Alert, AlertDescription } from '../components/ui/alert';
import { Badge } from '../components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import {
    Upload,
    Brain,
    Target,
    TrendingUp,
    Download,
    ExternalLink,
    CheckCircle,
    AlertTriangle,
    Clock,
    Zap
} from 'lucide-react';
import ChessBoard from '../components/chess/ChessBoard';
import { exercisesService } from '../services/exercisesService';

const PersonalizedExercisesPage = () => {
    const [playerName, setPlayerName] = useState('');
    const [pgnContent, setPgnContent] = useState('');
    const [analysisResult, setAnalysisResult] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [activeTab, setActiveTab] = useState('upload');

    const handleFileUpload = (event) => {
        const file = event.target.files[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = (e) => {
                setPgnContent(e.target.result);
            };
            reader.readAsText(file);
        }
    };

    const handleAnalyzePlayer = async () => {
        if (!playerName.trim()) {
            setError('Por favor ingresa el nombre del jugador');
            return;
        }

        setLoading(true);
        setError('');

        try {
            const response = await exercisesService.analyzePlayer({
                player_name: playerName,
                pgn_content: pgnContent || null,
                analysis_type: ['error_label', 'streaks', 'player_type']
            });

            setAnalysisResult(response);
            setActiveTab('results');
        } catch (err) {
            setError(`Error en el análisis: ${err.message}`);
        } finally {
            setLoading(false);
        }
    };

    const handleExportToLichess = async () => {
        try {
            const exportData = await exercisesService.exportToLichess(playerName);

            // Crear descarga automática del PGN
            const blob = new Blob([exportData.pgn_content], { type: 'text/plain' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `ejercicios_${playerName}.pgn`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);

            // Mostrar instrucciones
            alert(`PGN descargado exitosamente!\n\nPara importar en Lichess:\n1. Ve a lichess.org/study/new\n2. Selecciona "Import from PGN"\n3. Sube el archivo descargado\n4. ¡Disfruta tus ejercicios personalizados!`);

        } catch (err) {
            setError(`Error exportando: ${err.message}`);
        }
    };

    const getPriorityColor = (priority) => {
        switch (priority) {
            case 'critical': return 'bg-red-500 text-white';
            case 'high': return 'bg-orange-500 text-white';
            case 'medium': return 'bg-blue-500 text-white';
            default: return 'bg-gray-500 text-white';
        }
    };

    const getDifficultyIcon = (difficulty) => {
        switch (difficulty) {
            case 'beginner': return <Zap className="w-4 h-4 text-green-500" />;
            case 'intermediate': return <Target className="w-4 h-4 text-yellow-500" />;
            case 'advanced': return <Brain className="w-4 h-4 text-red-500" />;
            default: return <Clock className="w-4 h-4 text-gray-500" />;
        }
    };

    return (
        <div className="container mx-auto px-4 py-8 max-w-7xl">
            <div className="mb-8">
                <h1 className="text-3xl font-bold text-gray-900 mb-2">
                    🎯 Ejercicios Personalizados
                </h1>
                <p className="text-gray-600">
                    Analiza tus partidas con IA y genera ejercicios específicos para mejorar tus debilidades
                </p>
            </div>

            <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
                <TabsList className="grid w-full grid-cols-4">
                    <TabsTrigger value="upload" className="flex items-center gap-2">
                        <Upload className="w-4 h-4" />
                        Subir PGN
                    </TabsTrigger>
                    <TabsTrigger value="analyze" className="flex items-center gap-2">
                        <Brain className="w-4 h-4" />
                        Analizar
                    </TabsTrigger>
                    <TabsTrigger value="results" className="flex items-center gap-2" disabled={!analysisResult}>
                        <TrendingUp className="w-4 h-4" />
                        Resultados
                    </TabsTrigger>
                    <TabsTrigger value="export" className="flex items-center gap-2" disabled={!analysisResult}>
                        <Download className="w-4 h-4" />
                        Exportar
                    </TabsTrigger>
                </TabsList>

                {/* Tab 1: Upload PGN */}
                <TabsContent value="upload" className="space-y-6">
                    <Card>
                        <CardHeader>
                            <CardTitle className="flex items-center gap-2">
                                <Upload className="w-5 h-5" />
                                Subir Archivo PGN
                            </CardTitle>
                        </CardHeader>
                        <CardContent className="space-y-4">
                            <div>
                                <label className="block text-sm font-medium mb-2">
                                    Nombre del Jugador
                                </label>
                                <Input
                                    type="text"
                                    placeholder="Ej: Th3Hound, cmess1315, etc."
                                    value={playerName}
                                    onChange={(e) => setPlayerName(e.target.value)}
                                    className="w-full"
                                />
                            </div>

                            <div>
                                <label className="block text-sm font-medium mb-2">
                                    Archivo PGN (Opcional)
                                </label>
                                <Input
                                    type="file"
                                    accept=".pgn"
                                    onChange={handleFileUpload}
                                    className="w-full"
                                />
                                <p className="text-sm text-gray-500 mt-1">
                                    Si no subes un archivo, se analizarán las partidas existentes en la base de datos
                                </p>
                            </div>

                            {pgnContent && (
                                <div>
                                    <label className="block text-sm font-medium mb-2">
                                        Contenido PGN
                                    </label>
                                    <Textarea
                                        value={pgnContent.substring(0, 500) + (pgnContent.length > 500 ? '...' : '')}
                                        readOnly
                                        className="w-full h-24"
                                    />
                                    <p className="text-sm text-gray-500 mt-1">
                                        {pgnContent.length} caracteres cargados
                                    </p>
                                </div>
                            )}

                            <Button
                                onClick={() => setActiveTab('analyze')}
                                className="w-full"
                                disabled={!playerName.trim()}
                            >
                                Continuar al Análisis
                            </Button>
                        </CardContent>
                    </Card>
                </TabsContent>

                {/* Tab 2: Analyze */}
                <TabsContent value="analyze" className="space-y-6">
                    <Card>
                        <CardHeader>
                            <CardTitle className="flex items-center gap-2">
                                <Brain className="w-5 h-5" />
                                Análisis con Inteligencia Artificial
                            </CardTitle>
                        </CardHeader>
                        <CardContent className="space-y-4">
                            <div className="bg-blue-50 p-4 rounded-lg">
                                <h3 className="font-semibold text-blue-900 mb-2">
                                    ¿Qué analizaremos?
                                </h3>
                                <ul className="space-y-1 text-blue-800">
                                    <li>✅ <strong>Calidad de movimientos:</strong> Good, Inaccuracy, Mistake, Blunder</li>
                                    <li>✅ <strong>Rachas de errores:</strong> Patrones de errores consecutivos</li>
                                    <li>✅ <strong>Nivel de juego:</strong> Comparación con diferentes niveles ELO</li>
                                    <li>✅ <strong>Debilidades específicas:</strong> Áreas de mejora identificadas por ML</li>
                                </ul>
                            </div>

                            <div className="bg-yellow-50 p-4 rounded-lg">
                                <h4 className="font-semibold text-yellow-900 mb-2">Proceso de Análisis:</h4>
                                <ol className="list-decimal list-inside space-y-1 text-yellow-800">
                                    <li>Cargar partidas desde base de datos o PGN subido</li>
                                    <li>Generar features con motor Stockfish</li>
                                    <li>Ejecutar modelos de Machine Learning</li>
                                    <li>Identificar patrones y debilidades específicas</li>
                                    <li>Generar ejercicios personalizados para mejora</li>
                                </ol>
                            </div>

                            <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                                <div>
                                    <p className="font-medium">Jugador: {playerName}</p>
                                    <p className="text-sm text-gray-600">
                                        {pgnContent ? 'Con PGN personalizado' : 'Usando datos existentes'}
                                    </p>
                                </div>
                                <Button
                                    onClick={handleAnalyzePlayer}
                                    disabled={loading || !playerName.trim()}
                                    className="min-w-32"
                                >
                                    {loading ? 'Analizando...' : 'Iniciar Análisis'}
                                </Button>
                            </div>

                            {loading && (
                                <div className="text-center py-8">
                                    <div className="animate-spin w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full mx-auto mb-4"></div>
                                    <p className="text-gray-600">Ejecutando análisis con IA... Esto puede tomar 1-2 minutos</p>
                                </div>
                            )}
                        </CardContent>
                    </Card>
                </TabsContent>

                {/* Tab 3: Results */}
                <TabsContent value="results" className="space-y-6">
                    {analysisResult && (
                        <>
                            {/* Resumen del Análisis */}
                            <Card>
                                <CardHeader>
                                    <CardTitle className="flex items-center gap-2">
                                        <TrendingUp className="w-5 h-5" />
                                        Resumen del Análisis - {analysisResult.player_name}
                                    </CardTitle>
                                </CardHeader>
                                <CardContent>
                                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                                        <div className="text-center p-4 bg-green-50 rounded-lg">
                                            <div className="text-2xl font-bold text-green-600">
                                                {(analysisResult.analysis_summary.good_rate * 100).toFixed(1)}%
                                            </div>
                                            <div className="text-sm text-green-800">Movimientos Buenos</div>
                                        </div>
                                        <div className="text-center p-4 bg-red-50 rounded-lg">
                                            <div className="text-2xl font-bold text-red-600">
                                                {(analysisResult.analysis_summary.error_rate * 100).toFixed(1)}%
                                            </div>
                                            <div className="text-sm text-red-800">Tasa de Errores</div>
                                        </div>
                                        <div className="text-center p-4 bg-orange-50 rounded-lg">
                                            <div className="text-2xl font-bold text-orange-600">
                                                {analysisResult.analysis_summary.max_error_streak}
                                            </div>
                                            <div className="text-sm text-orange-800">Máxima Racha Errores</div>
                                        </div>
                                        <div className="text-center p-4 bg-blue-50 rounded-lg">
                                            <div className="text-2xl font-bold text-blue-600">
                                                {(analysisResult.analysis_summary.model_accuracy * 100).toFixed(0)}%
                                            </div>
                                            <div className="text-sm text-blue-800">Precisión del Modelo</div>
                                        </div>
                                    </div>
                                </CardContent>
                            </Card>

                            {/* Ejercicios Personalizados */}
                            <Card>
                                <CardHeader>
                                    <CardTitle className="flex items-center gap-2">
                                        <Target className="w-5 h-5" />
                                        Ejercicios Personalizados ({analysisResult.recommended_exercises.length})
                                    </CardTitle>
                                </CardHeader>
                                <CardContent>
                                    <div className="grid gap-4">
                                        {analysisResult.recommended_exercises.map((exercise, index) => (
                                            <div key={index} className="border rounded-lg p-4 hover:shadow-md transition-shadow">
                                                <div className="flex items-start justify-between mb-3">
                                                    <div className="flex items-center gap-2">
                                                        {getDifficultyIcon(exercise.difficulty)}
                                                        <h3 className="font-semibold">{exercise.title}</h3>
                                                    </div>
                                                    <Badge className={`${getPriorityColor(exercise.difficulty)} text-xs`}>
                                                        {exercise.difficulty}
                                                    </Badge>
                                                </div>

                                                <p className="text-gray-600 mb-3">{exercise.description}</p>

                                                <div className="grid md:grid-cols-2 gap-4">
                                                    <div>
                                                        <div className="bg-gray-50 p-3 rounded text-sm">
                                                            <strong>Tipo:</strong> {exercise.pattern_type}<br />
                                                            <strong>Movimientos objetivo:</strong> {exercise.target_moves.join(', ')}<br />
                                                            <strong>Explicación:</strong> {exercise.explanation}
                                                        </div>
                                                    </div>

                                                    {exercise.fen_position && exercise.fen_position !== '8/8/8/8/8/8/8/8 w - - 0 1' && (
                                                        <div className="flex justify-center">
                                                            <ChessBoard
                                                                position={exercise.fen_position}
                                                                size={200}
                                                                readOnly={true}
                                                            />
                                                        </div>
                                                    )}
                                                </div>

                                                {exercise.lichess_study_url && (
                                                    <div className="mt-3 pt-3 border-t">
                                                        <a
                                                            href={exercise.lichess_study_url}
                                                            target="_blank"
                                                            rel="noopener noreferrer"
                                                            className="inline-flex items-center gap-2 text-blue-600 hover:text-blue-800"
                                                        >
                                                            <ExternalLink className="w-4 h-4" />
                                                            Practicar en Lichess
                                                        </a>
                                                    </div>
                                                )}
                                            </div>
                                        ))}
                                    </div>
                                </CardContent>
                            </Card>

                            {/* Plan de Estudio */}
                            <Card>
                                <CardHeader>
                                    <CardTitle className="flex items-center gap-2">
                                        <Clock className="w-5 h-5" />
                                        Plan de Estudio Personalizado
                                    </CardTitle>
                                </CardHeader>
                                <CardContent>
                                    <div className="grid md:grid-cols-2 gap-6">
                                        <div>
                                            <h4 className="font-semibold mb-3">Horario Diario Sugerido:</h4>
                                            <div className="space-y-2">
                                                <div className="flex justify-between p-2 bg-blue-50 rounded">
                                                    <span>Táctica:</span>
                                                    <span className="font-medium">{analysisResult.study_plan.daily_schedule.tactics_time} min</span>
                                                </div>
                                                <div className="flex justify-between p-2 bg-green-50 rounded">
                                                    <span>Análisis:</span>
                                                    <span className="font-medium">{analysisResult.study_plan.daily_schedule.analysis_time} min</span>
                                                </div>
                                                <div className="flex justify-between p-2 bg-purple-50 rounded">
                                                    <span>Patrones:</span>
                                                    <span className="font-medium">{analysisResult.study_plan.daily_schedule.pattern_practice} min</span>
                                                </div>
                                            </div>
                                        </div>

                                        <div>
                                            <h4 className="font-semibold mb-3">Metas Semanales:</h4>
                                            <ul className="space-y-2">
                                                {analysisResult.study_plan.weekly_goals.map((goal, index) => (
                                                    <li key={index} className="flex items-start gap-2">
                                                        <CheckCircle className="w-4 h-4 text-green-500 mt-0.5 flex-shrink-0" />
                                                        <span className="text-sm">{goal}</span>
                                                    </li>
                                                ))}
                                            </ul>
                                        </div>
                                    </div>
                                </CardContent>
                            </Card>

                            {/* Áreas Prioritarias */}
                            <Card>
                                <CardHeader>
                                    <CardTitle className="flex items-center gap-2">
                                        <AlertTriangle className="w-5 h-5" />
                                        Áreas Prioritarias de Mejora
                                    </CardTitle>
                                </CardHeader>
                                <CardContent>
                                    <div className="flex flex-wrap gap-2">
                                        {analysisResult.priority_areas.map((area, index) => (
                                            <Badge key={index} variant="outline" className="px-3 py-1">
                                                {area.replace('_', ' ').toUpperCase()}
                                            </Badge>
                                        ))}
                                    </div>
                                    <p className="text-sm text-gray-600 mt-3">
                                        Enfócate en estas áreas durante las próximas 2-3 semanas para obtener mejores resultados.
                                    </p>
                                </CardContent>
                            </Card>
                        </>
                    )}
                </TabsContent>

                {/* Tab 4: Export */}
                <TabsContent value="export" className="space-y-6">
                    <Card>
                        <CardHeader>
                            <CardTitle className="flex items-center gap-2">
                                <Download className="w-5 h-5" />
                                Exportar a Lichess
                            </CardTitle>
                        </CardHeader>
                        <CardContent className="space-y-4">
                            <div className="bg-green-50 p-4 rounded-lg">
                                <h3 className="font-semibold text-green-900 mb-2">
                                    🎯 Ejercicios Listos para Exportar
                                </h3>
                                <p className="text-green-800 mb-4">
                                    Tus ejercicios personalizados están listos para ser importados como un estudio privado en Lichess.
                                </p>

                                <div className="space-y-3">
                                    <div className="flex items-center justify-between p-3 bg-white rounded border">
                                        <div>
                                            <p className="font-medium">Estudio: "Ejercicios Personalizados - {analysisResult?.player_name}"</p>
                                            <p className="text-sm text-gray-600">
                                                {analysisResult?.recommended_exercises.length} ejercicios específicos
                                            </p>
                                        </div>
                                        <Button onClick={handleExportToLichess} className="ml-4">
                                            <Download className="w-4 h-4 mr-2" />
                                            Descargar PGN
                                        </Button>
                                    </div>
                                </div>
                            </div>

                            <div className="bg-blue-50 p-4 rounded-lg">
                                <h4 className="font-semibold text-blue-900 mb-2">Instrucciones de Importación:</h4>
                                <ol className="list-decimal list-inside space-y-1 text-blue-800">
                                    <li>Haz clic en "Descargar PGN" para obtener tu archivo</li>
                                    <li>Ve a <a href="https://lichess.org/study/new" target="_blank" rel="noopener noreferrer" className="underline hover:text-blue-600">lichess.org/study/new</a></li>
                                    <li>Selecciona "Import from PGN"</li>
                                    <li>Sube el archivo descargado</li>
                                    <li>Configura como "Private" o "Unlisted"</li>
                                    <li>¡Disfruta practicando tus ejercicios personalizados!</li>
                                </ol>
                            </div>

                            <div className="bg-yellow-50 p-4 rounded-lg">
                                <h4 className="font-semibold text-yellow-900 mb-2">💡 Consejos de Uso:</h4>
                                <ul className="space-y-1 text-yellow-800">
                                    <li>• Practica 10-15 minutos diariamente</li>
                                    <li>• Enfócate en las áreas marcadas como "críticas" primero</li>
                                    <li>• Re-analiza tus partidas cada 2-3 semanas para ver el progreso</li>
                                    <li>• Combina estos ejercicios con partidas reales de práctica</li>
                                </ul>
                            </div>

                            <Button
                                onClick={() => window.open('https://lichess.org/study/new', '_blank')}
                                variant="outline"
                                className="w-full"
                            >
                                <ExternalLink className="w-4 h-4 mr-2" />
                                Abrir Lichess Studies
                            </Button>
                        </CardContent>
                    </Card>
                </TabsContent>
            </Tabs>

            {/* Error Alert */}
            {error && (
                <Alert variant="destructive" className="mt-4">
                    <AlertTriangle className="h-4 w-4" />
                    <AlertDescription>{error}</AlertDescription>
                </Alert>
            )}
        </div>
    );
};

export default PersonalizedExercisesPage;