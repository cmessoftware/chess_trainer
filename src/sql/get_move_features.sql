-- Features for one move of a game.
-- Apply in pgAdmin Query Tool connected to the SAME database as table games.

SET search_path TO public;

DROP PROCEDURE IF EXISTS public.call_get_move_features(text, integer, integer, boolean, text, text, text, text, text, double precision);
DROP PROCEDURE IF EXISTS public.get_move_features(text, integer, integer, boolean, text, text, text, text, text, double precision);
DROP FUNCTION IF EXISTS public.get_move_features(text, integer, integer);
DROP FUNCTION IF EXISTS public.get_move_features(text, integer);


CREATE OR REPLACE FUNCTION public.get_move_features(
    p_game_id text,
    p_move_number integer,
    p_player_color integer
)
    RETURNS TABLE (
        found boolean,
        error_message text,
        game_id text,
        move_number integer,
        player_color integer,
        fen text,
        move_san text,
        move_uci text,
        error_label text,
        material_balance double precision,
        material_total double precision,
        num_pieces integer,
        branching_factor integer,
        self_mobility integer,
        opponent_mobility integer,
        phase text,
        has_castling_rights integer,
        move_number_global integer,
        is_repetition integer,
        is_low_mobility integer,
        is_center_controlled integer,
        is_pawn_endgame integer,
        tags jsonb,
        score_diff double precision,
        created_at timestamp,
        site text,
        event text,
        date text,
        white_player text,
        black_player text,
        result text,
        num_moves integer,
        is_stockfish_test boolean
    )
    LANGUAGE plpgsql
    AS $$
    DECLARE
        v_game_id text;
        v_rows integer := 0;
    BEGIN
        IF p_game_id IS NULL OR btrim(p_game_id) = '' THEN
            found := false;
            error_message := 'game_id is required';
            game_id := p_game_id;
            move_number := p_move_number;
            player_color := p_player_color;
            RETURN NEXT;
            RETURN;
        END IF;

        IF p_move_number IS NULL OR p_move_number < 1 THEN
            found := false;
            error_message := 'move_number must be >= 1';
            game_id := btrim(p_game_id);
            move_number := p_move_number;
            player_color := p_player_color;
            RETURN NEXT;
            RETURN;
        END IF;

        IF p_player_color IS NOT NULL AND p_player_color NOT IN (0, 1) THEN
            found := false;
            error_message := 'player_color must be 0 (Black), 1 (White), or NULL';
            game_id := btrim(p_game_id);
            move_number := p_move_number;
            player_color := p_player_color;
            RETURN NEXT;
            RETURN;
        END IF;

        SELECT g.game_id::text
        INTO v_game_id
        FROM public.games AS g
        WHERE g.game_id = btrim(p_game_id);

        IF NOT FOUND THEN
            found := false;
            error_message := format('Game not found: %s', btrim(p_game_id));
            game_id := btrim(p_game_id);
            move_number := p_move_number;
            player_color := p_player_color;
            RETURN NEXT;
            RETURN;
        END IF;

        RETURN QUERY
        SELECT
            true,
            NULL::text,
            f.game_id::text,
            f.move_number,
            f.player_color,
            f.fen::text,
            f.move_san::text,
            f.move_uci::text,
            f.error_label::text,
            f.material_balance,
            f.material_total,
            f.num_pieces,
            f.branching_factor,
            f.self_mobility,
            f.opponent_mobility,
            f.phase::text,
            f.has_castling_rights,
            f.move_number_global,
            f.is_repetition,
            f.is_low_mobility,
            f.is_center_controlled,
            f.is_pawn_endgame,
            f.tags::jsonb,
            f.score_diff,
            f.created_at::timestamp,
            f.site::text,
            f.event::text,
            f.date::text,
            f.white_player::text,
            f.black_player::text,
            f.result::text,
            f.num_moves,
            f.is_stockfish_test
        FROM public.features AS f
        WHERE f.game_id = v_game_id
        AND f.move_number = p_move_number
        AND (p_player_color IS NULL OR f.player_color = p_player_color)
        ORDER BY f.player_color DESC;

        GET DIAGNOSTICS v_rows = ROW_COUNT;

        IF v_rows = 0 THEN
            found := false;
            IF p_player_color IS NULL THEN
                error_message := format(
                    'No features for game %s at move_number %s',
                    v_game_id,
                    p_move_number
                );
            ELSE
                error_message := format(
                    'No features for game %s at move_number %s player_color %s',
                    v_game_id,
                    p_move_number,
                    p_player_color
                );
            END IF;
            game_id := v_game_id;
            move_number := p_move_number;
            player_color := p_player_color;
            RETURN NEXT;
        END IF;
    END;
    $$;

    COMMENT ON FUNCTION public.get_move_features(text, integer, integer) IS
        'Returns feature rows for a game move. player_color 1=White, 0=Black, NULL=both.';


CREATE OR REPLACE PROCEDURE public.call_get_move_features(
    IN p_game_id text,
    IN p_move_number integer,
    IN p_player_color integer,
    INOUT o_found boolean DEFAULT NULL,
    INOUT o_error_message text DEFAULT NULL,
    INOUT o_fen text DEFAULT NULL,
    INOUT o_move_san text DEFAULT NULL,
    INOUT o_move_uci text DEFAULT NULL,
    INOUT o_error_label text DEFAULT NULL,
    INOUT o_score_diff double precision DEFAULT NULL
)
LANGUAGE plpgsql
AS $$
BEGIN
    SELECT
        r.found,
        r.error_message,
        r.fen,
        r.move_san,
        r.move_uci,
        r.error_label,
        r.score_diff
    INTO
        o_found,
        o_error_message,
        o_fen,
        o_move_san,
        o_move_uci,
        o_error_label,
        o_score_diff
    FROM public.get_move_features(p_game_id, p_move_number, p_player_color) AS r
    LIMIT 1;
END;
$$;

COMMENT ON PROCEDURE public.call_get_move_features(text, integer, integer, boolean, text, text, text, text, text, double precision) IS
    'Single-row CALL wrapper. Pass player_color 0 or 1. Prefer SELECT * FROM public.get_move_features(...).';
