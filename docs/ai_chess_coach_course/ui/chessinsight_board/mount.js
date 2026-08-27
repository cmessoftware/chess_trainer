/**
 * ChessInsight board mount (vanilla JS).
 * Same props as React `ChessinsightBoard`: fen, orientation, lastMove, viewOnly, dests.
 * After each legal drop, chess.js updates FEN + dests so pieces stay movable.
 */
import { Chessground } from 'https://cdn.jsdelivr.net/npm/chessground@9.2.1/+esm';
import { Chess } from 'https://cdn.jsdelivr.net/npm/chess.js@1.4.0/+esm';

function destsFromChess(chess) {
  const dests = new Map();
  for (const move of chess.moves({ verbose: true })) {
    const targets = dests.get(move.from) || [];
    if (!targets.includes(move.to)) targets.push(move.to);
    dests.set(move.from, targets);
  }
  return dests;
}

function lastMoveSquares(uci) {
  if (!uci || String(uci).length < 4) return undefined;
  return [uci.slice(0, 2), uci.slice(2, 4)];
}

function turnColor(chess) {
  return chess.turn() === 'b' ? 'black' : 'white';
}

export function mountChessinsightBoard(element, props) {
  const chess = new Chess(props.fen);
  const orientation = props.orientation === 'black' ? 'black' : 'white';
  const viewOnly = Boolean(props.viewOnly);

  const reportTry = (text) => {
    const out = element.parentElement?.querySelector('[data-role="last-try"]');
    if (out) out.textContent = text;
  };

  const afterMove = (orig, dest) => {
    const played = chess.move({ from: orig, to: dest, promotion: 'q' });
    if (!played) {
      sync();
      reportTry(`Ilegal: ${orig}${dest}`);
      return;
    }
    sync();
    element.dispatchEvent(
      new CustomEvent('chessinsight-move', {
        detail: { from: orig, to: dest, san: played.san, fen: chess.fen() },
        bubbles: true,
      })
    );
    reportTry(`${played.color === 'w' ? 'Blancas' : 'Negras'}: ${played.san}  (${chess.fen().split(' ')[1] === 'w' ? 'mueven blancas' : 'mueven negras'})`);
  };

  let ground;

  function movableConfig() {
    if (viewOnly || (typeof chess.isGameOver === 'function' && chess.isGameOver())) {
      return { free: false, color: undefined, dests: new Map() };
    }
    const turn = turnColor(chess);
    return {
      free: false,
      color: turn,
      dests: destsFromChess(chess),
      events: { after: afterMove },
    };
  }

  function sync() {
    const history = chess.history({ verbose: true });
    const last = history[history.length - 1];
    ground.set({
      fen: chess.fen(),
      turnColor: turnColor(chess),
      lastMove: last ? [last.from, last.to] : lastMoveSquares(props.lastMove),
      movable: movableConfig(),
    });
  }

  ground = Chessground(element, {
    fen: chess.fen(),
    orientation,
    turnColor: turnColor(chess),
    lastMove: lastMoveSquares(props.lastMove),
    viewOnly,
    draggable: { enabled: !viewOnly },
    selectable: { enabled: !viewOnly },
    movable: movableConfig(),
    premovable: { enabled: false },
  });

  return ground;
}
