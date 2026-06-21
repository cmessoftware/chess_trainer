select white_elo, count(white_elo) from public.games
where white_player = 'titimessi333578' or black_palyer =
source = 'novice' and (white_elo::integer < 1200 and black_elo::integer < 1200)
group by white_elo
order by cout

select count(*) from public.games g
join public.features f on g.game_id = f.game_id
where  g.white_player='cmess1315' or g.black_player='cmess1315';

select count(g.game_id) from games g
join public.features f on g.game_id = f.game_id
where source = 'stockfish';

BEGIN
	WITH MinEloPerSource AS (
	    SELECT 
	        source, 
	        MIN(NULLIF(white_elo, '')::numeric) AS min_white_elo,
	        MIN(NULLIF(black_elo, '')::numeric) AS min_black_elo
	    FROM games
	    GROUP BY source 
	),
	WITH MaxEloPerSource AS (
	    SELECT 
	        source, 
	        MAX(NULLIF(white_elo, '')::numeric) AS man_white_elo,
	        MAX(NULLIF(black_elo, '')::numeric) AS man_black_elo
	    FROM games
	    GROUP BY source 
	)
	SELECT 
	    source,
	    ROUND(AVG(min_white_elo)::numeric, 0) AS AvgMinWhiteElo -- Rounded to 0 decimals
	FROM MinEloPerSource    
	GROUP BY source
END;

--titimessi333578

--white_player like 'Th3Hound%' or black_player = 'Th3Hound%';
--limit 1000;
