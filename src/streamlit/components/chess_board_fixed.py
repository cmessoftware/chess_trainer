"""
🎯 Chess Board Visualizer Component - FIXED VERSION
Interactive chess board with game navigation using Chess.js + Chessboard.js

Features:
- Interactive chess board display
- Move navigation (first, previous, next, last)
- PGN parsing and playback
- Ready for enhancements: arrows, highlighting, analysis
- Responsive design with modern UI

Author: Chess Trainer Frontend Team
Date: January 16, 2026
"""

import streamlit as st
import streamlit.components.v1 as components
import re
from typing import Optional, List, Dict, Any
import json


class ChessBoardVisualizer:
    """Chess board visualizer using Chess.js and Chessboard.js"""

    def __init__(self):
        self.component_height = 700

    def render_chess_board(
        self,
        pgn_text: str,
        width: int = 400,
        height: Optional[int] = None,
        show_controls: bool = True,
        flip_board: bool = False,
        game_id: Optional[str] = None,
    ) -> None:
        """
        Render interactive chess board with PGN navigation

        Args:
            pgn_text: PGN notation of the game
            width: Board width in pixels
            height: Component height (auto if None)
            show_controls: Show navigation controls
            flip_board: Show board from black's perspective
            game_id: Optional game identifier
        """

        if not pgn_text:
            st.warning("⚠️ No se proporcionó PGN para visualizar")
            return

        # Clean and prepare PGN
        clean_pgn = self._clean_pgn(pgn_text)

        # Calculate component height
        component_height = height or (width + 200 if show_controls else width + 80)

        # Generate HTML content
        html_content = f"""
        <!DOCTYPE html>
        <html lang="es">
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <title>Chess Board</title>
            
            <!-- Libraries with fallbacks -->
            <link rel="stylesheet" href="https://unpkg.com/@chrisoakman/chessboardjs@1.0.0/dist/chessboard-1.0.0.min.css">
            <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
            
            <!-- Chess.js with multiple fallbacks -->
            <script>
                // Try multiple CDNs for Chess.js
                const chessJsCdns = [
                    'https://unpkg.com/chess.js@1.0.0-beta.6/chess.min.js',
                    'https://cdnjs.cloudflare.com/ajax/libs/chess.js/1.0.0-beta.6/chess.min.js',
                    'https://cdn.jsdelivr.net/npm/chess.js@1.0.0-beta.6/chess.min.js'
                ];
                
                let chessJsIndex = 0;
                
                function loadChessJs() {{
                    if (chessJsIndex >= chessJsCdns.length) {{
                        console.error('Failed to load Chess.js from all CDNs');
                        return;
                    }}
                    
                    const script = document.createElement('script');
                    script.src = chessJsCdns[chessJsIndex];
                    script.onload = () => console.log('Chess.js loaded from:', chessJsCdns[chessJsIndex]);
                    script.onerror = () => {{
                        console.log('Failed to load from:', chessJsCdns[chessJsIndex]);
                        chessJsIndex++;
                        loadChessJs();
                    }};
                    document.head.appendChild(script);
                }}
                
                loadChessJs();
            </script>
            
            <script src="https://unpkg.com/@chrisoakman/chessboardjs@1.0.0/dist/chessboard-1.0.0.min.js"></script>
            
            <style>
                body {{
                    margin: 0;
                    padding: 20px;
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    background: #f8f9fa;
                }}
                
                .chess-container {{
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    gap: 20px;
                    max-width: 600px;
                    margin: 0 auto;
                }}
                
                .board-wrapper {{
                    background: white;
                    padding: 20px;
                    border-radius: 12px;
                    box-shadow: 0 4px 12px rgba(0,0,0,0.1);
                }}
                
                #board1 {{
                    margin: 0 auto;
                }}
                
                .controls {{
                    background: white;
                    padding: 15px;
                    border-radius: 12px;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    flex-wrap: wrap;
                    gap: 15px;
                    min-width: 400px;
                }}
                
                .nav-buttons {{
                    display: flex;
                    gap: 8px;
                }}
                
                .nav-button {{
                    background: #1976d2;
                    color: white;
                    border: none;
                    border-radius: 6px;
                    padding: 10px 15px;
                    cursor: pointer;
                    font-size: 14px;
                    font-weight: 500;
                    transition: all 0.2s;
                }}
                
                .nav-button:hover:not(:disabled) {{
                    background: #1565c0;
                    transform: translateY(-1px);
                }}
                
                .nav-button:disabled {{
                    background: #ccc;
                    cursor: not-allowed;
                    transform: none;
                }}
                
                .move-info {{
                    display: flex;
                    align-items: center;
                    gap: 15px;
                    font-size: 14px;
                    color: #5f6368;
                }}
                
                .current-move {{
                    font-weight: 600;
                    color: #1976d2;
                }}
                
                .status {{
                    background: #e3f2fd;
                    color: #1565c0;
                    padding: 10px 15px;
                    border-radius: 6px;
                    font-weight: 500;
                    text-align: center;
                }}
                
                .loading {{
                    text-align: center;
                    padding: 40px;
                    color: #666;
                    font-size: 18px;
                }}
            </style>
        </head>
        <body>
            <div class="chess-container">
                <div class="board-wrapper">
                    <div id="loadingIndicator" class="loading">
                        🏁 Cargando tablero de ajedrez...
                    </div>
                    <div id="board1" style="width: {width}px; display: none;"></div>
                </div>
                
                {"" if not show_controls else f'''
                <div class="controls">
                    <div class="nav-buttons">
                        <button class="nav-button" id="startBtn" disabled>⏮️ Inicio</button>
                        <button class="nav-button" id="prevBtn" disabled>⏪ Anterior</button>
                        <button class="nav-button" id="nextBtn">⏩ Siguiente</button>
                        <button class="nav-button" id="endBtn">⏭️ Final</button>
                    </div>
                    
                    <div class="move-info">
                        <span>Jugada: <span class="current-move" id="moveNumber">0</span></span>
                        <span>Total: <span class="current-move" id="totalMoves">0</span></span>
                    </div>
                    
                    <button class="nav-button" id="flipBtn" style="background: #4caf50;">🔄 Voltear</button>
                </div>
                '''}
                
                <div class="status" id="status">Inicializando...</div>
            </div>

            <script>
                // Global variables
                let board = null;
                let game = null;
                let moves = [];
                let currentMoveIndex = -1;
                
                // PGN data
                const pgnText = `{clean_pgn}`;
                
                // Wait for DOM and libraries
                $(document).ready(function() {{
                    console.log('=== CHESS BOARD DEBUG START ===');
                    
                    // Wait a bit for dynamic Chess.js loading
                    setTimeout(function() {{
                        console.log('jQuery loaded:', typeof $ !== 'undefined');
                        console.log('Chess.js loaded:', typeof Chess !== 'undefined');
                        console.log('Chessboard.js loaded:', typeof Chessboard !== 'undefined');
                        
                        // Check each library individually
                        if (typeof $ === 'undefined') {{
                            $('#status').text('❌ jQuery no cargado');
                            console.error('jQuery not loaded');
                            return;
                        }}
                        
                        if (typeof Chess === 'undefined') {{
                            $('#status').text('❌ Chess.js no cargado - Reintentando...');
                            console.error('Chess.js not loaded, retrying...');
                            // Retry after another delay
                            setTimeout(function() {{
                                if (typeof Chess !== 'undefined') {{
                                    $('#status').text('🔧 Chess.js cargado tardíamente');
                                    setTimeout(initializeChessBoard, 500);
                                }} else {{
                                    $('#status').text('❌ Chess.js falló definitivamente');
                                }}
                            }}, 2000);
                            return;
                        }}
                        
                        if (typeof Chessboard === 'undefined') {{
                            $('#status').text('❌ Chessboard.js no cargado');
                            console.error('Chessboard.js not loaded');
                            return;
                        }}
                        
                        console.log('All libraries loaded successfully!');
                        $('#status').text('🔧 Todas las librerías cargadas');
                        
                        // Small delay to ensure everything is ready
                        setTimeout(function() {{
                            initializeChessBoard();
                        }}, 100);
                        
                    }}, 1000); // Wait 1 second for dynamic loading
                }});
                
                function initializeChessBoard() {{
                    try {{
                        console.log('=== INITIALIZING CHESS BOARD ===');
                        $('#status').text('🔧 Configurando tablero...');
                        
                        // Create Chess.js instance with detailed logging
                        console.log('Creating Chess.js instance...');
                        game = new Chess();
                        console.log('Chess.js instance created:', game);
                        
                        // Board configuration
                        const config = {{
                            draggable: false,
                            position: 'start',
                            pieceTheme: 'https://unpkg.com/@chrisoakman/chessboardjs@1.0.0/img/chesspieces/wikipedia/{{piece}}.png',
                            orientation: '{'black' if flip_board else 'white'}',
                            showNotation: true
                        }};
                        
                        console.log('Board config:', config);
                        console.log('Target element #board1 exists:', $('#board1').length > 0);
                        
                        // Create board with detailed error handling
                        console.log('Creating Chessboard...');
                        board = Chessboard('board1', config);
                        console.log('Chessboard created:', board);
                        
                        // Show board, hide loading
                        console.log('Showing board, hiding loading...');
                        $('#loadingIndicator').hide();
                        $('#board1').show();
                        
                        $('#status').text('♟️ Tablero creado - Cargando partida...');
                        
                        // Load PGN
                        console.log('PGN text length:', pgnText ? pgnText.length : 0);
                        if (pgnText && pgnText.trim()) {{
                            loadPGN(pgnText);
                        }} else {{
                            $('#status').text('✅ Tablero listo - Sin partida');
                            updateControls();
                        }}
                        
                        // Setup controls
                        console.log('Setting up controls...');
                        setupControls();
                        
                        console.log('=== CHESS BOARD INITIALIZED ===');
                        
                    }} catch (error) {{
                        console.error('=== ERROR INITIALIZING BOARD ===');
                        console.error('Error details:', error);
                        console.error('Stack trace:', error.stack);
                        $('#status').text('❌ Error: ' + error.message);
                    }}
                }}
                
                function loadPGN(pgn) {{
                    try {{
                        console.log('=== LOADING PGN ===');
                        console.log('PGN content:', pgn.substring(0, 100) + '...');
                        
                        // Reset game
                        console.log('Resetting game...');
                        game.reset();
                        
                        // Load PGN with better error handling
                        console.log('Loading PGN into Chess.js...');
                        const loadResult = game.load_pgn ? game.load_pgn(pgn) : game.loadPgn(pgn);
                        console.log('PGN load result:', loadResult);
                        
                        if (!loadResult) {{
                            throw new Error('No se pudo cargar el PGN');
                        }}
                        
                        // Get moves
                        console.log('Getting move history...');
                        moves = game.history({{ verbose: true }});
                        console.log('Moves extracted:', moves.length);
                        console.log('First few moves:', moves.slice(0, 3));
                        
                        // Reset to start
                        console.log('Resetting to start position...');
                        game.reset();
                        currentMoveIndex = -1;
                        
                        // Update display
                        console.log('Updating display...');
                        updatePosition();
                        updateMoveInfo();
                        updateControls();
                        
                        $('#status').text(`✅ Partida cargada: ${{moves.length}} jugadas`);
                        console.log('=== PGN LOADED SUCCESSFULLY ===');
                        
                    }} catch (error) {{
                        console.error('=== ERROR LOADING PGN ===');
                        console.error('Error details:', error);
                        $('#status').text('❌ Error cargando PGN: ' + error.message);
                    }}
                }}
                
                function setupControls() {{
                    $('#startBtn').click(goToStart);
                    $('#prevBtn').click(goToPrevious);
                    $('#nextBtn').click(goToNext);
                    $('#endBtn').click(goToEnd);
                    $('#flipBtn').click(flipBoard);
                    
                    // Keyboard navigation
                    $(document).keydown(function(e) {{
                        switch(e.which) {{
                            case 37: // Left arrow
                                e.preventDefault();
                                goToPrevious();
                                break;
                            case 39: // Right arrow
                                e.preventDefault();
                                goToNext();
                                break;
                            case 36: // Home
                                e.preventDefault();
                                goToStart();
                                break;
                            case 35: // End
                                e.preventDefault();
                                goToEnd();
                                break;
                        }}
                    }});
                }}
                
                function goToStart() {{
                    game.reset();
                    currentMoveIndex = -1;
                    updatePosition();
                    updateMoveInfo();
                    updateControls();
                }}
                
                function goToPrevious() {{
                    if (currentMoveIndex >= 0) {{
                        game.undo();
                        currentMoveIndex--;
                        updatePosition();
                        updateMoveInfo();
                        updateControls();
                    }}
                }}
                
                function goToNext() {{
                    if (currentMoveIndex < moves.length - 1) {{
                        currentMoveIndex++;
                        game.move(moves[currentMoveIndex]);
                        updatePosition();
                        updateMoveInfo();
                        updateControls();
                    }}
                }}
                
                function goToEnd() {{
                    while (currentMoveIndex < moves.length - 1) {{
                        currentMoveIndex++;
                        game.move(moves[currentMoveIndex]);
                    }}
                    updatePosition();
                    updateMoveInfo();
                    updateControls();
                }}
                
                function flipBoard() {{
                    if (board) {{
                        board.flip();
                    }}
                }}
                
                function updatePosition() {{
                    if (board && game) {{
                        board.position(game.fen());
                    }}
                }}
                
                function updateMoveInfo() {{
                    const moveNum = currentMoveIndex + 1;
                    $('#moveNumber').text(moveNum);
                    $('#totalMoves').text(moves.length);
                }}
                
                function updateControls() {{
                    $('#startBtn').prop('disabled', currentMoveIndex < 0);
                    $('#prevBtn').prop('disabled', currentMoveIndex < 0);
                    $('#nextBtn').prop('disabled', currentMoveIndex >= moves.length - 1);
                    $('#endBtn').prop('disabled', currentMoveIndex >= moves.length - 1);
                }}
            </script>
        </body>
        </html>
        """

        # Render component
        components.html(html_content, height=component_height)

    def render_static_position(
        self, fen: str, width: int = 400, flip_board: bool = False
    ) -> None:
        """
        Render static chess position from FEN

        Args:
            fen: FEN string representing the position
            width: Board width in pixels
            flip_board: Show board from black's perspective
        """

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Chess Position</title>
            <link rel="stylesheet" 
                  href="https://unpkg.com/@chrisoakman/chessboardjs@1.0.0/dist/chessboard-1.0.0.min.css">
            <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
            <script src="https://unpkg.com/@chrisoakman/chessboardjs@1.0.0/dist/chessboard-1.0.0.min.js"></script>
            <style>
                body {{ 
                    margin: 0; 
                    padding: 20px; 
                    text-align: center; 
                    background: #f8f9fa;
                    font-family: 'Segoe UI', sans-serif;
                }}
                .board-container {{ 
                    background: white; 
                    padding: 20px; 
                    border-radius: 12px; 
                    display: inline-block; 
                    box-shadow: 0 4px 12px rgba(0,0,0,0.1);
                }}
            </style>
        </head>
        <body>
            <div class="board-container">
                <div id="board" style="width: {width}px; height: {width}px;"></div>
            </div>
            <script>
                $(document).ready(function() {{
                    Chessboard('board', {{
                        position: '{fen}',
                        pieceTheme: 'https://unpkg.com/@chrisoakman/chessboardjs@1.0.0/img/chesspieces/wikipedia/{{piece}}.png',
                        orientation: '{'black' if flip_board else 'white'}'
                    }});
                }});
            </script>
        </body>
        </html>
        """

        components.html(html_content, height=width + 80)

    def _clean_pgn(self, pgn_text: str) -> str:
        """Clean PGN text for JavaScript consumption"""
        if not pgn_text:
            return ""

        # Remove comments and annotations
        pgn_text = re.sub(r"\\{[^}]*\\}", "", pgn_text)
        pgn_text = re.sub(r";[^\r\n]*", "", pgn_text)

        # Clean up whitespace
        pgn_text = " ".join(pgn_text.split())

        # Escape quotes for JavaScript
        pgn_text = (
            pgn_text.replace("\\", "\\\\").replace("`", "\\`").replace("${", "\\${")
        )

        return pgn_text


# Singleton instance
_chess_visualizer = None


def get_chess_visualizer() -> ChessBoardVisualizer:
    """Get or create chess visualizer instance"""
    global _chess_visualizer
    if _chess_visualizer is None:
        _chess_visualizer = ChessBoardVisualizer()
    return _chess_visualizer
