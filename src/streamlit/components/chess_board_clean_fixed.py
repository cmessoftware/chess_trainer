"""
🎯 Clean Chess Board - Fixed Version
Versión corregida sin conflictos de sintaxis

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

    def _extract_moves_from_pgn(self, pgn_text: str) -> list:
        """Extraer movimientos del PGN como lista"""
        try:
            # Eliminar headers
            lines = pgn_text.strip().split("\n")
            moves_lines = []

            for line in lines:
                line = line.strip()
                # Skip headers [Event "..."] and empty lines
                if not line or line.startswith("["):
                    continue
                moves_lines.append(line)

            # Join moves and clean up
            moves_text = " ".join(moves_lines)

            # Remove result indicators
            moves_text = re.sub(r"\s*(1-0|0-1|1/2-1/2|\*)\s*$", "", moves_text)

            # Clean up notation
            moves_text = re.sub(r"\{[^}]*\}", "", moves_text)  # Remove comments
            moves_text = re.sub(r"\([^)]*\)", "", moves_text)  # Remove variations
            moves_text = re.sub(r"\$\d+", "", moves_text)  # Remove annotations

            # Split into moves, keeping move numbers for reference
            parts = moves_text.split()
            moves = []

            for part in parts:
                part = part.strip()
                if not part:
                    continue
                # Skip move numbers (1., 2., etc.)
                if re.match(r"^\d+\.+$", part):
                    continue
                # Add actual moves
                if not re.match(r"^\d+\.$", part):
                    moves.append(part)

            return moves
        except Exception:
            return []

    def render_chess_board(
        self,
        pgn_text: str,
        width: int = 400,
        height: Optional[int] = None,
        show_controls: bool = True,
        flip_board: bool = False,
        game_id: Optional[str] = None,
    ) -> None:
        """Renderizar tablero de ajedrez limpio y funcional"""

        if not pgn_text:
            st.warning("⚠️ No se proporcionó PGN para visualizar")
            return

        # Extraer movimientos del PGN
        moves_list = self._extract_moves_from_pgn(pgn_text)

        # Component height
        component_height = height or (width + 250 if show_controls else width + 80)

        # Crear el HTML usando concatenación de strings para evitar problemas con f-strings
        html_content = self._build_html_content(
            width, moves_list, show_controls, flip_board
        )

        # Render component
        components.html(html_content, height=component_height, scrolling=False)

    def _build_html_content(
        self, width: int, moves_list: list, show_controls: bool, flip_board: bool
    ) -> str:
        """Construir contenido HTML de forma segura"""

        font_size = width // 10
        container_width = width + 40

        controls_html = ""
        if show_controls:
            controls_html = """
            <div class='controls'>
                <button id='btnPrevious' type='button'>⬅️ Anterior</button>
                <button id='btnNext' type='button'>Siguiente ➡️</button>
                <button id='btnReset' type='button'>🏠 Inicio</button>
                <span id='move-counter' style='margin-left: 10px; font-weight: bold;'>0 / 0</span>
            </div>
            """

        # Convertir la lista de movimientos a string JSON para JavaScript
        import json

        moves_json = json.dumps(moves_list)

        return f"""
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
                    max-width: {container_width}px;
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
                    font-size: {font_size}px;
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
                    cursor: pointer;
                    user-select: none;
                    transition: transform 0.2s;
                }}
                
                .piece:hover {{
                    transform: scale(1.05);
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
                    text-align: center;
                }}
            </style>
        </head>
        <body>
            <div class="board-container">
                <div id="move-display" class="move-display">Posición inicial</div>
                <div id="chessboard" class="chessboard"></div>
                {controls_html}
            </div>

            <script>
                // Unicode pieces
                var pieces = {{
                    'wK': '♔', 'wQ': '♕', 'wR': '♖', 'wB': '♗', 'wN': '♘', 'wP': '♙',
                    'bK': '♚', 'bQ': '♛', 'bR': '♜', 'bB': '♝', 'bN': '♞', 'bP': '♟'
                }};
                
                // Game state
                var currentMoveIndex = 0;
                var gameMoves = {moves_json};
                var gamePositions = [];
                
                // Create positions array - simplified approach
                // Position 0: initial position
                // Position n: after move n
                
                // Initial position
                var initialPosition = {{
                    'a8': 'bR', 'b8': 'bN', 'c8': 'bB', 'd8': 'bQ', 'e8': 'bK', 'f8': 'bB', 'g8': 'bN', 'h8': 'bR',
                    'a7': 'bP', 'b7': 'bP', 'c7': 'bP', 'd7': 'bP', 'e7': 'bP', 'f7': 'bP', 'g7': 'bP', 'h7': 'bP',
                    'a2': 'wP', 'b2': 'wP', 'c2': 'wP', 'd2': 'wP', 'e2': 'wP', 'f2': 'wP', 'g2': 'wP', 'h2': 'wP',
                    'a1': 'wR', 'b1': 'wN', 'c1': 'wB', 'd1': 'wQ', 'e1': 'wK', 'f1': 'wB', 'g1': 'wN', 'h1': 'wR'
                }};
                
                var currentPosition = JSON.parse(JSON.stringify(initialPosition));
                
                // Initialize positions array with proper move parsing
                function initializePositions() {{
                    gamePositions = [];
                    gamePositions.push(JSON.parse(JSON.stringify(initialPosition))); // Position 0
                    
                    console.log('Initializing positions for', gameMoves.length, 'moves');
                    
                    var currentPos = JSON.parse(JSON.stringify(initialPosition));
                    var isWhiteToMove = true;
                    
                    for (var i = 0; i < gameMoves.length; i++) {{
                        var move = gameMoves[i];
                        var newPos = JSON.parse(JSON.stringify(currentPos));
                        
                        // Apply basic move simulation
                        newPos = simulateMove(newPos, move, isWhiteToMove);
                        
                        gamePositions.push(newPos);
                        currentPos = newPos;
                        isWhiteToMove = !isWhiteToMove; // Alternate turns
                    }}
                    
                    console.log('Created', gamePositions.length, 'positions');
                }}
                
                function simulateMove(position, move, isWhite) {{
                    var newPos = JSON.parse(JSON.stringify(position));
                    
                    // Simple move parser for basic moves
                    try {{
                        if (move.includes('O-O-O')) {{
                            // Queenside castling
                            if (isWhite) {{
                                delete newPos['e1']; delete newPos['a1'];
                                newPos['c1'] = 'wK'; newPos['d1'] = 'wR';
                            }} else {{
                                delete newPos['e8']; delete newPos['a8'];
                                newPos['c8'] = 'bK'; newPos['d8'] = 'bR';
                            }}
                        }} else if (move.includes('O-O')) {{
                            // Kingside castling
                            if (isWhite) {{
                                delete newPos['e1']; delete newPos['h1'];
                                newPos['g1'] = 'wK'; newPos['f1'] = 'wR';
                            }} else {{
                                delete newPos['e8']; delete newPos['h8'];
                                newPos['g8'] = 'bK'; newPos['f8'] = 'bR';
                            }}
                        }} else {{
                            // Parse regular move
                            var cleanMove = move.replace(/[+#!?]/g, ''); // Remove check/mate/quality symbols
                            newPos = parseRegularMove(newPos, cleanMove, isWhite);
                        }}
                    }} catch (e) {{
                        console.log('Could not parse move:', move);
                    }}
                    
                    return newPos;
                }}
                
                function parseRegularMove(position, move, isWhite) {{
                    var newPos = JSON.parse(JSON.stringify(position));
                    var color = isWhite ? 'w' : 'b';
                    
                    // Extract destination square (last 2 characters)
                    var destination = move.slice(-2);
                    if (!/^[a-h][1-8]$/.test(destination)) {{
                        return newPos; // Invalid destination
                    }}
                    
                    var piece = '';
                    var fromSquare = '';
                    
                    if (move.length === 2) {{
                        // Pawn move (e.g., "e4")
                        piece = color + 'P';
                        fromSquare = findPawnSource(position, destination, isWhite, false);
                    }} else if (move.includes('x')) {{
                        // Capture
                        if (move.length === 4 && move[1] === 'x') {{
                            // Pawn capture (e.g., "exd5")
                            piece = color + 'P';
                            var fromFile = move[0];
                            fromSquare = findPawnSource(position, destination, isWhite, true, fromFile);
                        }} else {{
                            // Piece capture (e.g., "Nxf3", "Qxd8")
                            var pieceType = move[0];
                            piece = color + pieceType;
                            fromSquare = findPieceSource(position, piece, destination, move);
                        }}
                    }} else {{
                        // Regular piece move (e.g., "Nf3", "Qd8", "Be5")
                        var pieceType = move[0];
                        piece = color + pieceType;
                        fromSquare = findPieceSource(position, piece, destination, move);
                    }}
                    
                    // Apply move if valid source found
                    if (fromSquare && position[fromSquare] === piece) {{
                        delete newPos[fromSquare];
                        newPos[destination] = piece;
                    }}
                    
                    return newPos;
                }}
                
                function findPawnSource(position, destination, isWhite, isCapture, fromFile) {{
                    fromFile = fromFile || null; // Handle optional parameter
                    var file = destination[0];
                    var rank = parseInt(destination[1]);
                    var color = isWhite ? 'w' : 'b';
                    var piece = color + 'P';
                    
                    if (isCapture && fromFile) {{
                        // Pawn capture - check diagonal squares
                        var sourceRank = isWhite ? rank - 1 : rank + 1;
                        var sourceSquare = fromFile + sourceRank;
                        if (position[sourceSquare] === piece) {{
                            return sourceSquare;
                        }}
                    }} else {{
                        // Regular pawn move
                        var sourceRank = isWhite ? rank - 1 : rank + 1;
                        var sourceSquare = file + sourceRank;
                        
                        if (position[sourceSquare] === piece) {{
                            return sourceSquare;
                        }}
                        
                        // Check two-square initial move
                        if ((isWhite && rank === 4) || (!isWhite && rank === 5)) {{
                            sourceRank = isWhite ? rank - 2 : rank + 2;
                            sourceSquare = file + sourceRank;
                            if (position[sourceSquare] === piece) {{
                                return sourceSquare;
                            }}
                        }}
                    }}
                    
                    return null;
                }}
                
                function findPieceSource(position, piece, destination, fullMove) {{
                    // Simple implementation - find first matching piece that could move to destination
                    for (var square in position) {{
                        if (position[square] === piece) {{
                            // Basic validation - this is simplified
                            // In a real implementation, we'd check if the move is legal
                            return square;
                        }}
                    }}
                    return null;
                }}
                
                function createBoard() {{
                    var board = document.getElementById('chessboard');
                    board.innerHTML = '';
                    
                    for (var row = 8; row >= 1; row--) {{
                        for (var col = 1; col <= 8; col++) {{
                            var file = String.fromCharCode(96 + col); // 'a' to 'h'
                            var square = file + row;
                            
                            var squareElement = document.createElement('div');
                            squareElement.className = 'square ' + ((row + col) % 2 === 0 ? 'dark' : 'light');
                            squareElement.dataset.square = square;
                            
                            // NO drag & drop - only navigation
                            squareElement.addEventListener('click', handleSquareClick);
                            
                            var piece = currentPosition[square];
                            if (piece) {{
                                var pieceElement = document.createElement('span');
                                pieceElement.textContent = pieces[piece];
                                pieceElement.className = 'piece';
                                pieceElement.draggable = false; // Disable dragging
                                pieceElement.dataset.piece = piece;
                                squareElement.appendChild(pieceElement);
                            }}
                            
                            board.appendChild(squareElement);
                        }}
                    }}
                }}
                
                function handleSquareClick(event) {{
                    // Just show square info, no piece movement
                    var square = event.target.closest('.square').dataset.square;
                    var piece = currentPosition[square];
                    if (piece) {{
                        updateMoveDisplay('Casilla: ' + square + ' - Pieza: ' + pieces[piece]);
                    }} else {{
                        updateMoveDisplay('Casilla: ' + square + ' - Vacía');
                    }}
                }}
                
                function updateMoveDisplay(text) {{
                    document.getElementById('move-display').textContent = text;
                }}
                
                function updateMoveCounter() {{
                    var counter = document.getElementById('move-counter');
                    if (counter) {{
                        counter.textContent = currentMoveIndex + ' / ' + gameMoves.length;
                    }}
                }}
                
                function previousMove() {{
                    console.log('previousMove called, currentIndex:', currentMoveIndex);
                    if (currentMoveIndex > 0) {{
                        currentMoveIndex--;
                        updateToCurrentPosition();
                        console.log('Moved to index:', currentMoveIndex);
                    }} else {{
                        console.log('Already at beginning');
                        updateMoveDisplay('🏠 Ya en la posición inicial');
                    }}
                }}
                
                function nextMove() {{
                    console.log('nextMove called, currentIndex:', currentMoveIndex, 'maxMoves:', gameMoves.length);
                    if (currentMoveIndex < gameMoves.length && currentMoveIndex < gamePositions.length - 1) {{
                        currentMoveIndex++;
                        updateToCurrentPosition();
                        console.log('Moved to index:', currentMoveIndex);
                    }} else {{
                        console.log('Already at end');
                        updateMoveDisplay('🔚 Ya en la última jugada');
                    }}
                }}
                
                function resetPosition() {{
                    console.log('resetPosition called');
                    currentMoveIndex = 0;
                    updateToCurrentPosition();
                    console.log('Reset to beginning');
                }}
                
                function updateToCurrentPosition() {{
                    console.log('updateToCurrentPosition called, index:', currentMoveIndex, 'positions available:', gamePositions.length);
                    
                    if (currentMoveIndex < gamePositions.length) {{
                        currentPosition = JSON.parse(JSON.stringify(gamePositions[currentMoveIndex]));
                        createBoard();
                        
                        if (currentMoveIndex === 0) {{
                            updateMoveDisplay('🏠 Posición inicial');
                        }} else {{
                            var move = gameMoves[currentMoveIndex - 1];
                            var moveNumber = Math.ceil(currentMoveIndex / 2);
                            var color = currentMoveIndex % 2 === 1 ? 'Blancas' : 'Negras';
                            updateMoveDisplay(moveNumber + '. ' + move + ' (' + color + ')');
                        }}
                        
                        updateMoveCounter();
                    }} else {{
                        console.log('Position index out of range');
                        updateMoveDisplay('❌ Error: Posición no disponible');
                    }}
                }}
                
                // Initialize board
                document.addEventListener('DOMContentLoaded', function() {{
                    console.log('Movimientos cargados:', gameMoves);
                    initializePositions();
                    createBoard();
                    
                    // Setup button event listeners
                    var btnPrevious = document.getElementById('btnPrevious');
                    var btnNext = document.getElementById('btnNext');
                    var btnReset = document.getElementById('btnReset');
                    
                    if (btnPrevious) {{
                        btnPrevious.addEventListener('click', function() {{
                            console.log('Previous button clicked');
                            previousMove();
                        }});
                    }}
                    
                    if (btnNext) {{
                        btnNext.addEventListener('click', function() {{
                            console.log('Next button clicked');
                            nextMove();
                        }});
                    }}
                    
                    if (btnReset) {{
                        btnReset.addEventListener('click', function() {{
                            console.log('Reset button clicked');
                            resetPosition();
                        }});
                    }}
                    
                    if (gameMoves.length > 0) {{
                        updateMoveDisplay('Partida cargada: ' + gameMoves.length + ' movimientos');
                    }} else {{
                        updateMoveDisplay('Posición inicial - Usa los botones para navegar');
                    }}
                    
                    updateMoveCounter();
                }});
            </script>
        </body>
        </html>
        """


def get_clean_chess_visualizer() -> CleanChessBoardVisualizer:
    """Factory function to get clean chess visualizer instance."""
    return CleanChessBoardVisualizer()
