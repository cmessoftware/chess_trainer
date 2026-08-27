import { Chessboard } from 'react-chessboard'

/**
 * Vite/React board aligned with docs/ai_chess_coach_course/ui/chessinsight_board/CONTRACT.md
 * Jupyter uses the same props via Chessground (vanilla JS).
 */
export default function ChessinsightBoard({
    fen,
    orientation = 'white',
    lastMove = null,
    viewOnly = false,
    onMove,
    boardWidth = 420,
}) {
    const lastMoveStyles = squaresFromUci(lastMove)

    const handleDrop = (sourceSquare, targetSquare) => {
        if (viewOnly) {
            return false
        }
        if (onMove) {
            onMove({ from: sourceSquare, to: targetSquare, fen })
        }
        return true
    }

    return (
        <Chessboard
            position={fen}
            boardWidth={boardWidth}
            boardOrientation={orientation === 'black' ? 'black' : 'white'}
            arePiecesDraggable={!viewOnly}
            onPieceDrop={handleDrop}
            customSquareStyles={lastMoveStyles}
            animationDuration={200}
        />
    )
}

function squaresFromUci(uci) {
    if (!uci || String(uci).length < 4) {
        return {}
    }
    const from = uci.slice(0, 2)
    const to = uci.slice(2, 4)
    const paint = { backgroundColor: 'rgba(255, 255, 0, 0.45)' }
    return { [from]: paint, [to]: paint }
}
