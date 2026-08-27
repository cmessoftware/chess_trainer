# ChessInsight board contract

Shared props for Jupyter (vanilla JS + Chessground) and the Vite app (`react-chessboard`).

| Prop | Type | Meaning |
|---|---|---|
| `fen` | string | Position to show |
| `orientation` | `"white"` \| `"black"` | Side at the bottom |
| `lastMove` | UCI string (`e2e4`) | Highlight last move |
| `viewOnly` | boolean | If true, pieces cannot be dragged |
| `dests` | `{ [from]: string[] }` | Legal targets (Jupyter / Chessground) |
| `onMove` | `( { from, to } ) => void` | Drop handler (React) |

Events (Jupyter): DOM `chessinsight-move` with `{ from, to, fen }`.

React: `src/frontend/src/components/chess/ChessinsightBoard.jsx`.
