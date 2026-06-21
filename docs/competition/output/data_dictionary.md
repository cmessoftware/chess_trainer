# Data Dictionary — ChessTrainer Kaggle Competition

| Column | Type | Description | Values |
|--------|------|-------------|--------|
| id | int | Unique row identifier (one chess move). | 1 … N |
| player_elo | int | ELO of the player who made the move. | 600–3000 |
| elo_band | category | Player strength band derived from player_elo. | <1200, 1200-1399, …, 2400+ |
| time_control_bucket | category | Normalized time control. | bullet, blitz, rapid, classical |
| phase | category | Game phase for the position. | opening, middlegame, endgame |
| opening | string | Opening name from the game metadata. | free text |
| move_number | int | Full-move counter. | ≥ 1 |
| fen | string | FEN of the position before the move. | standard FEN |
| move_san | string | Move played in SAN notation. | e.g. Nf3, exd5 |
| material_total | float | Total material on the board. | ≥ 0 |
| material_balance | float | Material balance (positive = advantage for side to move). | integer-ish |
| num_pieces | int | Piece count. | ≥ 0 |
| has_castling_rights | int | 1 if castling rights remain. | 0 or 1 |
| is_pawn_endgame | int | 1 if pawn endgame. | 0 or 1 |
| branching_factor | int | Legal move count (complexity proxy). | ≥ 0 |
| self_mobility | int | Mobility of side to move. | ≥ 0 |
| opponent_mobility | int | Mobility of opponent. | ≥ 0 |
| king_safety | int | King safety (self − opponent mobility). | integer |
| center_control | int | Center control proxy (branching-based). | ≥ 0 |
| is_low_mobility | int | 1 if side to move has low mobility. | 0 or 1 |
| is_center_controlled | int | 1 if center squares are controlled. | 0 or 1 |
| tactical_tag | category | Primary tactical motif for the move. | normal, check, fork, pin, … |
| tag_check | int | 1 if the move gives check. | 0 or 1 |
| tag_fork | int | 1 if the move is a knight fork on major pieces. | 0 or 1 |
| tag_pin | int | 1 if the move creates a pin. | 0 or 1 |
| tag_discovered_attack | int | 1 if the move is a discovered attack. | 0 or 1 |
| tag_mate | int | 1 if the position is checkmate. | 0 or 1 |
| error_label | category | Move quality label (train only). | good, inaccuracy, mistake, blunder |
