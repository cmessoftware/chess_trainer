-- Insertar partida dummy
INSERT INTO
    games (
        game_id,
        site,
        event,
        date,
        white_player,
        black_player,
        result
    )
VALUES (
        'abcd1234testgame',
        'Chess.com',
        'Dummy Test',
        '2025.07.01',
        'TestWhite',
        'TestBlack',
        '1-0'
    );

-- Insertar features para ese game
INSERT INTO
    features (
        game_id,
        move_number,
        player_color,
        fen,
        move_san,
        move_uci,
        error_label,
        material_balance,
        material_total,
        num_pieces,
        branching_factor,
        self_mobility,
        opponent_mobility,
        phase,
        has_castling_rights,
        move_number_global,
        is_repetition,
        is_low_mobility,
        is_center_controlled,
        is_pawn_endgame,
        tags,
        score_diff,
        site,
        event,
        date,
        white_player,
        black_player,
        result,
        num_moves,
        is_stockfish_test
    )
VALUES
    -- Movimiento 12 blanco
    (
        'abcd1234testgame',
        12,
        1,
        'dummy_fen_12',
        'Nf3',
        'g1f3',
        NULL,
        0,
        32,
        16,
        20,
        10,
        10,
        'mid',
        1,
        12,
        0,
        0,
        1,
        0,
        NULL,
        0,
        'Chess.com',
        'Dummy Test',
        '2025.07.01',
        'TestWhite',
        'TestBlack',
        '1-0',
        20,
        false
    )

-- Movimiento 15 negro
(
    'abcd1234testgame',
    15,
    0,
    'dummy_fen_15',
    'e5',
    'e7e5',
    NULL,
    0,
    30,
    15,
    22,
    9,
    11,
    'mid',
    1,
    15,
    0,
    0,
    1,
    0,
    NULL,
    0,
    'Chess.com',
    'Dummy Test',
    '2025.07.01',
    'TestWhite',
    'TestBlack',
    '1-0',
    20,
    false
);

select
    game_id,
    move_number,
    player_color,
    tags
from features
where
    game_id = 'abcd1234testgame';