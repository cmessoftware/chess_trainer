# ACC UI renewal — implementation plan

## Objective

Replace the Vite/React chess layer (`chess.js` + `react-chessboard` + custom boards) with **chessops + Chessground + a real move tree**, then build an analysis workstation UI (STOP, candidates, engines, calculation) **without rewriting FastAPI**.

```text
Audit (no dual boards)
→ chessops + ChessGameController + MoveTree (tests)
→ Chessground via ChessBoardAdapter
→ delete chess.js / react-chessboard / chessboardjsx / custom boards
→ Lichess-like variations
→ Analysis panels (07/08 contracts only)
→ Engine bar + MultiPV (Stockfish first)
→ Calculation training (frozen board)
```

**Last status update:** 2026-09-07. Documentation only. No UI code in this increment.

### Current progress

| Area | Status | Notes |
| ---- | ------ | ----- |
| Source spec | 📄 Draft | [`../drafts/acc_ui_improvements_specs.md`](../drafts/acc_ui_improvements_specs.md) |
| This plan | ✅ Written | Implementation authority for `ext-ui` chess renewal |
| Frontend chess today | 📄 Inventoried | See [`../drafts/acc_ui_current_architecture.md`](../drafts/acc_ui_current_architecture.md) (U00-001). Still legacy code. |
| Frontend unit tests | ⬜ Missing | `@testing-library/*` in `package.json`; **no** `npm test` script, **no** `*.test.*` |
| Module 07/08 UI contracts | ⬜ Partial | 07 P0 exists in course `analysis/`; STOP/Lc0/cognitive UI **must not invent** fields the API does not send |

### Naming

| Item | Convention |
| ---- | ---------- |
| Feature IDs | `U00-001` … `U07-00n` (phase prefix) |
| Git branch | `features/acc_ui_<phase>_<taskid>_<short_slug>` |
| Example | `features/acc_ui_p1_u01-003_move_tree` |
| Phase token | `p0` … `p7` (lowercase) |
| Task id in branch | `u01-003` (lowercase, hyphen) |

Repo F07 items stay on `feature/07_<id>_<slug>`. This UI epic uses **`features/acc_ui_…`** as requested. One ID per branch. Do not mix another `Uxx` into that branch.

---

## Coherence with the draft spec and the repo

### What is coherent

- Single chess stack: Chessground (view) + chessops (rules) + own MoveTree.
- Chessground must not know FastAPI, Stockfish, ML, Lc0, RAG, or criticality.
- One source of truth for the selected node (`currentMoveId` → FEN), not parallel `currentFen` / `gameIndex`.
- Do not put engine lines on the game tree without an explicit user action.
- Do not rewrite the backend; UI presents contracts.
- Desktop-first analysis workstation, not a generic dashboard-first layout.
- Delete old chess libraries after the new path can load and navigate a full game (§51 of the spec).

### Snapshot of the current frontend (audit seed; Phase 0 must confirm)

| Piece | Location | Spec impact |
| ----- | -------- | ----------- |
| `chess.js` | `package.json`; `useChessGame.js`; `ChessBoard.jsx`; `PlayStockfishPage.jsx`; `StockfishGameLogic.js` | Must go after Phase 2 works |
| `react-chessboard` | `ChessinsightBoard.jsx`, `ChessBoardAlternative.jsx` | Must go |
| `chessboardjsx` | `package.json` only (no `src/` import found) | Spec never named it; **still remove** |
| `chessboard.js` | **Not present** | Spec §3/§39 lists it; treat as “must not appear”, not as a current dep |
| Custom board | `SimpleChessBoard.jsx` (used by `ChessBoard.jsx` and play page) | Forbidden custom renderer |
| Linear game state | `useChessGame`: `game` + `currentFen` + `currentMoveIndex` + `gameHistory` | Violates spec §27 |
| Jupyter board | `docs/ai_chess_coach_course/ui/chessinsight_board/` already **Chessground** | Product React board is **react-chessboard** with the same prop contract |
| Theme | `App.tsx` MUI `mode: 'light'` | Spec §38 requires dark + tokens |
| Play mixed into analysis | `ChessBoard.jsx` + `StockfishGameLogic.js` | Spec is an analysis workstation; play is a separate mode |
| Tests | none under `src/frontend` | Spec Phase 3 `npm test` cannot pass until a runner exists |

### Gaps and conflicts (resolve before coding)

| Topic | Issue | Decision for this plan |
| ----- | ----- | ---------------------- |
| **Forbidden libs vs `package.json`** | Spec bans `chessboard.js`; repo has unused **`chessboardjsx`**. | Ban list = spec **plus** `chessboardjsx`. Search both. |
| **Two Chessgrounds** | Jupyter already uses Chessground; Vite uses `react-chessboard` behind `ChessinsightBoard`. Spec says “no two board systems”. | Vite app: one React Chessground. Jupyter may keep vanilla Chessground if it implements **the same CONTRACT**. Update `CONTRACT.md` in U02-001. Do not run two renderers **inside the Vite app**. |
| **Phase 1 MoveTree vs Phase 4 variations** | Spec §42 creates `MoveTree` before UI; §45 is “Lichess variations”. | **P1:** tree that can store a **linear main line** (and empty `children`). **P4:** create/promote/delete branches + PGN round-trip of RAVs. |
| **TypeScript everywhere** | Spec stack is TS; chess UI is mostly `.jsx`; `App.tsx` already exists. | New chess domain (`controller`, `tree`, `adapter`) **TypeScript only**. Pages migrate when they touch the board. Do not convert auth/admin in this epic. |
| **`npm test`** | Spec Phase 3 requires it; there is no test script. | **U00-006** adds Vitest + Testing Library **before** Phase 1 domain tests. |
| **MUI vs “not SaaS”** | App is MUI; spec wants ChessBase/Lichess workstation. | Keep MUI as primitives. **Do not** restyle the whole product in Phase 1. Workstation **shell** (dark tokens + board-first grid) is **U02-008**. No second UI framework. |
| **Eval as “87% probability”** | Spec mock layout shows `Probability 87%`. Module 08 forbids treating cp as win probability. | UI may show `errorProbability` **only** if the API sends a calibrated field. Never derive % from SF cp. STOP uses **explicit text** (`NORMAL` / `CONSIDER` / `CALCULATE` / `CRITICAL`), not color-only. |
| **Lc0 panel** | Spec layout and Phase 6 show SF + Lc0. Lc0 is **not** a Module 07 MVP producer. | Engine UI: Stockfish (or existing analysis payload) first. Lc0 = empty/disabled state until a backend contract exists. No fake Lc0 numbers. |
| **Analysis panels vs 07** | `PositionAnalysis.shouldStop` / signals / candidate types need 07/08. 07 criticality is still **DROP-led**; F07-009+ incomplete. | Phase 5 **renders JSON**. Missing fields → `UNKNOWN` / hide / `NEEDS_REVIEW`. **No client-side criticality.** Gate: review-pack or equivalent API; if missing, fixture JSON only. |
| **Candidate labels** (`forcing` / `positional`) | F07-017/018 not done. | Show SAN + engine eval. Type/purpose only if backend sends them. |
| **chessops `variants`** | Spec §5 lists variants. Product is standard chess. | **Standard chess only.** No Chess960/antichess in this epic. |
| **Premoves** | Spec §4 “if required later”. Analysis board does not need them. | Out of scope until a play-clock mode. |
| **Play vs analysis** | Spec is analysis; `ChessBoard` also plays Stockfish. | After P3, play page must use the **same** adapter+controller. Do not add new play features here. Promotion always `q` in `StockfishGameLogic` is a known bug; fix only when that file is rewritten onto chessops (U02-007). |
| **§51 vs Phase 5–7** | “Delete old libs before new features” vs later analysis/engine/calculation. | **Hard gate:** no U05/U06/U07 until U03 (purge) is Done. |
| **OpenSpec** | `docs/ai_chess_coach/README.md` requires OpenSpec for requirement changes. | This file is the catalog. An OpenSpec change can wrap the epic later; **do not block P0 audit** on OpenSpec. |
| **Backend rewrite** | Spec forbids it, but engine/STOP need APIs. | UI consumes existing FastAPI. New endpoints are **separate backend IDs**, not this epic. Fixtures unblock UI. |

### Suggested spec vs this plan

The draft is an architecture brief: phases exist, but no IDs, no repo inventory, no 07 gate, no test list, and `chessboard.js` does not match `package.json`. **This file** is the implementation catalog. Do not implement the draft as a single PR.

---

## Principles

- One ID, one branch, one PR.
- Chessground is a rendering layer, never the source of truth.
- chessops owns legality, FEN, SAN/UCI, promotion. Do not reimplement.
- No dual board libraries in the Vite app after Phase 3.
- Do not invent analysis, STOP, or engine scores in the browser.
- Missing backend data → explicit empty/`UNKNOWN`, never placeholders that look real.
- Mandatory tests listed per ID **must** exist before the ID is Done.
- Do not start Phase 5+ until Phase 3 purge is Done.

---

## 1. Module breakdown

| Submodule | Spec map | Responsibility |
| --------- | -------- | -------------- |
| 00 Audit + harness | §40, §51 | Inventory, Vitest, branch rules, CONTRACT |
| 01 Chess domain | §42, §8, §13, §17–18, §27–29 | chessops, controller, linear tree, PGN/FEN load |
| 02 Chessground | §43, §4, §7, §9–10, §36–38 | Adapter, replace boards, dark workstation shell |
| 03 Purge | §44, §39, §49 | Remove legacy chess deps and custom boards |
| 04 Variations | §45, §13–16, §22–23 | Branch, promote, delete, PGN RAVs |
| 05 Analysis UI | §46, §30–34 | STOP, candidates, signals (API/fixtures) |
| 06 Engine UI | §47, §19–21 | Eval bar, MultiPV, arrows; SF first |
| 07 Calculation | §48, §24–26 | Frozen board, calculation tree, compare |

---

## 2. Feature catalog

### Status legend

| Status | Meaning |
| ------ | ------- |
| ⬜ Todo | Not started (default) |
| 🟡 In Progress | Implementation underway |
| 🧪 In Testing | Implemented; under validation |
| ❌ Canceled | Out of scope or superseded |
| ✅ Done | Completed and accepted |

### Mandatory test columns

Every ID lists **Mandatory tests**. Those are the Done gate for that branch. Prefer Vitest unit tests for domain; RTL for adapter/components; a small PGN fixture set (no live Stockfish in unit tests).

---

### 00 — Audit and test harness (spec Phase “first work”)

| ID | Feature | Input | Verifiable output | Mandatory tests | Priority | Status | Branch slug | Comments |
| -- | ------- | ----- | ----------------- | --------------- | -------- | ------ | ----------- | -------- |
| U00-001 | Chess dependency inventory | `src/frontend/package.json`, lockfile, `src/` | Markdown inventory: deps, imports, wrappers, keep/drop | Script or test that **fails** if `chess.js` / `react-chessboard` / `chessboardjsx` / `chessboard.js` appear **after** Phase 3; in P0 the same grep runs in **report mode** (does not fail CI yet) | P0 | ✅ Done | `inventory` | [`../drafts/acc_ui_current_architecture.md`](../drafts/acc_ui_current_architecture.md) |
| U00-002 | Game-state inventory | `useChessGame`, `ChessBoard.jsx`, pages | List of parallel state fields vs spec §27 | Review checklist in inventory doc; no code | P0 | ✅ Done | `state_audit` | Covered in U00-001 report; no extra branch |
| U00-003 | PGN/FEN/API inventory | `games.js`, import page, FastAPI game payload | How PGN/moves/FEN enter the UI today | Load path documented (UCI list, no PGN parser) | P0 | ✅ Done | `api_audit` | Covered in U00-001 report |
| U00-004 | Jupyter vs Vite contract | `CONTRACT.md`, `mount.js`, `ChessinsightBoard.jsx` | Gap list (dests, events, promotions) | Gap table in U00-001 (CONTRACT.md update is U02-001) | P0 | ✅ Done | `board_contract` | Covered in U00-001 report |
| U00-005 | Scope freeze | This plan + spec | Written out-of-scope: variants, premoves, Lc0 live, MUI rewrite, backend | Checklist in this file §5 | P0 | ⬜ Todo | `scope_freeze` | Docs only |
| U00-006 | Vitest + RTL harness | `src/frontend` | `npm test` runs Vitest; one smoke test | `npm test` exit 0; smoke test `true` | P0 | ⬜ Todo | `vitest_harness` | **First code branch of the epic** (harness only) |

---

### 01 — Chess model (spec Phase 1)

| ID | Feature | Input | Verifiable output | Mandatory tests | Priority | Status | Branch slug | Comments |
| -- | ------- | ----- | ----------------- | --------------- | -------- | ------ | ----------- | -------- |
| U01-001 | Add `chessops` | package.json | Dependency pinned; no Chessground yet | Import `parseFen` in a unit test | P0 | ⬜ Todo | `add_chessops` | Do not add Chessground here |
| U01-002 | `ChessPosition` DTO | FEN string | Position: STM, castling, EP, legal UCI list via chessops | Invalid FEN throws; startpos 20 legal moves; black-to-move fixture | P0 | ⬜ Todo | `chess_position` | Standard chess only |
| U01-003 | `MoveTree` linear | UCI/SAN sequence | Nodes with id, parent, fenBefore/After, ply, `isMainLine` | Scholar’s mate fixture: 7 plies; `goTo` by id restores FEN | P0 | ⬜ Todo | `move_tree` | `children` array exists but stays empty until P4 |
| U01-004 | `ChessGameController` | FEN/PGN/UCI | `loadFen`, `loadPgn` (main line), `makeMove`, `getLegalMoves`, first/prev/next/last, `goToMove` | PGN mainline round-trip FEN; illegal move rejected; promotion UCI `e7e8q` | P0 | ⬜ Todo | `game_controller` | No chess.js |
| U01-005 | Single cursor | `currentMoveId` | FEN derived from node; no stored duplicate FEN in controller | After `next()`, `getFen()` equals node `fenAfter` | P0 | ⬜ Todo | `current_move_id` | |
| U01-006 | PGN import mainline | PGN text | Tree = main line; comments/NAGs stored on nodes if chessops/pgn parser allows | PGN with comment on move 3; comment preserved on node | P0 | ⬜ Todo | `pgn_mainline` | RAVs ignored or stored unparsed until P4 — **document which** |
| U01-007 | FEN session | Arbitrary FEN | Analysis from non-startpos; copy FEN | Load midgame FEN; `first()` stays that root | P0 | ⬜ Todo | `fen_session` | Spec §18 |
| U01-008 | Store slices (types) | Spec §28 | TS types `GameState` / `AnalysisState` / `EngineState` / `UiState`; game slice wired | Type-only + controller holds `GameState` | P1 | ⬜ Todo | `store_types` | No Redux requirement; React context/zustand later if needed |

---

### 02 — Chessground (spec Phase 2)

| ID | Feature | Input | Verifiable output | Mandatory tests | Priority | Status | Branch slug | Comments |
| -- | ------- | ----- | ----------------- | --------------- | -------- | ------ | ----------- | -------- |
| U02-001 | Chessground + `ChessBoardAdapter` | Controller dests/FEN | Adapter API spec §7; **only** adapter talks to Chessground | Adapter unit tests with mock CG: `setPosition`, `setDests`, `setLastMove`, `flip` | P0 | ⬜ Todo | `board_adapter` | |
| U02-002 | Destinations + last move | Legal UCI from chessops | Dest map in Chessground shape; last move from/to | Given FEN+move, dests include only legal targets | P0 | ⬜ Todo | `dests_lastmove` | |
| U02-003 | Drag + click-to-move | User gestures | Legal moves applied via controller; illegal ignored | RTL or adapter callback tests: legal drop calls `makeMove`; illegal does not | P0 | ⬜ Todo | `drag_click` | |
| U02-004 | Promotion UI | Pawn to 8th/1st | User chooses piece; UCI includes promotion | Four promotion choices; cancel leaves position unchanged | P0 | ⬜ Todo | `promotion` | chessops validates |
| U02-005 | Keyboard + buttons nav | Arrow keys, Home/End | Same as controller first/prev/next/last | Keydown tests or controller already covered + thin hook test | P0 | ⬜ Todo | `navigation` | Spec §10 |
| U02-006 | Annotations model | `BoardAnnotation[]` | Adapter draws arrows/circles/squares; semanticType → color map | Snapshot or query: one arrow candidate, one threat circle | P1 | ⬜ Todo | `annotations` | Right-click can be stub |
| U02-007 | Replace product boards | `ChessBoard.jsx`, `ChessinsightBoard`, play page | All user-visible boards use adapter | Grep test: `SimpleChessBoard` / `react-chessboard` unused in pages | P0 | ⬜ Todo | `replace_boards` | Play uses same adapter |
| U02-008 | Workstation shell + dark tokens | Spec §9, §36–38 | Board-first desktop grid; CSS tokens; MUI dark | Token test or visual checklist; no hex in board components | P1 | ⬜ Todo | `shell_dark` | Analysis **panels can be placeholders** |
| U02-009 | Read-only vs analysis mode | `movable` flag | Read-only: no piece moves; nav+annotations still work | `setMovable(false)` then drop ignored | P1 | ⬜ Todo | `readonly_mode` | Spec §23 |

**Phase 2 completion (spec §43):** FEN, orientation, legal moves, drag, click-to-move, promotions, last move, highlights.

---

### 03 — Purge legacy (spec Phase 3)

| ID | Feature | Input | Verifiable output | Mandatory tests | Priority | Status | Branch slug | Comments |
| -- | ------- | ----- | ----------------- | --------------- | -------- | ------ | ----------- | -------- |
| U03-001 | Remove chess.js usage | All TS/JS | Zero imports | CI grep **fails** on `from 'chess.js'` / `from "chess.js"` | P0 | ⬜ Todo | `purge_chessjs` | After U02-007 |
| U03-002 | Remove react-chessboard | package.json + src | Zero imports and dependency | CI grep `react-chessboard` | P0 | ⬜ Todo | `purge_rcb` | |
| U03-003 | Remove chessboardjsx + custom boards | package.json, `SimpleChessBoard`, `ChessBoardAlternative` | Files gone or re-export adapter only | Grep `chessboardjsx`, `SimpleChessBoard` | P0 | ⬜ Todo | `purge_custom` | |
| U03-004 | `npm run build` + `npm test` | Frontend | Both green | Build + full frontend test job in CI **or** documented local gate | P0 | ⬜ Todo | `purge_verify` | Spec §44 |
| U03-005 | Rewrite `StockfishGameLogic` onto chessops | Play helpers | No `Chess` from chess.js | Unit tests: legal move, checkmate fixture | P0 | ⬜ Todo | `play_chessops` | May merge with U02-007 if needed; prefer own branch |

---

### 04 — Variations (spec Phase 4)

| ID | Feature | Input | Verifiable output | Mandatory tests | Priority | Status | Branch slug | Comments |
| -- | ------- | ----- | ----------------- | --------------- | -------- | ------ | ----------- | -------- |
| U04-001 | Auto-branch on sideline | Main line + different move at same ply | New child; **main line not replaced** | Spec §14 fixture: `20.Re1` stays main; `20.Qc2` is variation | P0 | ⬜ Todo | `auto_branch` | |
| U04-002 | Promote variation | Selected sideline | `parent.children` reordered; old main kept | Promote then export order | P0 | ⬜ Todo | `promote_var` | Spec §15 |
| U04-003 | Delete variation | Selected node | Node + descendants gone; siblings remain | Delete child A; child B intact | P0 | ⬜ Todo | `delete_var` | Spec §16 |
| U04-004 | PGN RAV import/export | PGN with `( )` | Tree matches; export preserves structure (whitespace may differ) | Round-trip the spec §13 example | P0 | ⬜ Todo | `pgn_rav` | Spec §17 |
| U04-005 | Variation UI | Tree | Clickable notation with nested lines (not a flat list) | RTL: click sideline SAN → `currentMoveId` | P1 | ⬜ Todo | `variation_ui` | Spec §22 |
| U04-006 | Candidate preview (no commit) | Hover/select SAN | Temporary board preview; `currentMoveId` unchanged | Preview FEN ≠ committed FEN; on leave restore | P2 | ⬜ Todo | `position_preview` | Spec §26; can wait |

---

### 05 — Analysis UI (spec Phase 5)

**Gate:** Phase 3 Done. Backend or **fixture** `PositionAnalysis` JSON. Do not compute STOP from eval drop in the client.

| ID | Feature | Input | Verifiable output | Mandatory tests | Priority | Status | Branch slug | Comments |
| -- | ------- | ----- | ----------------- | --------------- | -------- | ------ | ----------- | -------- |
| U05-001 | `PositionAnalysis` view-model | JSON contract | Maps API/fixture → panel props; unknown fields ignored | Fixture with missing `criticalityScore` → no fake number | P0 | ⬜ Todo | `analysis_vm` | Spec §30 |
| U05-002 | STOP banner | `stopLevel` | Text `NORMAL`/`CONSIDER`/`CALCULATE`/`CRITICAL` always visible | Four fixtures; color not the only cue | P0 | ⬜ Todo | `stop_banner` | Spec §31 |
| U05-003 | Signals lists | `tacticalSignals` / `strategicSignals` | Two lists; empty state | Mixed fixture; LLM blob not rendered as a signal | P0 | ⬜ Todo | `signals_lists` | Spec §33 |
| U05-004 | Candidate list | `candidates[]` | SAN + optional eval; select → annotation arrow | Select `Bxh7+` sets arrow origin/dest; **FEN unchanged** | P0 | ⬜ Todo | `candidates_list` | Spec §12, §32 |
| U05-005 | Preview / Calculate / Play | Mode + candidate | Preview = arrow; Play = `makeMove` on **game** tree; Calculate = P7 | Three mode tests; Play does not run in read-only | P1 | ⬜ Todo | `candidate_actions` | Calculate can no-op until P7 |
| U05-006 | Decision-process panel | Structured fields | Situation/Threat/Worst piece/Plan/Candidates/Calculation | Renders only provided keys | P2 | ⬜ Todo | `decision_panel` | Spec §34; 07.4 may be absent |
| U05-007 | `errorProbability` | Optional API field | Shown only if present and typed | Absent → hidden; never `cp → %` | P0 | ⬜ Todo | `no_fake_probability` | Conflict resolution |

---

### 06 — Engine interaction (spec Phase 6)

**Gate:** Phase 3 Done. Prefer 07 MultiPV JSON fixtures. Live UCI in the browser is out of scope.

| ID | Feature | Input | Verifiable output | Mandatory tests | Priority | Status | Branch slug | Comments |
| -- | ------- | ----- | ----------------- | --------------- | -------- | ------ | ----------- | -------- |
| U06-001 | `EngineEvaluation` + eval bar | cp/mate | Bar saturates at large \|cp\|; mate shows `#n` | cp +600 and mate 3 fixtures | P0 | ⬜ Todo | `eval_bar` | Spec §19 |
| U06-002 | MultiPV panel | 3 lines | Rank, SAN, eval; not inserted into game tree | Fixture MultiPV=3; clicking does not change `currentMoveId` | P0 | ⬜ Todo | `multipv_panel` | Spec §21 |
| U06-003 | Engine PV display | PV SAN | Independent panel (spec §20) | Long PV truncated with expand | P1 | ⬜ Todo | `engine_lines` | |
| U06-004 | Engine arrows | PV1 or selected line | Annotations `semanticType: engine` | Arrow from PV1 first ply | P1 | ⬜ Todo | `engine_arrows` | |
| U06-005 | Dual-engine slot | SF + optional Lc0 | Lc0 row hidden or `unavailable` | Fixture SF-only; no invented Lc0 eval | P1 | ⬜ Todo | `lc0_slot` | Until backend exists |
| U06-006 | Apply engine move (explicit) | User confirms | Then `makeMove` / new variation | Without confirm, tree unchanged | P1 | ⬜ Todo | `apply_engine_move` | Spec §20 |

---

### 07 — Calculation training (spec Phase 7)

**Gate:** Phase 4 (need a second tree). Frozen display board.

| ID | Feature | Input | Verifiable output | Mandatory tests | Priority | Status | Branch slug | Comments |
| -- | ------- | ----- | ----------------- | --------------- | -------- | ------ | ----------- | -------- |
| U07-001 | `CalculationTree` isolated | User moves in calc mode | Game tree unchanged | After 3 calc plies, `game.currentMoveId` same | P0 | ⬜ Todo | `calc_tree` | Spec §25 |
| U07-002 | Frozen Chessground | Calc mode | Display FEN = calc root, not calc leaf | Assert adapter `setPosition` called with root only | P0 | ⬜ Todo | `frozen_board` | Spec §24 |
| U07-003 | Calc notation list | Calc tree | Shows entered line while board frozen | RTL list has `Bxh7+` etc. | P1 | ⬜ Todo | `calc_notation` | |
| U07-004 | Compare vs engine fixture | Calc line + engine PV | Diff highlight; no auto-merge into game | Mismatch fixture | P2 | ⬜ Todo | `calc_compare` | No live engine required |

---

## 3. Per-feature test format

| Field | Description |
| ----- | ----------- |
| `id` | `Uxx-yyy` |
| `fen` / `pgn` | Fixture |
| `expected_fen` | After nav or move |
| `expected_tree` | Mainline vs children ids |
| `ui_mode` | `analysis` / `readonly` / `calculation` / `play` |
| `backend_payload` | Optional 07/08 JSON; may be omitted |
| `must_not` | e.g. no chess.js import; no FEN change on candidate select |

Suggested files (when implementing, not now):

```text
src/frontend/src/chess/          # domain TS
src/frontend/src/chess/__tests__/
src/frontend/src/components/chess/__tests__/
```

---

## 4. Documentation / code layout (when implementing)

```text
docs/ai_chess_coach/
├── drafts/acc_ui_improvements_specs.md          # architecture brief
├── drafts/acc_ui_current_architecture.md        # U00-001 deliverable (not created yet)
├── roadmap/12-acc-ui-renewal-implementation-plan.md  # this file
src/frontend/
├── package.json                                 # later: chessops, chessground, vitest
└── src/chess/                                   # do not create until U01-001
```

Do not add Chessground/chessops until U01-001 / U02-001 on their branches.

---

## 5. First implementable increment

### Hard gates

- [ ] **Docs:** U00-001…U00-005 inventory written
- [ ] **Harness:** U00-006 `npm test` exists
- [ ] **Increment A (spec §51):** U01-001…U01-007 + U02-001…U02-005 + U02-007 + U03-001…U03-004  
  Load PGN, navigate full game, Chessground only, legacy libs gone
- [ ] **Increment B:** Phase 4 variations
- [ ] **Increment C:** Phase 5 only with fixtures or real 07 JSON — **no invented STOP**
- [ ] **Increment D:** Phase 6 SF/fixture MultiPV
- [ ] **Increment E:** Phase 7 calculation

### Out of scope for the whole epic unless a new ID is added

- FastAPI rewrite, RAG, ML in the browser
- Second frontend framework
- Chess variants, premoves, clocks
- Live Lc0
- Pixel-copy of Lichess
- Converting non-chess pages to TS
- Computing criticality / eval_loss in the client

---

## 6. Implementation phases (branch order)

```text
P0  U00-001 → … → U00-006
P1  U01-001 → U01-007 (U01-008 optional)
P2  U02-001 → U02-007 (P0 board), then U02-008/009
P3  U03-* purge  ★ gate
P4  U04-001 → U04-005
P5  U05-*
P6  U06-*
P7  U07-*
```

---

## 7. MVP acceptance (spec §49, narrowed)

- [ ] Chessground is the only Vite board renderer
- [ ] chessops is the only frontend rules engine
- [ ] `chess.js`, `react-chessboard`, `chessboardjsx`, `chessboard.js` absent
- [ ] No `SimpleChessBoard` custom piece renderer
- [ ] PGN mainline load + FEN load + legal moves + promotions + flip + last-move
- [ ] Navigation buttons and keyboard
- [ ] Build + frontend tests green
- [ ] Existing FastAPI game load still works (same payloads)
- [ ] Variations, STOP, engines, calculation are **later increments**, not MVP

---

## 8. Priority order

```text
P0
1. Audit docs + Vitest
2. chessops controller + linear tree
3. Chessground adapter + replace boards
4. Purge legacy
5. Auto-branch / promote / delete / PGN RAV
6. STOP + candidates from fixtures (no fake %)

P1
7. Dark workstation shell, annotations, read-only
8. Eval bar + MultiPV panel + engine arrows
9. Candidate Preview/Play
10. Play helpers on chessops

P2
11. Decision panel, preview-on-hover, calc compare, Lc0 slot
```

---

## 9. Decision on existing code

- **Replace** `useChessGame` chess.js state with `ChessGameController` (do not wrap Chess.js).
- **Replace** `SimpleChessBoard` / `ChessBoardAlternative` / `ChessinsightBoard` react-chessboard implementation with the adapter. Keep the **prop names** from `CONTRACT.md` where Jupyter needs them.
- **Keep** routing, auth, games list, import, reports — out of this epic except board consumers.
- **Keep** MUI; change theme tokens, not the library.
- **Treat** `PlayStockfishPage.jsx` as a consumer of the same chess domain, not a second rules engine.
- **Treat** Jupyter `mount.js` as a sibling renderer with a shared contract, not as a second product UI.

---

## 10. TODO — one checkbox = one branch

Copy a line to a ticket. Branch: `features/acc_ui_<phase>_<taskid>_<slug>`.

### P0 Audit (docs; U00-006 is harness code)

- [x] `features/acc_ui_p0_u00-001_inventory` — U00-001 Chess dependency inventory + grep report (also covers U00-002/003/004)
- [x] `features/acc_ui_p0_u00-002_state_audit` — skipped as separate branch; see U00-001 report
- [x] `features/acc_ui_p0_u00-003_api_audit` — skipped as separate branch; see U00-001 report
- [x] `features/acc_ui_p0_u00-004_board_contract` — skipped as separate branch; see U00-001 report
- [ ] `features/acc_ui_p0_u00-005_scope_freeze` — U00-005 Scope freeze note (if not already this file)
- [ ] `features/acc_ui_p0_u00-006_vitest_harness` — U00-006 Vitest + `npm test` smoke

### P1 Chess model

- [ ] `features/acc_ui_p1_u01-001_add_chessops` — U01-001 Add chessops
- [ ] `features/acc_ui_p1_u01-002_chess_position` — U01-002 ChessPosition + mandatory FEN tests
- [ ] `features/acc_ui_p1_u01-003_move_tree` — U01-003 Linear MoveTree
- [ ] `features/acc_ui_p1_u01-004_game_controller` — U01-004 ChessGameController
- [ ] `features/acc_ui_p1_u01-005_current_move_id` — U01-005 Single cursor
- [ ] `features/acc_ui_p1_u01-006_pgn_mainline` — U01-006 PGN mainline + comments
- [ ] `features/acc_ui_p1_u01-007_fen_session` — U01-007 Arbitrary FEN session
- [ ] `features/acc_ui_p1_u01-008_store_types` — U01-008 Store slice types

### P2 Chessground

- [ ] `features/acc_ui_p2_u02-001_board_adapter` — U02-001 ChessBoardAdapter
- [ ] `features/acc_ui_p2_u02-002_dests_lastmove` — U02-002 Dests + last move
- [ ] `features/acc_ui_p2_u02-003_drag_click` — U02-003 Drag and click-to-move
- [ ] `features/acc_ui_p2_u02-004_promotion` — U02-004 Promotion UI
- [ ] `features/acc_ui_p2_u02-005_navigation` — U02-005 Keyboard and buttons
- [ ] `features/acc_ui_p2_u02-006_annotations` — U02-006 Annotation model
- [ ] `features/acc_ui_p2_u02-007_replace_boards` — U02-007 Replace all product boards
- [ ] `features/acc_ui_p2_u02-008_shell_dark` — U02-008 Workstation shell + dark tokens
- [ ] `features/acc_ui_p2_u02-009_readonly_mode` — U02-009 Read-only mode

### P3 Purge (gate before P5–P7)

- [ ] `features/acc_ui_p3_u03-001_purge_chessjs` — U03-001 Remove chess.js
- [ ] `features/acc_ui_p3_u03-002_purge_rcb` — U03-002 Remove react-chessboard
- [ ] `features/acc_ui_p3_u03-003_purge_custom` — U03-003 Remove chessboardjsx + custom boards
- [ ] `features/acc_ui_p3_u03-004_purge_verify` — U03-004 build + test verify
- [ ] `features/acc_ui_p3_u03-005_play_chessops` — U03-005 Play helpers on chessops

### P4 Variations

- [ ] `features/acc_ui_p4_u04-001_auto_branch` — U04-001 Auto-create sideline
- [ ] `features/acc_ui_p4_u04-002_promote_var` — U04-002 Promote variation
- [ ] `features/acc_ui_p4_u04-003_delete_var` — U04-003 Delete variation
- [ ] `features/acc_ui_p4_u04-004_pgn_rav` — U04-004 PGN RAV import/export
- [ ] `features/acc_ui_p4_u04-005_variation_ui` — U04-005 Nested notation UI
- [ ] `features/acc_ui_p4_u04-006_position_preview` — U04-006 Hover preview (optional)

### P5 Analysis UI

- [ ] `features/acc_ui_p5_u05-001_analysis_vm` — U05-001 PositionAnalysis view-model
- [ ] `features/acc_ui_p5_u05-002_stop_banner` — U05-002 STOP text levels
- [ ] `features/acc_ui_p5_u05-003_signals_lists` — U05-003 Tactical vs strategic signals
- [ ] `features/acc_ui_p5_u05-004_candidates_list` — U05-004 Candidates + arrow, no FEN change
- [ ] `features/acc_ui_p5_u05-005_candidate_actions` — U05-005 Preview / Calculate / Play
- [ ] `features/acc_ui_p5_u05-006_decision_panel` — U05-006 Decision process panel
- [ ] `features/acc_ui_p5_u05-007_no_fake_probability` — U05-007 No cp-as-probability

### P6 Engine UI

- [ ] `features/acc_ui_p6_u06-001_eval_bar` — U06-001 Evaluation bar
- [ ] `features/acc_ui_p6_u06-002_multipv_panel` — U06-002 MultiPV panel
- [ ] `features/acc_ui_p6_u06-003_engine_lines` — U06-003 Engine PV panel
- [ ] `features/acc_ui_p6_u06-004_engine_arrows` — U06-004 Engine arrows
- [ ] `features/acc_ui_p6_u06-005_lc0_slot` — U06-005 Lc0 unavailable slot
- [ ] `features/acc_ui_p6_u06-006_apply_engine_move` — U06-006 Explicit apply engine move

### P7 Calculation

- [ ] `features/acc_ui_p7_u07-001_calc_tree` — U07-001 Isolated calculation tree
- [ ] `features/acc_ui_p7_u07-002_frozen_board` — U07-002 Frozen board
- [ ] `features/acc_ui_p7_u07-003_calc_notation` — U07-003 Calc move list
- [ ] `features/acc_ui_p7_u07-004_calc_compare` — U07-004 Compare vs engine fixture

**Start here:** `U00-001` (docs inventory). First code: `U00-006`, then `U01-001`.
