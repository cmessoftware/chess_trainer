# ACC UI — current architecture (U00-001)

**Date:** 2026-09-07  
**ID:** U00-001  
**Scope:** Vite app `src/frontend` plus the Jupyter board contract. No code changes.  
**Plan:** [`../roadmap/12-acc-ui-renewal-implementation-plan.md`](../roadmap/12-acc-ui-renewal-implementation-plan.md)  
**Brief:** [`acc_ui_improvements_specs.md`](acc_ui_improvements_specs.md)

Grep in this report is **report mode** (U00-001). A failing CI grep is **U03-004**, after the purge.

This file also records game state (U00-002), PGN/FEN/API (U00-003), and Jupyter vs Vite contract gaps (U00-004). Those IDs do not need empty follow-up branches unless the inventory goes stale.

---

## CURRENT ARCHITECTURE

```text
Browser
  App.tsx (MUI light, React Router)
    ChessBoardPage  →  ChessBoard.jsx
                         ├── useChessGame.js     (chess.js + linear UCI list)
                         ├── SimpleChessBoard    (Unicode/FEN text grid)  ← what users see
                         ├── MovesList           (flat index list)
                         ├── StockfishGameLogic  (chess.js play vs engine)
                         └── analysisService     POST /chess/position-analysis
    GamesPage / ImportPage / reports / auth
    PlayStockfishPage.jsx  (NOT in App.tsx routes)

Jupyter (course)
  interactive_board.py → mount.js → Chessground 9.2.1 (CDN)
  Same prop names as ChessinsightBoard (react-chessboard), different renderer

FastAPI
  GET  /chess/games/:id          → moves as UCI-like strings
  POST /chess/position-analysis  → evaluation / best_move
  POST /chess/validate-move
  POST /chess/analyze-game
```

There is **no** Chessground, **no** chessops, **no** move tree, **no** `ChessGameController` in the Vite app.

### Routes that touch chess

| Route | Page | Board |
| ----- | ---- | ----- |
| `/chess-board` | `ChessBoardPage.jsx` | `ChessBoard` → `SimpleChessBoard` |
| `/chess-board/:gameId` | same | loads `useChessGame.loadGame` |
| `/games` | `GamesPage.tsx` | navigates to board with `mode` |
| Play page | `PlayStockfishPage.jsx` | `SimpleChessBoard` + `chess.js` — **not registered** in `App.tsx` |

`ChessBoardPage` modes: query/state `mode` default `'view'`. `ChessBoard.jsx` also has `'play'` (Stockfish) mixed in the same component.

---

## DEPENDENCIES TO REMOVE

From `src/frontend/package.json` (2026-09-07):

| Package | Version | Used in `src/`? |
| ------- | ------- | ---------------- |
| `chess.js` | ^1.4.0 | Yes |
| `react-chessboard` | ^5.8.6 | Yes (two files; **not** the visible analysis board) |
| `chessboardjsx` | ^2.4.7 | **No imports** (dead dependency) |
| `chessboard.js` | — | **Absent** (spec name only) |

Also in lockfile: `src/frontend/package-lock.json` (`chess.js`, `react-chessboard`, `chessboardjsx`).

Not present: `chessops`, `chessground`, `@lichess-org/chessground`.

Jupyter pulls Chessground from jsDelivr (`chessground@9.2.1`), not from npm.

### Grep report (frontend `src/`)

| Pattern | Hits |
| ------- | ---- |
| `from 'chess.js'` / `from "chess.js"` | `hooks/useChessGame.js`, `components/chess/ChessBoard.jsx`, `components/chess/StockfishGameLogic.js`, `pages/PlayStockfishPage.jsx` |
| `react-chessboard` | `ChessinsightBoard.jsx`, `ChessBoardAlternative.jsx` |
| `chessboardjsx` | `package.json` / lockfile only |
| `chessboard.js` | none |
| `SimpleChessBoard` | `ChessBoard.jsx`, `PlayStockfishPage.jsx`, `SimpleChessBoard.jsx` |
| `ChessBoardAlternative` | definition only (no page import found) |
| `ChessinsightBoard` | definition; course tests/docs; **not** used by `ChessBoard.jsx` |

Other repo mentions (not Vite runtime): `src/config/init_frontend.py` (print), `tests/frontend/test_chess_board_integration.js` (manual console script), Streamlit `src/streamlit/components/chess_board_simple.py` (separate product surface; **out of this epic** unless explicitly added).

---

## CUSTOM CODE TO REMOVE

Replace after chessops + Chessground work; do not delete in P0.

| File | Why it dies |
| ---- | ----------- |
| `SimpleChessBoard.jsx` | Custom FEN parse + Unicode pieces; no drag/drop |
| `ChessBoardAlternative.jsx` | Unused `react-chessboard` wrapper |
| `ChessinsightBoard.jsx` | `react-chessboard` adapter for the Jupyter contract |
| `useChessGame.js` | `chess.js` as source of truth; parallel FEN/index |
| `StockfishGameLogic.js` | `chess.js`; promotion hardcoded to `q` |
| Legal-move / FEN helpers inside `SimpleChessBoard.parseFEN` | chessops already does this |
| `gameVersion` bump to force React updates | symptom of duplicated state |

Keep the **page shells** (`ChessBoardPage`, games list, import, auth) and rewrite only the chess domain they call.

---

## COMPONENTS TO REPLACE

| Current | Replace with (later IDs) |
| ------- | ------------------------ |
| `SimpleChessBoard` | `ChessBoardAdapter` + Chessground (U02-001, U02-007) |
| `ChessinsightBoard` | same adapter; keep **prop names** from CONTRACT |
| `ChessBoardAlternative` | delete (U03-003) |
| `MovesList` (flat `gameHistory` index) | tree notation after P4; until then list driven by `MoveTree` main line |
| `useChessGame` | `ChessGameController` (U01-004) |
| MUI `theme.palette.mode = 'light'` in `App.tsx` | dark tokens (U02-008); keep MUI |

`ChessBoard.jsx` (~748 lines) is a **god component** (view + play + analysis toggle + logging). Split when replacing boards; not a P0 code task.

---

## COMPONENTS TO KEEP

| Keep | Role |
| ---- | ---- |
| `App.tsx` router, `ProtectedRoute`, `Navigation` | Product shell |
| `GamesPage`, `ImportPage`, reports, login, admin | Out of chess-renderer epic |
| `services/api.js`, `services/games.js`, `services/auth.js` | HTTP |
| `analysisService.js` | Keep as API client; **do not** treat it as chess rules. Later panels consume 07 JSON, not ad-hoc eval in the client |
| MUI + Emotion + React Query | Stay |
| Jupyter `mount.js` + Chessground CDN | Sibling renderer; update CONTRACT in U02-001 |
| FastAPI game and analysis endpoints | No backend rewrite in this epic |

Testing Library packages are already in `package.json` but **unused** (no `npm test`). Harness is U00-006.

---

## Game state (spec §27) — U00-002

`useChessGame.js` keeps **independent** fields that can drift:

| Field | Role |
| ----- | ---- |
| `game` | `chess.js` `Chess` instance |
| `currentFen` | duplicate of `game.fen()` |
| `fen` export | alias of `currentFen` |
| `gameHistory` | linear UCI strings |
| `currentMoveIndex` | `-1` = startpos; integer into `gameHistory` |
| `gameVersion` | integer to force memo refresh |
| `gameData` | API metadata + `sanMoves` / `uciMoves` |
| `playGame` (in `ChessBoard.jsx`) | **second** `chess.js` instance in play mode |

`makeMove` updates `game`/`currentFen` but **does not** append to `gameHistory` → analysis sidelines are not a tree and can desync from the list.

Target (spec): one `currentMoveId` (or equivalent) on a `MoveTree`; FEN derived from the node.

---

## PGN / FEN / navigation — U00-003

### How a game is loaded

1. UI: `GET /chess/games/:gameId` via `gamesService.getGame`.
2. Payload used: `data.moves[]` treated as **UCI (or chess.js `move()` strings)**.
3. Frontend replays each string with `chess.js` to build SAN, then **resets** to startpos for navigation.
4. There is **no PGN parser** in the Vite chess hook. Variants, comments, NAGs are not represented.
5. Optional `getGameMoves(gameId)` exists (`GET .../moves`) and is not the main `loadGame` path.

### How FEN is calculated

Replay `gameHistory[0..=index]` on a fresh `Chess()`. Stored again in `currentFen`. Invalid moves are skipped with a warning (history can be shorter than the API list).

### Navigation

Buttons in `ChessBoard` / `MovesList` call `goToStart` / `previousMove` / `nextMove` / `goToEnd` / `goToMove(index)`. **No** keyboard Home/End/arrows in the hook. Linear only.

### Backend analysis from the board

`analysisService.getQuickEvaluation(fen)` → `POST /chess/position-analysis` `{ fen, depth }` (depth 5). This is **not** Module 07 review-pack / STOP / MultiPV. Do not reuse it as criticality.

---

## Jupyter vs Vite CONTRACT — U00-004

File: `docs/ai_chess_coach_course/ui/chessinsight_board/CONTRACT.md`

| Prop | Jupyter Chessground | Vite `ChessinsightBoard` |
| ---- | ------------------- | ------------------------ |
| `fen` | yes | yes |
| `orientation` | yes | yes |
| `lastMove` UCI | yes | yes (square styles) |
| `viewOnly` | yes | yes (`arePiecesDraggable`) |
| `dests` | yes (CG dest map) | **ignored** (prop not wired) |
| `onMove` | DOM `chessinsight-move` `{ from, to, fen }` | `onMove({ from, to, fen })` — **does not apply** the move itself (`return true` after callback) |
| Promotions | not in contract | not handled |
| Arrows / circles | not in contract | not handled |

**Product analysis UI does not mount `ChessinsightBoard` at all**; it mounts `SimpleChessBoard`, which implements **none** of drag, dests, last-move highlight as CG would.

Course test: `tests/docs_courses/test_f07_003_engine_eval.py` asserts `mountChessinsightBoard` in HTML.

---

## Tests today

| Location | What it is |
| -------- | ---------- |
| `src/frontend` | **No** `*.test.*`; `package.json` has `build`/`lint` only |
| `tests/frontend/test_chess_board_integration.js` | Node console script, not Vitest |
| Course | Jupyter board string checks |

U00-006 must add `npm test` before domain tests in P1.

---

## Keep / drop summary

| Drop (after P2 works) | Keep |
| --------------------- | ---- |
| `chess.js`, `react-chessboard`, `chessboardjsx` | Router, auth, games/import/reports |
| Custom FEN grid, unused alternative board | FastAPI clients |
| Dual FEN+index state | Jupyter CG **if** CONTRACT stays aligned |
| Client-side “quick eval” as if it were 07 STOP | MUI (restyle later) |

---

## Backlog

This document is **Done** for U00-001. Implementation starts later on `features/acc_ui_p0_u00-006_vitest_harness` then `features/acc_ui_p1_u01-001_add_chessops` (see plan §10). Do not implement chess UI on this branch.
