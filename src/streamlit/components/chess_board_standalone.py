"""
🎯 Chess Board Visualizer - STANDALONE VERSION
Versión completamente autónoma sin dependencias de CDN externo

Author: Chess Trainer Frontend Team
Date: January 16, 2026
"""

import streamlit as st
import streamlit.components.v1 as components
import re
from typing import Optional


class StandaloneChessBoardVisualizer:
    """Versión autónoma del visualizador de ajedrez"""
    
    def __init__(self):
        self.component_height = 600
        
    def render_chess_board(self, 
                          pgn_text: str, 
                          width: int = 400, 
                          height: Optional[int] = None,
                          show_controls: bool = True,
                          flip_board: bool = False,
                          game_id: Optional[str] = None) -> None:
        """Renderizar tablero de ajedrez autónomo"""
        
        if not pgn_text:
            st.warning("⚠️ No se proporcionó PGN para visualizar")
            return
            
        # Clean PGN
        clean_pgn = self._clean_pgn(pgn_text)
        
        # Component height
        component_height = height or (width + 250 if show_controls else width + 80)
        
        # HTML completamente autónomo
        html_content = f"""
        <!DOCTYPE html>
        <html lang="es">
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <title>Chess Board Standalone</title>
            
            <style>
                /* Chessboard CSS básico */
                .chessboard-63f37 {{
                    border: 2px solid #404040;
                    box-sizing: content-box;
                }}
                
                .square-55d63 {{
                    float: left;
                    position: relative;
                    cursor: pointer;
                }}
                
                .white-1e1d7 {{
                    background-color: #f0d9b5;
                    color: #b58863;
                }}
                
                .black-3c85d {{
                    background-color: #b58863;
                    color: #f0d9b5;
                }}
                
                .piece-417db {{
                    position: absolute;
                    top: 0;
                    left: 0;
                    width: 100%;
                    height: 100%;
                    background-size: contain;
                    background-repeat: no-repeat;
                    background-position: center;
                    cursor: grab;
                    user-select: none;
                    z-index: 10;
                }}
                
                .piece-417db:hover {{
                    transform: scale(1.05);
                    z-index: 20;
                }}
                
                .piece-417db.dragging {{
                    cursor: grabbing;
                    z-index: 30;
                    opacity: 0.8;
                    transform: scale(1.1);
                }}
                
                .square-55d63.highlight-possible {{
                    box-shadow: inset 0 0 0 3px #00ff00;
                }}
                
                .square-55d63.highlight-selected {{
                    box-shadow: inset 0 0 0 4px #ffff00;
                }}
                
                .square-55d63.highlight-last-move {{
                    box-shadow: inset 0 0 0 2px #ff6b6b;
                }}
                
                .move-indicator {{
                    position: absolute;
                    width: 20px;
                    height: 20px;
                    border-radius: 50%;
                    background: rgba(0, 255, 0, 0.6);
                    border: 2px solid #00aa00;
                    pointer-events: none;
                    z-index: 15;
                    top: 50%;
                    left: 50%;
                    transform: translate(-50%, -50%);
                }}
                
                /* Estilos de la aplicación */
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
                    �️ VERSIÓN AUTÓNOMA - SIN CDN - ID: {game_id or 'standalone'}<br>
                    📊 Estado: Inicializando tablero básico (sin librerías externas)
                </div>
                
                <div class="board-wrapper">
                    <div id="loadingIndicator" class="loading">
                        🏁 Creando tablero básico...
                    </div>
                    <div id="board1" style="width: {width}px; height: {width}px; display: none;">
                        <!-- Tablero básico será generado aquí -->
                    </div>
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
                
                <div class="status" id="status">🚀 Iniciando versión autónoma...</div>
            </div>

            <script>
                // Variables globales
                let board = null;
                let currentPosition = 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1'; // Posición inicial
                let moves = [];
                let currentMoveIndex = -1;
                const pgnText = `{clean_pgn}`;
                let selectedSquare = null;
                let possibleMoves = [];
                let draggedPiece = null;
                let gameHistory = []; // Historial de posiciones
                let isInteractive = true;
                
                // Mapeo simple de piezas a Unicode
                const pieceUnicode = {{
                    'K': '♔', 'Q': '♕', 'R': '♖', 'B': '♗', 'N': '♘', 'P': '♙',
                    'k': '♚', 'q': '♛', 'r': '♜', 'b': '♝', 'n': '♞', 'p': '♟'
                }};
                
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
                
                // Parsear FEN básico
                function parseFEN(fen) {{
                    const parts = fen.split(' ');
                    const position = parts[0];
                    const rows = position.split('/');
                    const board = [];
                    
                    for (let i = 0; i < 8; i++) {{
                        const row = [];
                        const rowString = rows[i];
                        
                        for (let j = 0; j < rowString.length; j++) {{
                            const char = rowString[j];
                            if (char >= '1' && char <= '8') {{
                                // Espacios vacíos
                                const emptySquares = parseInt(char);
                                for (let k = 0; k < emptySquares; k++) {{
                                    row.push(null);
                                }}
                            }} else {{
                                // Pieza
                                row.push(char);
                            }}
                        }}
                        board.push(row);
                    }}
                    
                    return board;
                }}
                
                // Crear tablero HTML básico
                function createBasicBoard() {{
                    const boardElement = document.getElementById('board1');
                    const squareSize = {width} / 8;
                    
                    boardElement.innerHTML = '';
                    boardElement.style.width = '{width}px';
                    boardElement.style.height = '{width}px';
                    boardElement.style.position = 'relative';
                    boardElement.style.border = '2px solid #404040';
                    
                    // Crear 64 casillas
                    for (let row = 0; row < 8; row++) {{
                        for (let col = 0; col < 8; col++) {{
                            const square = document.createElement('div');
                            square.style.position = 'absolute';
                            square.style.left = (col * squareSize) + 'px';
                            square.style.top = (row * squareSize) + 'px';
                            square.style.width = squareSize + 'px';
                            square.style.height = squareSize + 'px';
                            square.style.fontSize = (squareSize * 0.7) + 'px';
                            square.style.display = 'flex';
                            square.style.alignItems = 'center';
                            square.style.justifyContent = 'center';
                            
                            // Color de la casilla
                            if ((row + col) % 2 === 0) {{
                                square.style.backgroundColor = '#f0d9b5';
                            }} else {{
                                square.style.backgroundColor = '#b58863';
                            }}
                            
                            square.id = `square-${{row}}-${{col}}`;
                            square.dataset.row = row;
                            square.dataset.col = col;
                            
                            // Event listeners para interactividad
                            square.addEventListener('click', handleSquareClick);
                            square.addEventListener('dragover', handleDragOver);
                            square.addEventListener('drop', handleDrop);
                            
                            boardElement.appendChild(square);
                        }}
                    }}
                    
                    updateDebug('✅ Tablero básico creado (8x8 casillas) con interactividad');
                }}
                
                // Actualizar posición del tablero
                function updateBoardPosition() {{
                    const boardArray = parseFEN(currentPosition);
                    updateDebug('🎯 Actualizando posición: ' + currentPosition.substring(0, 20) + '...');
                    
                    // Limpiar highlights
                    clearHighlights();
                    
                    for (let row = 0; row < 8; row++) {{
                        for (let col = 0; col < 8; col++) {{
                            const square = document.getElementById(`square-${{row}}-${{col}}`);
                            const piece = boardArray[row][col];
                            
                            if (piece && pieceUnicode[piece]) {{
                                square.textContent = pieceUnicode[piece];
                                square.style.color = piece === piece.toUpperCase() ? '#fff' : '#000';
                                square.style.textShadow = '1px 1px 2px rgba(0,0,0,0.5)';
                                
                                // Hacer piezas draggables
                                square.draggable = true;
                                square.addEventListener('dragstart', handleDragStart);
                                square.addEventListener('dragend', handleDragEnd);
                            }} else {{
                                square.textContent = '';
                                square.draggable = false;
                                square.removeEventListener('dragstart', handleDragStart);
                                square.removeEventListener('dragend', handleDragEnd);
                            }}
                        }}
                    }}
                }}
                
                // Manejar click en casilla
                function handleSquareClick(event) {{
                    if (!isInteractive) return;
                    
                    const square = event.currentTarget;
                    const row = parseInt(square.dataset.row);
                    const col = parseInt(square.dataset.col);
                    const piece = square.textContent;
                    
                    updateDebug(`🖱️ Click en casilla ${{row}},${{col}} - Pieza: ${{piece || 'vacía'}}`);
                    
                    if (selectedSquare) {{
                        // Ya hay una casilla seleccionada, intentar mover
                        if (selectedSquare.row === row && selectedSquare.col === col) {{
                            // Deseleccionar la misma casilla
                            clearSelection();
                        }} else {{
                            // Intentar hacer movimiento
                            attemptMove(selectedSquare.row, selectedSquare.col, row, col);
                        }}
                    }} else if (piece) {{
                        // Seleccionar pieza
                        selectSquare(row, col, square);
                    }}
                }}
                
                // Seleccionar casilla
                function selectSquare(row, col, square) {{
                    selectedSquare = {{ row, col }};
                    square.classList.add('highlight-selected');
                    
                    // Calcular movimientos posibles (simplificado)
                    possibleMoves = calculatePossibleMoves(row, col);
                    highlightPossibleMoves();
                    
                    updateDebug(`✅ Seleccionada casilla ${{row}},${{col}} - ${{possibleMoves.length}} movimientos posibles`);
                }}
                
                // Limpiar selección
                function clearSelection() {{
                    selectedSquare = null;
                    possibleMoves = [];
                    clearHighlights();
                    updateDebug('🔄 Selección limpiada');
                }}
                
                // Limpiar highlights
                function clearHighlights() {{
                    const squares = document.querySelectorAll('.square-55d63');
                    squares.forEach(square => {{
                        square.classList.remove('highlight-selected', 'highlight-possible', 'highlight-last-move');
                        // Remover indicadores de movimiento
                        const indicators = square.querySelectorAll('.move-indicator');
                        indicators.forEach(indicator => indicator.remove());
                    }});
                }}
                
                // Resaltar movimientos posibles
                function highlightPossibleMoves() {{
                    possibleMoves.forEach(move => {{
                        const targetSquare = document.getElementById(`square-${{move.row}}-${{move.col}}`);
                        if (targetSquare) {{
                            targetSquare.classList.add('highlight-possible');
                            
                            // Agregar indicador visual si la casilla está vacía
                            if (!targetSquare.textContent) {{
                                const indicator = document.createElement('div');
                                indicator.className = 'move-indicator';
                                targetSquare.appendChild(indicator);
                            }}
                        }}
                    }});
                }}
                
                // Calcular movimientos posibles (versión simplificada)
                function calculatePossibleMoves(row, col) {{
                    const moves = [];
                    const boardArray = parseFEN(currentPosition);
                    const piece = boardArray[row][col];
                    
                    if (!piece) return moves;
                    
                    // Movimientos básicos por tipo de pieza (simplificado)
                    const pieceType = piece.toLowerCase();
                    
                    switch (pieceType) {{
                        case 'p': // Peón
                            moves.push(...calculatePawnMoves(row, col, piece, boardArray));
                            break;
                        case 'r': // Torre
                            moves.push(...calculateRookMoves(row, col, boardArray));
                            break;
                        case 'n': // Caballo
                            moves.push(...calculateKnightMoves(row, col, boardArray));
                            break;
                        case 'b': // Alfil
                            moves.push(...calculateBishopMoves(row, col, boardArray));
                            break;
                        case 'q': // Reina
                            moves.push(...calculateQueenMoves(row, col, boardArray));
                            break;
                        case 'k': // Rey
                            moves.push(...calculateKingMoves(row, col, boardArray));
                            break;
                    }}
                    
                    return moves;
                }}
                
                // Calcular movimientos de peón (simplificado)
                function calculatePawnMoves(row, col, piece, board) {{
                    const moves = [];
                    const isWhite = piece === piece.toUpperCase();
                    const direction = isWhite ? -1 : 1;
                    const startRow = isWhite ? 6 : 1;
                    
                    // Movimiento hacia adelante
                    if (row + direction >= 0 && row + direction < 8 && !board[row + direction][col]) {{
                        moves.push({{ row: row + direction, col }});
                        
                        // Movimiento doble desde posición inicial
                        if (row === startRow && !board[row + 2 * direction][col]) {{
                            moves.push({{ row: row + 2 * direction, col }});
                        }}
                    }}
                    
                    // Capturas diagonales
                    for (let deltaCol of [-1, 1]) {{
                        const newRow = row + direction;
                        const newCol = col + deltaCol;
                        if (newRow >= 0 && newRow < 8 && newCol >= 0 && newCol < 8) {{
                            const target = board[newRow][newCol];
                            if (target && ((isWhite && target === target.toLowerCase()) || (!isWhite && target === target.toUpperCase()))) {{
                                moves.push({{ row: newRow, col: newCol }});
                            }}
                        }}
                    }}
                    
                    return moves;
                }}
                
                // Calcular movimientos de torre
                function calculateRookMoves(row, col, board) {{
                    const moves = [];
                    const directions = [[0, 1], [0, -1], [1, 0], [-1, 0]];
                    
                    for (let [dx, dy] of directions) {{
                        for (let i = 1; i < 8; i++) {{
                            const newRow = row + i * dx;
                            const newCol = col + i * dy;
                            
                            if (newRow < 0 || newRow >= 8 || newCol < 0 || newCol >= 8) break;
                            
                            const target = board[newRow][newCol];
                            if (!target) {{
                                moves.push({{ row: newRow, col: newCol }});
                            }} else {{
                                // Puede capturar si es del color contrario
                                const piece = board[row][col];
                                const isWhite = piece === piece.toUpperCase();
                                const targetIsWhite = target === target.toUpperCase();
                                if (isWhite !== targetIsWhite) {{
                                    moves.push({{ row: newRow, col: newCol }});
                                }}
                                break;
                            }}
                        }}
                    }}
                    
                    return moves;
                }}
                
                // Calcular movimientos de caballo
                function calculateKnightMoves(row, col, board) {{
                    const moves = [];
                    const knightMoves = [
                        [-2, -1], [-2, 1], [-1, -2], [-1, 2],
                        [1, -2], [1, 2], [2, -1], [2, 1]
                    ];
                    
                    const piece = board[row][col];
                    const isWhite = piece === piece.toUpperCase();
                    
                    for (let [dx, dy] of knightMoves) {{
                        const newRow = row + dx;
                        const newCol = col + dy;
                        
                        if (newRow >= 0 && newRow < 8 && newCol >= 0 && newCol < 8) {{
                            const target = board[newRow][newCol];
                            if (!target || (target && ((isWhite && target === target.toLowerCase()) || (!isWhite && target === target.toUpperCase())))) {{
                                moves.push({{ row: newRow, col: newCol }});
                            }}
                        }}
                    }}
                    
                    return moves;
                }}
                
                // Calcular movimientos de alfil (similar a torre pero diagonales)
                function calculateBishopMoves(row, col, board) {{
                    const moves = [];
                    const directions = [[1, 1], [1, -1], [-1, 1], [-1, -1]];
                    
                    for (let [dx, dy] of directions) {{
                        for (let i = 1; i < 8; i++) {{
                            const newRow = row + i * dx;
                            const newCol = col + i * dy;
                            
                            if (newRow < 0 || newRow >= 8 || newCol < 0 || newCol >= 8) break;
                            
                            const target = board[newRow][newCol];
                            if (!target) {{
                                moves.push({{ row: newRow, col: newCol }});
                            }} else {{
                                const piece = board[row][col];
                                const isWhite = piece === piece.toUpperCase();
                                const targetIsWhite = target === target.toUpperCase();
                                if (isWhite !== targetIsWhite) {{
                                    moves.push({{ row: newRow, col: newCol }});
                                }}
                                break;
                            }}
                        }}
                    }}
                    
                    return moves;
                }}
                
                // Calcular movimientos de reina (torre + alfil)
                function calculateQueenMoves(row, col, board) {{
                    return [...calculateRookMoves(row, col, board), ...calculateBishopMoves(row, col, board)];
                }}
                
                // Calcular movimientos de rey
                function calculateKingMoves(row, col, board) {{
                    const moves = [];
                    const directions = [
                        [-1, -1], [-1, 0], [-1, 1],
                        [0, -1],           [0, 1],
                        [1, -1],  [1, 0],  [1, 1]
                    ];
                    
                    const piece = board[row][col];
                    const isWhite = piece === piece.toUpperCase();
                    
                    for (let [dx, dy] of directions) {{
                        const newRow = row + dx;
                        const newCol = col + dy;
                        
                        if (newRow >= 0 && newRow < 8 && newCol >= 0 && newCol < 8) {{
                            const target = board[newRow][newCol];
                            if (!target || (target && ((isWhite && target === target.toLowerCase()) || (!isWhite && target === target.toUpperCase())))) {{
                                moves.push({{ row: newRow, col: newCol }});
                            }}
                        }}
                    }}
                    
                    return moves;
                }}
                
                // Intentar hacer movimiento
                function attemptMove(fromRow, fromCol, toRow, toCol) {{
                    updateDebug(`🎯 Intentando movimiento: ${{fromRow}},${{fromCol}} → ${{toRow}},${{toCol}}`);
                    
                    // Verificar si el movimiento es válido
                    const isValidMove = possibleMoves.some(move => move.row === toRow && move.col === toCol);
                    
                    if (isValidMove) {{
                        executeMove(fromRow, fromCol, toRow, toCol);
                        updateDebug(`✅ Movimiento ejecutado exitosamente`);
                    }} else {{
                        updateDebug(`❌ Movimiento inválido`);
                        updateStatus('❌ Movimiento no válido', 'error');
                    }}
                    
                    clearSelection();
                }}
                
                // Ejecutar movimiento
                function executeMove(fromRow, fromCol, toRow, toCol) {{
                    const boardArray = parseFEN(currentPosition);
                    const piece = boardArray[fromRow][fromCol];
                    const capturedPiece = boardArray[toRow][toCol];
                    
                    // Guardar posición actual en historial
                    gameHistory.push(currentPosition);
                    
                    // Hacer el movimiento en el array
                    boardArray[toRow][toCol] = piece;
                    boardArray[fromRow][fromCol] = null;
                    
                    // Convertir de vuelta a FEN (simplificado)
                    currentPosition = boardArrayToFEN(boardArray);
                    
                    // Actualizar tablero visual
                    updateBoardPosition();
                    
                    // Resaltar último movimiento
                    const fromSquare = document.getElementById(`square-${{fromRow}}-${{fromCol}}`);
                    const toSquare = document.getElementById(`square-${{toRow}}-${{toCol}}`);
                    if (fromSquare) fromSquare.classList.add('highlight-last-move');
                    if (toSquare) toSquare.classList.add('highlight-last-move');
                    
                    // Actualizar estado
                    const moveNotation = `${{String.fromCharCode(97 + fromCol)}}${{8 - fromRow}}-${{String.fromCharCode(97 + toCol)}}${{8 - toRow}}`;
                    updateStatus(`✅ Movimiento: ${{moveNotation}}${{capturedPiece ? ' (captura)' : ''}}`, 'success');
                }}
                
                // Convertir array del tablero a FEN (simplificado)
                function boardArrayToFEN(board) {{
                    let fen = '';
                    
                    for (let row = 0; row < 8; row++) {{
                        let emptyCount = 0;
                        for (let col = 0; col < 8; col++) {{
                            const piece = board[row][col];
                            if (piece) {{
                                if (emptyCount > 0) {{
                                    fen += emptyCount;
                                    emptyCount = 0;
                                }}
                                fen += piece;
                            }} else {{
                                emptyCount++;
                            }}
                        }}
                        if (emptyCount > 0) {{
                            fen += emptyCount;
                        }}
                        if (row < 7) fen += '/';
                    }}
                    
                    fen += ' w KQkq - 0 1'; // Estado adicional simplificado
                    return fen;
                }}
                
                // Manejar drag start
                function handleDragStart(event) {{
                    if (!isInteractive) {{
                        event.preventDefault();
                        return;
                    }}
                    
                    draggedPiece = event.currentTarget;
                    draggedPiece.classList.add('dragging');
                    
                    const row = parseInt(draggedPiece.dataset.row);
                    const col = parseInt(draggedPiece.dataset.col);
                    
                    selectSquare(row, col, draggedPiece);
                    updateDebug(`🔥 Iniciando drag desde ${{row}},${{col}}`);
                }}
                
                // Manejar drag end
                function handleDragEnd(event) {{
                    if (draggedPiece) {{
                        draggedPiece.classList.remove('dragging');
                        draggedPiece = null;
                    }}
                    updateDebug('🔥 Terminando drag');
                }}
                
                // Manejar drag over
                function handleDragOver(event) {{
                    event.preventDefault(); // Permitir drop
                }}
                
                // Manejar drop
                function handleDrop(event) {{
                    event.preventDefault();
                    
                    if (!draggedPiece || !selectedSquare) return;
                    
                    const dropSquare = event.currentTarget;
                    const toRow = parseInt(dropSquare.dataset.row);
                    const toCol = parseInt(dropSquare.dataset.col);
                    
                    updateDebug(`🎯 Drop en ${{toRow}},${{toCol}}`);
                    attemptMove(selectedSquare.row, selectedSquare.col, toRow, toCol);
                }}
                
                // Parsear PGN básico (solo extraer movimientos)
                function parseBasicPGN(pgn) {{
                    try {{
                        updateDebug('📋 Parseando PGN básico...');
                        
                        // Remover metadatos y comentarios
                        let cleanPgn = pgn.replace(/\\[[^\\]]*\\]/g, '');
                        cleanPgn = cleanPgn.replace(/\\{{[^\\}}]*\\}}/g, '');
                        cleanPgn = cleanPgn.replace(/;[^\\r\\n]*/g, '');
                        
                        // Extraer movimientos (patrón básico)
                        const moveMatches = cleanPgn.match(/\\d+\\.\\s*[^\\s]+(?:\\s+[^\\s]+)?/g);
                        
                        if (moveMatches) {{
                            moves = moveMatches;
                            updateDebug('✅ Encontrados ' + moves.length + ' grupos de movimientos');
                            return true;
                        }} else {{
                            updateDebug('⚠️ No se encontraron movimientos en el PGN');
                            return false;
                        }}
                        
                    }} catch (error) {{
                        updateDebug('❌ Error parseando PGN: ' + error.message);
                        return false;
                    }}
                }}
                
                // Inicializar todo
                function initializeStandaloneBoard() {{
                    try {{
                        updateDebug('🎯 Inicializando tablero autónomo...');
                        updateStatus('🎯 Creando tablero...', 'info');
                        
                        // Crear tablero básico
                        createBasicBoard();
                        
                        // Mostrar tablero
                        document.getElementById('loadingIndicator').style.display = 'none';
                        document.getElementById('board1').style.display = 'block';
                        
                        // Actualizar con posición inicial
                        updateBoardPosition();
                        
                        // Procesar PGN si existe
                        if (pgnText && pgnText.trim()) {{
                            if (parseBasicPGN(pgnText)) {{
                                updateStatus('✅ Tablero y PGN cargados (versión básica)', 'success');
                            }} else {{
                                updateStatus('✅ Tablero cargado - PGN inválido', 'info');
                            }}
                        }} else {{
                            updateStatus('✅ Tablero listo - Sin partida', 'success');
                        }}
                        
                        // Configurar controles
                        setupBasicControls();
                        updateDisplay();
                        
                        updateDebug('✅ Inicialización completa');
                        
                    }} catch (error) {{
                        updateDebug('❌ Error: ' + error.message);
                        updateStatus('❌ Error: ' + error.message, 'error');
                    }}
                }}
                
                // Configurar controles básicos
                function setupBasicControls() {{
                    const startBtn = document.getElementById('startBtn');
                    const prevBtn = document.getElementById('prevBtn');
                    const nextBtn = document.getElementById('nextBtn');
                    const endBtn = document.getElementById('endBtn');
                    const flipBtn = document.getElementById('flipBtn');
                    
                    if (startBtn) startBtn.onclick = goToStart;
                    if (prevBtn) prevBtn.onclick = goToPrevious;
                    if (nextBtn) nextBtn.onclick = goToNext;
                    if (endBtn) endBtn.onclick = goToEnd;
                    if (flipBtn) flipBtn.onclick = flipBoard;
                    
                    updateDebug('✅ Controles configurados');
                }}
                
                function updateDisplay() {{
                    const moveNum = currentMoveIndex + 1;
                    const moveNumberEl = document.getElementById('moveNumber');
                    const totalMovesEl = document.getElementById('totalMoves');
                    
                    if (moveNumberEl) moveNumberEl.textContent = moveNum;
                    if (totalMovesEl) totalMovesEl.textContent = moves.length;
                    
                    const startBtn = document.getElementById('startBtn');
                    const prevBtn = document.getElementById('prevBtn');
                    const nextBtn = document.getElementById('nextBtn');
                    const endBtn = document.getElementById('endBtn');
                    
                    if (startBtn) startBtn.disabled = (currentMoveIndex < 0);
                    if (prevBtn) prevBtn.disabled = (currentMoveIndex < 0);
                    if (nextBtn) nextBtn.disabled = (currentMoveIndex >= moves.length - 1);
                    if (endBtn) endBtn.disabled = (currentMoveIndex >= moves.length - 1);
                }}
                
                function goToStart() {{
                    currentPosition = 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1';
                    currentMoveIndex = -1;
                    updateBoardPosition();
                    updateDisplay();
                    updateDebug('🔄 Volviendo al inicio');
                }}
                
                function goToPrevious() {{
                    if (currentMoveIndex >= 0) {{
                        currentMoveIndex--;
                        // En versión básica, solo volver al inicio por ahora
                        if (currentMoveIndex < 0) {{
                            currentPosition = 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1';
                        }}
                        updateBoardPosition();
                        updateDisplay();
                        updateDebug('⏪ Movimiento anterior');
                    }}
                }}
                
                function goToNext() {{
                    if (currentMoveIndex < moves.length - 1) {{
                        currentMoveIndex++;
                        // En versión básica, mantenemos posición inicial
                        // TODO: Implementar lógica de movimientos
                        updateDisplay();
                        updateDebug('⏩ Siguiente movimiento (básico)');
                    }}
                }}
                
                function goToEnd() {{
                    currentMoveIndex = moves.length - 1;
                    // En versión básica, mantenemos posición inicial
                    updateDisplay();
                    updateDebug('⏭️ Final de la partida (básico)');
                }}
                
                function flipBoard() {{
                    // TODO: Implementar voltear tablero
                    updateDebug('🔄 Voltear tablero (pendiente)');
                }}
                
                // Iniciar después de cargar la página
                window.onload = function() {{
                    updateDebug('🚀 Página cargada, inicializando...');
                    setTimeout(initializeStandaloneBoard, 100);
                }};
                
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
_standalone_chess_visualizer = None

def get_standalone_chess_visualizer() -> StandaloneChessBoardVisualizer:
    """Obtener visualizador autónomo de ajedrez"""
    global _standalone_chess_visualizer
    if _standalone_chess_visualizer is None:
        _standalone_chess_visualizer = StandaloneChessBoardVisualizer()
    return _standalone_chess_visualizer