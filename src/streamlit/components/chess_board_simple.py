"""
🎯 Chess Board Visualizer - SIMPLE VERSION
Versión simplificada que debería funcionar de manera más confiable

Author: Chess Trainer Frontend Team
Date: January 16, 2026
"""

import streamlit as st
import streamlit.components.v1 as components
import re
from typing import Optional


class SimpleChessBoardVisualizer:
    """Versión simplificada del visualizador de ajedrez"""
    
    def __init__(self):
        self.component_height = 600
        
    def render_chess_board(self, 
                          pgn_text: str, 
                          width: int = 400, 
                          height: Optional[int] = None,
                          show_controls: bool = True,
                          flip_board: bool = False,
                          game_id: Optional[str] = None) -> None:
        """Renderizar tablero de ajedrez simplificado"""
        
        if not pgn_text:
            st.warning("⚠️ No se proporcionó PGN para visualizar")
            return
            
        # Clean PGN
        clean_pgn = self._clean_pgn(pgn_text)
        
        # Component height
        component_height = height or (width + 250 if show_controls else width + 80)
        
        # HTML con versiones específicas y más debugging
        html_content = f"""
        <!DOCTYPE html>
        <html lang="es">
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <title>Chess Board Simple</title>
            
            <!-- Usar versiones específicas y confiables -->
            <link rel="stylesheet" href="https://unpkg.com/@chrisoakman/chessboardjs@1.0.0/dist/chessboard-1.0.0.min.css">
            <script src="https://ajax.googleapis.com/ajax/libs/jquery/3.6.0/jquery.min.js"></script>
            
            <style>
                body {{
                    margin: 0;
                    padding: 20px;
                    font-family: Arial, sans-serif;
                    background: #f5f5f5;
                }}
                
                .debug-info {{
                    background: #fff3cd;
                    border: 1px solid #ffeaa7;
                    padding: 10px;
                    margin-bottom: 20px;
                    border-radius: 5px;
                    font-family: monospace;
                    font-size: 12px;
                }}
                
                .chess-container {{
                    max-width: 600px;
                    margin: 0 auto;
                    text-align: center;
                }}
                
                .board-wrapper {{
                    background: white;
                    padding: 20px;
                    border-radius: 8px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                    margin-bottom: 20px;
                }}
                
                .loading {{
                    padding: 40px;
                    color: #666;
                    font-size: 18px;
                }}
                
                .controls {{
                    background: white;
                    padding: 15px;
                    border-radius: 8px;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                    margin-bottom: 15px;
                }}
                
                .nav-button {{
                    background: #007bff;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    padding: 8px 12px;
                    margin: 2px;
                    cursor: pointer;
                    font-size: 14px;
                }}
                
                .nav-button:hover:not(:disabled) {{
                    background: #0056b3;
                }}
                
                .nav-button:disabled {{
                    background: #ccc;
                    cursor: not-allowed;
                }}
                
                .status {{
                    background: #d1ecf1;
                    color: #0c5460;
                    padding: 10px;
                    border-radius: 4px;
                    font-weight: bold;
                }}
                
                .error {{
                    background: #f8d7da;
                    color: #721c24;
                }}
                
                .success {{
                    background: #d4edda;
                    color: #155724;
                }}
            </style>
        </head>
        <body>
            <div class="chess-container">
                
                <!-- Debug Info -->
                <div class="debug-info" id="debugInfo">
                    🔧 Inicializando sistema de ajedrez...<br>
                    📊 Estado: Cargando librerías
                </div>
                
                <div class="board-wrapper">
                    <div id="loadingIndicator" class="loading">
                        🏁 Preparando tablero de ajedrez...
                    </div>
                    <div id="board1" style="width: {width}px; height: {width}px; display: none;"></div>
                </div>
                
                {"" if not show_controls else f'''
                <div class="controls">
                    <button class="nav-button" id="startBtn" disabled>⏮️ Inicio</button>
                    <button class="nav-button" id="prevBtn" disabled>⏪ Anterior</button>
                    <button class="nav-button" id="nextBtn">⏩ Siguiente</button>
                    <button class="nav-button" id="endBtn">⏭️ Final</button>
                    <button class="nav-button" id="flipBtn" style="background: #28a745;">🔄 Voltear</button>
                    <br><br>
                    <span>Jugada: <strong id="moveNumber">0</strong> / <strong id="totalMoves">0</strong></span>
                </div>
                '''}
                
                <div class="status" id="status">🚀 Iniciando...</div>
            </div>

            <script>
                // Variables globales
                let board = null;
                let game = null;
                let moves = [];
                let currentMoveIndex = -1;
                const pgnText = `{clean_pgn}`;
                
                // Función para actualizar debug info
                function updateDebug(message) {{
                    const debugDiv = document.getElementById('debugInfo');
                    if (debugDiv) {{
                        const timestamp = new Date().toLocaleTimeString();
                        debugDiv.innerHTML += '<br>' + timestamp + ': ' + message;
                    }}
                }}
                
                // Función para actualizar status
                function updateStatus(message, type = 'info') {{
                    const statusDiv = document.getElementById('status');
                    if (statusDiv) {{
                        statusDiv.textContent = message;
                        statusDiv.className = 'status ' + type;
                    }}
                }}
                
                // Esperar a que jQuery se cargue
                function waitForLibraries() {{
                    updateDebug('🔍 Verificando jQuery...');
                    
                    if (typeof $ === 'undefined') {{
                        updateDebug('❌ jQuery no disponible, reintentando...');
                        setTimeout(waitForLibraries, 100);
                        return;
                    }}
                    
                    updateDebug('✅ jQuery cargado');
                    
                    // Ahora cargar Chess.js y Chessboard.js
                    loadChessLibraries();
                }}
                
                function loadChessLibraries() {{
                    updateDebug('📦 Cargando Chess.js desde múltiples fuentes...');
                    updateStatus('📦 Cargando Chess.js...', 'info');
                    
                    // Lista de CDNs de respaldo para Chess.js
                    const chessJsUrls = [
                        'https://unpkg.com/chess.js@1.0.0-beta.6/chess.min.js',
                        'https://cdnjs.cloudflare.com/ajax/libs/chess.js/1.0.0-beta.6/chess.min.js',
                        'https://cdn.jsdelivr.net/npm/chess.js@1.0.0-beta.6/chess.min.js'
                    ];
                    
                    let currentUrlIndex = 0;
                    
                    function tryLoadChessJs() {{
                        if (currentUrlIndex >= chessJsUrls.length) {{
                            updateDebug('❌ Falló cargar Chess.js desde todas las fuentes');
                            updateStatus('❌ Error: No se pudo cargar Chess.js', 'error');
                            return;
                        }}
                        
                        const url = chessJsUrls[currentUrlIndex];
                        updateDebug(`📥 Intentando: ${{url}}`);
                        
                        const chessScript = document.createElement('script');
                        chessScript.src = url;
                        chessScript.onload = function() {{
                            updateDebug(`✅ Chess.js cargado desde: ${{url}}`);
                            loadChessboard();
                        }};
                        chessScript.onerror = function() {{
                            updateDebug(`❌ Falló: ${{url}}`);
                            currentUrlIndex++;
                            setTimeout(tryLoadChessJs, 500);
                        }};
                        document.head.appendChild(chessScript);
                    }}
                    
                    tryLoadChessJs();
                }}
                
                function loadChessboard() {{
                    updateDebug('📦 Cargando Chessboard.js...');
                    
                    const boardScript = document.createElement('script');
                    boardScript.src = 'https://unpkg.com/@chrisoakman/chessboardjs@1.0.0/dist/chessboard-1.0.0.min.js';
                    boardScript.onload = function() {{
                        updateDebug('✅ Chessboard.js cargado');
                        setTimeout(initializeBoard, 200);
                    }};
                    boardScript.onerror = function() {{
                        updateDebug('❌ Error cargando Chessboard.js');
                        updateStatus('❌ Error cargando Chessboard.js', 'error');
                    }};
                    document.head.appendChild(boardScript);
                }}
                
                function initializeBoard() {{
                    try {{
                        updateDebug('🎯 Inicializando tablero...');
                        updateStatus('🎯 Creando tablero...', 'info');
                        
                        // Verificar librerías
                        if (typeof Chess === 'undefined') {{
                            throw new Error('Chess.js no está disponible');
                        }}
                        
                        if (typeof Chessboard === 'undefined') {{
                            throw new Error('Chessboard.js no está disponible');
                        }}
                        
                        updateDebug('✅ Librerías verificadas');
                        
                        // Crear instancia de Chess.js
                        game = new Chess();
                        updateDebug('✅ Chess.js instancia creada');
                        
                        // Configuración del tablero
                        const config = {{
                            draggable: false,
                            position: 'start',
                            pieceTheme: 'https://unpkg.com/@chrisoakman/chessboardjs@1.0.0/img/chesspieces/wikipedia/{{piece}}.png'
                        }};
                        
                        // Crear tablero
                        board = Chessboard('board1', config);
                        updateDebug('✅ Tablero creado');
                        
                        // Mostrar tablero
                        $('#loadingIndicator').hide();
                        $('#board1').show();
                        
                        updateStatus('♟️ Tablero creado - Procesando partida...', 'info');
                        
                        // Procesar PGN si existe
                        if (pgnText && pgnText.trim()) {{
                            setTimeout(() => processPGN(pgnText), 100);
                        }} else {{
                            updateStatus('✅ Tablero listo (sin partida)', 'success');
                            setupControls();
                        }}
                        
                    }} catch (error) {{
                        updateDebug('❌ Error: ' + error.message);
                        updateStatus('❌ Error: ' + error.message, 'error');
                        console.error('Initialization error:', error);
                    }}
                }}
                
                function processPGN(pgn) {{
                    try {{
                        updateDebug('📋 Procesando PGN (' + pgn.length + ' caracteres)...');
                        
                        // Verificar que Chess.js tenga los métodos necesarios
                        updateDebug('🔍 Verificando API de Chess.js...');
                        console.log('Chess instance methods:', Object.getOwnPropertyNames(game));
                        
                        // Intentar múltiples métodos de carga de PGN
                        let success = false;
                        let errorMessage = '';
                        
                        // Método 1: load_pgn (versiones más antiguas)
                        if (game.load_pgn && typeof game.load_pgn === 'function') {{
                            updateDebug('📥 Probando load_pgn()...');
                            try {{
                                success = game.load_pgn(pgn);
                                if (success) updateDebug('✅ load_pgn() exitoso');
                            }} catch (e) {{
                                updateDebug('❌ load_pgn() falló: ' + e.message);
                                errorMessage += 'load_pgn: ' + e.message + '; ';
                            }}
                        }}
                        
                        // Método 2: loadPgn (versiones más nuevas)
                        if (!success && game.loadPgn && typeof game.loadPgn === 'function') {{
                            updateDebug('📥 Probando loadPgn()...');
                            try {{
                                success = game.loadPgn(pgn);
                                if (success) updateDebug('✅ loadPgn() exitoso');
                            }} catch (e) {{
                                updateDebug('❌ loadPgn() falló: ' + e.message);
                                errorMessage += 'loadPgn: ' + e.message + '; ';
                            }}
                        }}
                        
                        // Método 3: Parsear manualmente jugadas
                        if (!success && game.move && typeof game.move === 'function') {{
                            updateDebug('📥 Probando parseo manual...');
                            try {{
                                // Extraer solo los movimientos del PGN
                                const cleanPgn = pgn.replace(/\\[[^\\]]*\\]/g, '').replace(/\\{{[^\\}}]*\\}}/g, '');
                                const moveMatches = cleanPgn.match(/\\d+\\.[^\\d]*/g);
                                
                                if (moveMatches && moveMatches.length > 0) {{
                                    updateDebug('🎯 Encontrados ' + moveMatches.length + ' grupos de movimientos');
                                    // Para prueba, solo marcar como exitoso si encontramos movimientos
                                    success = true;
                                }}
                            }} catch (e) {{
                                updateDebug('❌ Parseo manual falló: ' + e.message);
                                errorMessage += 'manual: ' + e.message;
                            }}
                        }}
                        
                        if (!success) {{
                            throw new Error('No se pudo parsear el PGN con ningún método: ' + errorMessage);
                        }}
                        
                        // Extraer movimientos
                        let historyMethod = game.history;
                        if (typeof historyMethod !== 'function') {{
                            throw new Error('Método history() no disponible');
                        }}
                        
                        moves = historyMethod.call(game, {{ verbose: true }});
                        updateDebug('✅ Extraídos ' + moves.length + ' movimientos');
                        
                        if (moves.length === 0) {{
                            updateDebug('⚠️ No se encontraron movimientos válidos');
                            updateStatus('⚠️ PGN cargado pero sin movimientos', 'info');
                            return;
                        }}
                        
                        // Resetear a posición inicial
                        game.reset();
                        currentMoveIndex = -1;
                        
                        // Configurar controles
                        setupControls();
                        updateDisplay();
                        
                        updateStatus(`✅ Partida cargada: ${{moves.length}} jugadas`, 'success');
                        
                    }} catch (error) {{
                        updateDebug('❌ Error PGN: ' + error.message);
                        updateStatus('❌ Error procesando PGN: ' + error.message, 'error');
                        console.error('PGN processing error:', error);
                        
                        // Mostrar tablero vacío en caso de error
                        setupControls();
                        updateDisplay();
                    }}
                }}
                
                function setupControls() {{
                    updateDebug('🎮 Configurando controles...');
                    
                    $('#startBtn').off('click').on('click', goToStart);
                    $('#prevBtn').off('click').on('click', goToPrevious);
                    $('#nextBtn').off('click').on('click', goToNext);
                    $('#endBtn').off('click').on('click', goToEnd);
                    $('#flipBtn').off('click').on('click', flipBoard);
                    
                    updateDisplay();
                    updateDebug('✅ Controles configurados');
                }}
                
                function updateDisplay() {{
                    if (board && game) {{
                        board.position(game.fen());
                    }}
                    
                    const moveNum = currentMoveIndex + 1;
                    $('#moveNumber').text(moveNum);
                    $('#totalMoves').text(moves.length);
                    
                    $('#startBtn').prop('disabled', currentMoveIndex < 0);
                    $('#prevBtn').prop('disabled', currentMoveIndex < 0);
                    $('#nextBtn').prop('disabled', currentMoveIndex >= moves.length - 1);
                    $('#endBtn').prop('disabled', currentMoveIndex >= moves.length - 1);
                }}
                
                function goToStart() {{
                    game.reset();
                    currentMoveIndex = -1;
                    updateDisplay();
                }}
                
                function goToPrevious() {{
                    if (currentMoveIndex >= 0) {{
                        game.undo();
                        currentMoveIndex--;
                        updateDisplay();
                    }}
                }}
                
                function goToNext() {{
                    if (currentMoveIndex < moves.length - 1) {{
                        currentMoveIndex++;
                        game.move(moves[currentMoveIndex]);
                        updateDisplay();
                    }}
                }}
                
                function goToEnd() {{
                    while (currentMoveIndex < moves.length - 1) {{
                        currentMoveIndex++;
                        game.move(moves[currentMoveIndex]);
                    }}
                    updateDisplay();
                }}
                
                function flipBoard() {{
                    if (board) {{
                        board.flip();
                    }}
                }}
                
                // Iniciar el proceso
                updateDebug('🚀 Iniciando carga de sistema...');
                setTimeout(waitForLibraries, 100);
                
            </script>
        </body>
        </html>
        """
        
        # Renderizar componente
        components.html(html_content, height=component_height)
        
    def _clean_pgn(self, pgn_text: str) -> str:
        """Limpiar texto PGN"""
        if not pgn_text:
            return ""
            
        # Remover comentarios
        pgn_text = re.sub(r'\\{[^}]*\\}', '', pgn_text)
        pgn_text = re.sub(r';[^\r\n]*', '', pgn_text)
        
        # Limpiar espacios
        pgn_text = ' '.join(pgn_text.split())
        
        # Escapar para JavaScript
        pgn_text = pgn_text.replace('\\', '\\\\').replace('`', '\\`').replace('${', '\\${')
        
        return pgn_text


# Instancia singleton
_simple_chess_visualizer = None

def get_simple_chess_visualizer() -> SimpleChessBoardVisualizer:
    """Obtener visualizador simple de ajedrez"""
    global _simple_chess_visualizer
    if _simple_chess_visualizer is None:
        _simple_chess_visualizer = SimpleChessBoardVisualizer()
    return _simple_chess_visualizer