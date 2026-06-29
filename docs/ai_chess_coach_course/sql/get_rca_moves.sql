select g.pgn, g.game_id, fen, move_san, error_label, tags 
from features f
join games g on g.game_id = f.game_id
where 
	(g.white_player = 'cmess1315' and f.result='0-1')
	or
	(g.black_player = 'cmess1315' and f.result='1-0')
	and
	error_label in ('mistake','blunder')
	and tags is not null;
	
select game_id,pgn from games where game_id='7ec8a74d2ae587929edbe33596d8efa22c48e263d121b4e2a5af1a44869773c5'
	
	