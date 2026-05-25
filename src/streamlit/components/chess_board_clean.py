"""
🎯 Clean Chess Board - Minimalist Interactive Chess Board
Versión minimalista sin logs excesivos para testing

Author: Chess Trainer Frontend Team  
Date: January 16, 2026
"""

import streamlit as st
import streamlit.components.v1 as components
import re
from typing import Optional


class CleanChessBoardVisualizer:
    """Versión limpia del visualizador de ajedrez sin logs excesivos"""
    
    def __init__(self):
        pass
    
    def _extract_moves_from_pgn(self, pgn_text: str) -> str:
        """Extraer movimientos del PGN"""
        try:
            # Eliminar headers
            lines = pgn_text.strip().split('\n')
            moves_lines = []
            
            for line in lines:
                line = line.strip()
                # Skip headers [Event "..."] and empty lines
                if not line or line.startswith('['):
                    continue
                moves_lines.append(line)
            
            # Join moves and clean up
            moves_text = ' '.join(moves_lines)
            
            # Remove result indicators
            moves_text = re.sub(r'\s*(1-0|0-1|1/2-1/2|\*)\s*$', '', moves_text)
            
            # Clean up notation
            moves_text = re.sub(r'\{[^}]*\}', '', moves_text)  # Remove comments
            moves_text = re.sub(r'\([^)]*\)', '', moves_text)  # Remove variations
            moves_text = re.sub(r'\d+\.+', ' ', moves_text)    # Remove move numbers
            moves_text = re.sub(r'\s+', ' ', moves_text).strip()
            
            return moves_text
        except Exception:
            return ""
        
    def render_chess_board(self, 
                          pgn_text: str, 
                          width: int = 400, 
                          height: Optional[int] = None,
                          show_controls: bool = True,
                          flip_board: bool = False,
                          game_id: Optional[str] = None) -> None:
        """Renderizar tablero de ajedrez limpio y funcional"""
        
        if not pgn_text:
            st.warning("⚠️ No se proporcionó PGN para visualizar")
            return
            
        # Extraer movimientos del PGN
        moves_text = self._extract_moves_from_pgn(pgn_text)
        
        # Component height
        component_height = height or (width + 250 if show_controls else width + 80)
        
        # HTML completamente limpio
        html_content = f"""
        <!DOCTYPE html>
        <html lang="es">
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <title>Chess Board Clean</title>
            
            <style>
                body {{ margin: 0; padding: 20px; font-family: Arial, sans-serif; }}
                
                .board-container {{
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    max-width: {width + 40}px;
                    margin: 0 auto;
                }}
                
                .chessboard {{
                    border: 2px solid #333;
                    display: grid;
                    grid-template-columns: repeat(8, 1fr);
                    grid-template-rows: repeat(8, 1fr);
                    width: {width}px;
                    height: {width}px;
                    position: relative;
                }}
                
                .square {{
                    position: relative;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-size: {width // 10}px;
                    cursor: pointer;
                }}
                
                .square.light {{ background-color: #f0d9b5; }}
                .square.dark {{ background-color: #b58863; }}
                
                .square.selected {{
                    box-shadow: inset 0 0 0 3px #ffff00;
                }}
                
                .square.possible-move {{
                    box-shadow: inset 0 0 0 3px #00ff00;
                }}
                
                .piece {{
                    cursor: grab;
                    user-select: none;
                    transition: transform 0.2s;
                }}
                
                .piece:hover {{
                    transform: scale(1.1);
                }}
                
                .piece.dragging {{
                    cursor: grabbing;
                    opacity: 0.7;
                    z-index: 1000;
                }}
                
                .controls {{
                    margin-top: 20px;
                    text-align: center;
                }}
                
                .controls button {{
                    margin: 0 5px;
                    padding: 8px 16px;
                    border: 1px solid #ccc;
                    background: #f9f9f9;
                    border-radius: 4px;
                    cursor: pointer;
                }}
                
                .controls button:hover {{
                    background: #e9e9e9;
                }}
                
                .move-display {{
                    margin: 10px 0;
                    font-weight: bold;
                    min-height: 20px;
                }}
            </style>
        </head>
        <body>
            <div class="board-container">
                <div id="move-display" class="move-display">Posición inicial</div>
                <div id="chessboard" class="chessboard"></div>
                {"<div class='controls'><button onclick='previousMove()'>⬅️ Anterior</button><button onclick='nextMove()'>Siguiente ➡️</button><button onclick='resetPosition()'>🏠 Inicio</button></div>" if show_controls else ""}
            </div>

            <script>
                // Unicode pieces
                const pieces = {
                    'wK': '♔', 'wQ': '♕', 'wR': '♖', 'wB': '♗', 'wN': '♘', 'wP': '♙',
                    'bK': '♚', 'bQ': '♛', 'bR': '♜', 'bB': '♝', 'bN': '♞', 'bP': '♟'
                };
                
                // Game state
                let currentMoveIndex = 0;
                let gameMoves = [];
                let gamePositions = [];
                let selectedSquare = null;
                let draggedPiece = null;
                
                // Parse moves from PGN
                const movesText = "{moves_text}";
                if (movesText.trim()) {{
                    const splitRegex = new RegExp('\\\\s+');
                    gameMoves = movesText.split(splitRegex).filter(function(move) {{
                        return move.length > 0;
                    }});
                    console.log('Parsed moves:', gameMoves);
                }}
                
                // Initial position
                let initialPosition = {{
                    'a8': 'bR', 'b8': 'bN', 'c8': 'bB', 'd8': 'bQ', 'e8': 'bK', 'f8': 'bB', 'g8': 'bN', 'h8': 'bR',
                    'a7': 'bP', 'b7': 'bP', 'c7': 'bP', 'd7': 'bP', 'e7': 'bP', 'f7': 'bP', 'g7': 'bP', 'h7': 'bP',
                    'a2': 'wP', 'b2': 'wP', 'c2': 'wP', 'd2': 'wP', 'e2': 'wP', 'f2': 'wP', 'g2': 'wP', 'h2': 'wP',
                    'a1': 'wR', 'b1': 'wN', 'c1': 'wB', 'd1': 'wQ', 'e1': 'wK', 'f1': 'wB', 'g1': 'wN', 'h1': 'wR'
                }};
                
                let currentPosition = JSON.parse(JSON.stringify(initialPosition));
                
                function createBoard() {{
                    const board = document.getElementById('chessboard');
                    board.innerHTML = '';
                    
                    for (let row = 8; row >= 1; row--) {{
                        for (let col = 1; col <= 8; col++) {{
                            const file = String.fromCharCode(96 + col); // 'a' to 'h'
                            const square = file + row;
                            
                            const squareElement = document.createElement('div');
                            squareElement.className = 'square ' + ((row + col) % 2 === 0 ? 'dark' : 'light');
                            squareElement.dataset.square = square;
                            
                            // Event listeners
                            squareElement.addEventListener('click', handleSquareClick);
                            squareElement.addEventListener('dragover', handleDragOver);
                            squareElement.addEventListener('drop', handleDrop);
                            
                            const piece = currentPosition[square];
                            if (piece) {{
                                const pieceElement = document.createElement('span');
                                pieceElement.textContent = pieces[piece];
                                pieceElement.className = 'piece';
                                pieceElement.draggable = true;
                                pieceElement.dataset.piece = piece;
                                pieceElement.addEventListener('dragstart', handleDragStart);
                                squareElement.appendChild(pieceElement);
                            }}
                            
                            board.appendChild(squareElement);
                        }}
                    }}
                }}
                
                function handleSquareClick(event) {{
                    const square = event.target.closest('.square').dataset.square;
                    
                    if (selectedSquare) {{
                        // Try to make move
                        if (selectedSquare !== square) {{
                            makeMove(selectedSquare, square);
                        }}
                        clearHighlights();
                    }} else if (currentPosition[square]) {{
                        // Select piece
                        selectedSquare = square;
                        event.target.closest('.square').classList.add('selected');
                        highlightPossibleMoves(square);
                    }}
                }}
                
                function handleDragStart(event) {{
                    draggedPiece = {{
                        piece: event.target.dataset.piece,
                        square: event.target.closest('.square').dataset.square
                    }};
                    event.target.classList.add('dragging');
                }}
                
                function handleDragOver(event) {{
                    event.preventDefault();
                }}
                
                function handleDrop(event) {{
                    event.preventDefault();
                    
                    if (draggedPiece) {{
                        const targetSquare = event.target.closest('.square').dataset.square;
                        makeMove(draggedPiece.square, targetSquare);
                        
                        // Clean up
                        const draggingPiece = document.querySelector('.piece.dragging');
                        if (draggingPiece) draggingPiece.classList.remove('dragging');
                        draggedPiece = null;
                    }}
                }}
                
                function makeMove(fromSquare, toSquare) {{
                    if (fromSquare && toSquare && fromSquare !== toSquare) {{
                        const piece = currentPosition[fromSquare];
                        if (piece) {{
                            // Simple move validation (basic)
                            if (isValidMove(fromSquare, toSquare, piece)) {{
                                currentPosition[toSquare] = piece;
                                delete currentPosition[fromSquare];
                                createBoard();
                                updateMoveDisplay('Movimiento: ' + fromSquare + '-' + toSquare);
                            }}
                        }}
                    }}
                    selectedSquare = null;
                }}
                
                function isValidMove(fromSquare, toSquare, piece) {{
                    // Basic validation - can be enhanced
                    return toSquare && fromSquare !== toSquare;
                }}
                
                function highlightPossibleMoves(square) {{
                    // Basic highlighting - can be enhanced
                    const squares = document.querySelectorAll('.square');
                    squares.forEach(sq => {{
                        if (sq.dataset.square !== square) {{
                            sq.classList.add('possible-move');
                        }}
                    }});
                }}
                
                function clearHighlights() {{
                    const squares = document.querySelectorAll('.square');
                    squares.forEach(sq => {{
                        sq.classList.remove('selected', 'possible-move');
                    }});
                    selectedSquare = null;
                }}
                
                function updateMoveDisplay(text) {{
                    document.getElementById('move-display').textContent = text;
                }}
                
                function previousMove() {
                    if (currentMoveIndex > 0) {
                        currentMoveIndex--;
                        updatePositionToMove(currentMoveIndex);
                        const move = currentMoveIndex === 0 ? 'Posición inicial' : gameMoves[currentMoveIndex - 1];
                        updateMoveDisplay(`Movimiento ${currentMoveIndex}: ${move}`);
                    }
                }
                
                function nextMove() {
                    if (currentMoveIndex < gameMoves.length) {
                        const move = gameMoves[currentMoveIndex];
                        currentMoveIndex++;
                        updatePositionToMove(currentMoveIndex);
                        updateMoveDisplay(`Movimiento ${currentMoveIndex}: ${move}`);
                    }
                }
                
                function resetPosition() {
                    currentMoveIndex = 0;
                    currentPosition = JSON.parse(JSON.stringify(initialPosition));
                    createBoard();
                    updateMoveDisplay('🏠 Posición inicial');
                    clearHighlights();
                }
                
                function updatePositionToMove(moveIndex) {
                    // Simple implementation - for demo purposes
                    // In a real implementation, you'd parse and execute each move
                    // For now, just show we're navigating
                    createBoard();
                }
                
                // Initialize board
                document.addEventListener('DOMContentLoaded', function() {
                    createBoard();
                    if (gameMoves.length > 0) {
                        updateMoveDisplay(`Partida cargada: ${gameMoves.length} movimientos disponibles`);
                    } else {
                        updateMoveDisplay('Posición inicial - Tablero interactivo listo');
                    }
                });
            </script>
        </body>
        </html>
        """
        
        # Render component
        components.html(html_content, height=component_height, scrolling=False)


def get_clean_chess_visualizer() -> CleanChessBoardVisualizer:
    """Factory function to get clean chess visualizer instance."""
    return CleanChessBoardVisualizer()