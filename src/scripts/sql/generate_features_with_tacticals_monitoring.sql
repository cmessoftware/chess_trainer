	-- 1) Backlog temporal (nulos recientes, esperables durante ejecución)
		select count(*) as null_recent
		from features f
		join games g on g.game_id = f.game_id
		where g.source in ('novice','personal')
		  and f.error_label is null
		  and f.created_at >= now() - interval '10 minutes';
-- 2) Nulos persistentes (más útiles para calidad real)
-- 2) Nulos persistentes (más útiles para calidad real)
	select count(*) as null_persistentes
	from features f
	join games g on g.game_id = f.game_id
	where g.source in ('novice','personal')
	  and f.error_label is null
	  and f.created_at < now() - interval '10 minutes';

-- 3) Cobertura por fuente en juegos ya procesados
	with base as (
	  select g.source,
	         count(*) as total_rows,
	         sum(case when f.error_label is null then 1 else 0 end) as null_rows
	  from features f
	  join games g on g.game_id = f.game_id
	  join processed_features pf on pf.game_id = g.game_id
	  where g.source in ('novice','personal')
	  group by g.source
	)
	select source,
	       total_rows,
	       null_rows,
	       round(100.0 * (total_rows - null_rows) / nullif(total_rows,0), 2) as pct_con_label
	from base
	order by source;