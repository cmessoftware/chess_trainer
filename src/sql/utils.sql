select * from experiments;

select count(game_id) from features limit 10;

SELECT 
    column_name, 
    data_type, 
    character_maximum_length, 
    is_nullable 
FROM 
    information_schema.columns
WHERE 
    table_schema = 'public'  
    AND table_name   = 'games';
 