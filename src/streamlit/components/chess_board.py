"""
🎯 Chess Board Visualizer Component
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
        self.component_height = 600
        
    def render_chess_board(self, 
                          pgn_text: str, 
                          game_id: str,
                          width: int = 400,
                          show_controls: bool = True,
                          flip_board: bool = False) -> None:
        """
        Render interactive chess board with PGN navigation
        
        Args:
            pgn_text: PGN string of the game
            game_id: Unique identifier for this board instance
            width: Board width in pixels
            show_controls: Show navigation controls
            flip_board: Show from black's perspective
        """
        
        # Clean and prepare PGN
        clean_pgn = self._clean_pgn(pgn_text) if pgn_text else ""
        
        # HTML content with Chess.js + Chessboard.js
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Chess Board - {game_id}</title>
            
            <!-- Chessboard.js CSS -->
            <link rel="stylesheet" 
                  href="https://chessboardjs.com/css/chessboard-1.0.0.min.css">
            
            <!-- jQuery (required for Chessboard.js) -->
            <script src="https://code.jquery.com/jquery-3.7.1.min.js"></script>
            
            <!-- Chess.js Library -->
            <script src="https://cdnjs.cloudflare.com/ajax/libs/chess.js/1.0.0-beta.6/chess.min.js"></script>
            
            <!-- Chessboard.js Library -->
            <script src="https://chessboardjs.com/js/chessboard-1.0.0.min.js"></script>
            
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    margin: 0;
                    padding: 20px;
                    background: #f8f9fa;
                }}
                
                .chess-container {{
                    max-width: {width + 100}px;
                    margin: 0 auto;
                    background: white;
                    border-radius: 12px;
                    box-shadow: 0 4px 12px rgba(0,0,0,0.1);
                    overflow: hidden;
                }}
                
                .board-container {{
                    padding: 20px;
                    text-align: center;
                }}
                
                #board1 {{
                    margin: 0 auto;
                    border: 2px solid #ccc;
                    border-radius: 8px;
                }}
                
                .loading-board {{
                    width: {width}px;
                    height: {width}px;
                    border: 2px dashed #ccc;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    color: #666;
                    font-size: 18px;
                    margin: 0 auto;
                    border-radius: 8px;
                    background: #f9f9f9;
                }}
                
                .controls {{
                    background: #f1f3f4;
                    padding: 15px 20px;
                    border-top: 1px solid #e8eaed;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    flex-wrap: wrap;
                    gap: 10px;
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
                    padding: 8px 12px;
                    cursor: pointer;
                    font-size: 14px;
                    font-weight: 500;
                    transition: background 0.2s;
                }}
                
                .nav-button:hover:not(:disabled) {{
                    background: #1565c0;
                }}
                
                .nav-button:disabled {{
                    background: #ccc;
                    cursor: not-allowed;
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
                
                .flip-button {{
                    background: #34a853;
                }}
                
                .flip-button:hover {{
                    background: #2d8a47;
                }}
                
                .status {{
                    text-align: center;
                    padding: 10px;
                    font-size: 14px;
                    color: #5f6368;
                }}
                
                .error {{
                    color: #d93025;
                    background: #fce8e6;
                    padding: 15px;
                    margin: 10px 20px;
                    border-radius: 6px;
                }}
            </style>
        </head>
        <body>
            <div class="chess-container">
                <div class="board-container">
                    <div id="loadingBoard" class="loading-board">
                        ♟️ Cargando tablero...
                    </div>
                    <div id="board1" style="width: {width}px; height: {width}px; display: none;"></div>
                </div>
                
                {"" if not show_controls else f'''
                <div class="controls">
                    <div class="nav-buttons">
                        <button class="nav-button" id="startBtn">⏮️ Inicio</button>
                        <button class="nav-button" id="prevBtn">⏪ Anterior</button>
                        <button class="nav-button" id="nextBtn">⏩ Siguiente</button>
                        <button class="nav-button" id="endBtn">⏭️ Final</button>
                    </div>
                    
                    <div class="move-info">
                        <span id="moveNumber">Jugada: <span class="current-move">0</span></span>
                        <span id="totalMoves">Total: <span class="current-move">0</span></span>
                        <span id="currentMove"></span>
                    </div>
                    
                    <div>
                        <button class="nav-button flip-button" id="flipBtn">🔄 Voltear</button>
                    </div>
                </div>
                '''}
                
                <div id="status" class="status">Cargando tablero...</div>
            </div>

            <script>
                // Chess game instance
                let game = new Chess();
                let board = null;
                let moves = [];
                let currentMoveIndex = -1;
                
                // PGN text
                const pgnText = `{clean_pgn}`;
                
                // Board configuration
                const config = {{
                    draggable: false,
                    position: 'start',
                    pieceTheme: 'https://chessboardjs.com/img/chesspieces/wikipedia/{{piece}}.png',
                    orientation: '{'black' if flip_board else 'white'}',
                    showNotation: true,
                    sparePieces: false
                }};
                
                // Initialize board with error handling
                try {{
                    console.log('Initializing chess board...');
                    board = Chessboard('board1', config);
                    
                    // Hide loading, show board
                    document.getElementById('loadingBoard').style.display = 'none';
                    document.getElementById('board1').style.display = 'block';
                    
                    console.log('Chess board initialized successfully');
                }} catch (error) {{
                    console.error('Failed to initialize chess board:', error);
                    document.getElementById('status').innerHTML = '❌ Error al inicializar tablero';
                    return;
                }}
                
                // Parse PGN and extract moves
                function initializeGame() {{
                    console.log('Initializing game with PGN:', pgnText.length, 'characters');
                    
                    if (!pgnText || pgnText.trim() === '') {{
                        document.getElementById('status').innerHTML = '⚠️ No hay movimientos disponibles';
                        return;
                    }}
                    
                    try {{
                        // Test if Chess.js is available
                        if (typeof Chess === 'undefined') {{
                            throw new Error('Chess.js library not loaded');
                        }}
                        
                        // Load PGN
                        const loadResult = game.loadPgn(pgnText);
                        console.log('PGN load result:', loadResult);
                        
                        // Get all moves
                        const history = game.history({{ verbose: true }});
                        moves = history;
                        console.log('Extracted moves:', moves.length);
                        
                        // Reset to start position
                        game.reset();
                        currentMoveIndex = -1;
                        
                        // Update display
                        updateBoard();
                        updateControls();
                        updateMoveInfo();
                        
                        document.getElementById('status').innerHTML = `✅ Partida cargada: ${{moves.length}} jugadas`;
                        
                    }} catch (error) {{
                        console.error('Game initialization error:', error);
                        document.getElementById('status').innerHTML = `❌ Error al cargar PGN: ${{error.message}}`;
                    }}
                }}
                
                // Update board position
                function updateBoard() {{
                    if (board && game) {{
                        board.position(game.fen());
                        console.log('Board updated to position:', game.fen().split(' ')[0]);
                    }}
                }}
                
                // Update control buttons
                function updateControls() {{
                    const startBtn = document.getElementById('startBtn');
                    const prevBtn = document.getElementById('prevBtn');
                    const nextBtn = document.getElementById('nextBtn');
                    const endBtn = document.getElementById('endBtn');
                    
                    if (startBtn) startBtn.disabled = (currentMoveIndex <= -1);
                    if (prevBtn) prevBtn.disabled = (currentMoveIndex <= -1);
                    if (nextBtn) nextBtn.disabled = (currentMoveIndex >= moves.length - 1);
                    if (endBtn) endBtn.disabled = (currentMoveIndex >= moves.length - 1);
                }}
                
                // Update move information
                function updateMoveInfo() {{
                    const moveNumberElement = document.getElementById('moveNumber');
                    const totalMovesElement = document.getElementById('totalMoves');
                    const currentMoveElement = document.getElementById('currentMove');
                    
                    if (moveNumberElement) {{
                        moveNumberElement.innerHTML = `Jugada: <span class="current-move">${{currentMoveIndex + 1}}</span>`;
                    }}
                    
                    if (totalMovesElement) {{
                        totalMovesElement.innerHTML = `Total: <span class="current-move">${{moves.length}}</span>`;
                    }}
                    
                    if (currentMoveElement && currentMoveIndex >= 0 && currentMoveIndex < moves.length) {{
                        const move = moves[currentMoveIndex];
                        currentMoveElement.innerHTML = `<strong>${{move.san}}</strong>`;
                    }} else if (currentMoveElement) {{
                        currentMoveElement.innerHTML = '<em>Posición inicial</em>';
                    }}
                }}
                
                // Navigation functions
                function goToStart() {{
                    game.reset();
                    currentMoveIndex = -1;
                    updateBoard();
                    updateControls();
                    updateMoveInfo();
                }}
                
                function goToPrevious() {{
                    if (currentMoveIndex > -1) {{
                        game.undo();
                        currentMoveIndex--;
                        updateBoard();
                        updateControls();
                        updateMoveInfo();
                    }}
                }}
                
                function goToNext() {{
                    if (currentMoveIndex < moves.length - 1) {{
                        currentMoveIndex++;
                        game.move(moves[currentMoveIndex]);
                        updateBoard();
                        updateControls();
                        updateMoveInfo();
                    }}
                }}
                
                function goToEnd() {{
                    // Reset and play all moves
                    game.reset();
                    for (let i = 0; i < moves.length; i++) {{
                        game.move(moves[i]);
                    }}
                    currentMoveIndex = moves.length - 1;
                    updateBoard();
                    updateControls();
                    updateMoveInfo();
                }}
                
                function flipBoard() {{
                    board.flip();
                }}
                
                // Event listeners
                document.addEventListener('DOMContentLoaded', function() {{
                    console.log('DOM Content Loaded - setting up chess board');
                    
                    // Check if required libraries are loaded
                    if (typeof $ === 'undefined') {{
                        document.getElementById('status').innerHTML = '❌ jQuery no cargado';
                        return;
                    }}
                    
                    if (typeof Chess === 'undefined') {{
                        document.getElementById('status').innerHTML = '❌ Chess.js no cargado';
                        return;
                    }}
                    
                    if (typeof Chessboard === 'undefined') {{
                        document.getElementById('status').innerHTML = '❌ Chessboard.js no cargado';
                        return;
                    }}
                    
                    console.log('All libraries loaded successfully');
                    
                    const startBtn = document.getElementById('startBtn');
                    const prevBtn = document.getElementById('prevBtn');
                    const nextBtn = document.getElementById('nextBtn');
                    const endBtn = document.getElementById('endBtn');
                    const flipBtn = document.getElementById('flipBtn');
                    
                    if (startBtn) startBtn.addEventListener('click', goToStart);
                    if (prevBtn) prevBtn.addEventListener('click', goToPrevious);
                    if (nextBtn) nextBtn.addEventListener('click', goToNext);
                    if (endBtn) endBtn.addEventListener('click', goToEnd);
                    if (flipBtn) flipBtn.addEventListener('click', flipBoard);
                    
                    // Keyboard navigation
                    document.addEventListener('keydown', function(e) {{
                        switch(e.key) {{
                            case 'ArrowLeft':
                                e.preventDefault();
                                goToPrevious();
                                break;
                            case 'ArrowRight':
                                e.preventDefault();
                                goToNext();
                                break;
                            case 'Home':
                                e.preventDefault();
                                goToStart();
                                break;
                            case 'End':
                                e.preventDefault();
                                goToEnd();
                                break;
                        }}
                    }});
                    
                    // Initialize the game after a short delay to ensure everything is loaded
                    setTimeout(function() {{
                        initializeGame();
                    }}, 500);
                }});
            </script>
        </body>
        </html>
        """
        
        # Render the component
        components.html(
            html_content, 
            height=self.component_height
        )
    
    def _clean_pgn(self, pgn_text: str) -> str:
        """Clean and prepare PGN text for parsing"""
        if not pgn_text:
            return ""
            
        # Remove excessive whitespace
        pgn_text = re.sub(r'\s+', ' ', pgn_text.strip())
        
        # Ensure it ends with result if moves are present
        if pgn_text and not any(result in pgn_text for result in ['1-0', '0-1', '1/2-1/2', '*']):
            pgn_text += " *"
        
        return pgn_text

    def render_position_only(self, 
                           fen: str, 
                           width: int = 350,
                           flip_board: bool = False) -> None:
        """Render a static chess position from FEN"""
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <link rel="stylesheet" 
                  href="https://unpkg.com/@chrisoakman/chessboardjs@1.0.0/dist/chessboard-1.0.0.min.css">
            <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
            <script src="https://unpkg.com/@chrisoakman/chessboardjs@1.0.0/dist/chessboard-1.0.0.min.js"></script>
            <style>
                body {{ margin: 0; padding: 20px; text-align: center; background: #f8f9fa; }}
                .board-container {{ 
                    background: white; 
                    padding: 20px; 
                    border-radius: 12px; 
                    display: inline-block; 
                    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                }}
            </style>
        </head>
        <body>
            <div class="board-container">
                <div id="board" style="width: {width}px; height: {width}px;"></div>
            </div>
            <script>
                Chessboard('board', {{
                    position: '{fen}',
                    pieceTheme: 'https://chessboardjs.com/img/chesspieces/wikipedia/{{piece}}.png',
                    orientation: '{'black' if flip_board else 'white'}'
                }});
            </script>
        </body>
        </html>
        """
        
        components.html(html_content, height=width + 80)


# Singleton instance
_chess_visualizer = None

def get_chess_visualizer() -> ChessBoardVisualizer:
    """Get or create chess visualizer instance"""
    global _chess_visualizer
    if _chess_visualizer is None:
        _chess_visualizer = ChessBoardVisualizer()
    return _chess_visualizer