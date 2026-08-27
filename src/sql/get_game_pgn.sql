    -- Install get_game_pgn in the database where table public.games lives.
    -- In pgAdmin: Query Tool on that database, run THIS entire script (not get_move_features.sql).

    SELECT current_database() AS db, current_user AS usr, current_schemas(true) AS schemas;

    DO $$
    DECLARE
        r record;
    BEGIN
        FOR r IN
            SELECT n.nspname, p.proname, pg_get_function_identity_arguments(p.oid) AS args, p.prokind
            FROM pg_proc p
            JOIN pg_namespace n ON n.oid = p.pronamespace
            WHERE p.proname IN ('get_game_pgn', 'call_get_game_pgn')
        LOOP
            IF r.prokind = 'p' THEN
                EXECUTE format('DROP PROCEDURE %I.%I(%s)', r.nspname, r.proname, r.args);
            ELSE
                EXECUTE format('DROP FUNCTION %I.%I(%s)', r.nspname, r.proname, r.args);
            END IF;
        END LOOP;
    END;
    $$;

    CREATE FUNCTION public.get_game_pgn(p_game_id text)
    RETURNS TABLE (
        found boolean,
        game_id text,
        pgn text,
        error_message text
    )
    LANGUAGE plpgsql
    STABLE
    AS $$
    DECLARE
        v_id text;
        v_pgn text;
    BEGIN
        IF p_game_id IS NULL OR btrim(p_game_id) = '' THEN
            RETURN QUERY SELECT false, p_game_id, NULL::text, 'game_id is required'::text;
            RETURN;
        END IF;

        SELECT g.game_id::text, g.pgn::text
        INTO v_id, v_pgn
        FROM public.games AS g
        WHERE g.game_id = btrim(p_game_id);

        IF NOT FOUND THEN
            RETURN QUERY SELECT
                false,
                btrim(p_game_id),
                NULL::text,
                format('Game not found: %s', btrim(p_game_id));
            RETURN;
        END IF;

        IF v_pgn IS NULL OR btrim(v_pgn) = '' THEN
            RETURN QUERY SELECT
                false,
                v_id,
                v_pgn,
                format('Game %s exists but PGN is empty', v_id);
            RETURN;
        END IF;

        RETURN QUERY SELECT true, v_id, v_pgn, NULL::text;
    END;
    $$;

    GRANT EXECUTE ON FUNCTION public.get_game_pgn(text) TO PUBLIC;

    SELECT n.nspname AS schema, p.proname, pg_get_function_identity_arguments(p.oid) AS args
    FROM pg_proc p
    JOIN pg_namespace n ON n.oid = p.pronamespace
    WHERE p.proname = 'get_game_pgn';
