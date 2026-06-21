SELECT 
    a.attname AS column_name,
    format_type(a.atttypid, a.atttypmod) AS data_type,
    CASE 
        WHEN a.attnotnull THEN 'NO' 
        ELSE 'YES' 
    END AS is_nullable,
    pg_get_expr(d.adbin, d.adrelid) AS column_default,
    col_description(a.attrelid, a.attnum) AS column_description
FROM 
    pg_catalog.pg_attribute a
LEFT JOIN 
    pg_catalog.pg_attrdef d ON a.attrelid = d.adrelid AND a.attnum = d.adnum
JOIN 
    pg_catalog.pg_class c ON a.attrelid = c.oid
JOIN 
    pg_catalog.pg_namespace n ON c.relnamespace = n.oid
WHERE 
    c.relname = 'games'      -- Replace with your table name
    AND n.nspname = 'public'  -- Replace with your schema (e.g., 'public')
    AND a.attnum > 0 
    AND NOT a.attisdropped
ORDER BY 
    a.attnum;
