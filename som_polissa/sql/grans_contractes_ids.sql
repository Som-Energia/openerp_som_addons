SELECT DISTINCT(pol.id)
FROM giscedata_polissa pol
INNER JOIN giscedata_polissa_category_rel rel ON rel.polissa_id = pol.id
INNER JOIN giscedata_polissa_category cat ON cat.id = rel.category_id
WHERE cat.code = 'GC'
AND (pol.data_baixa is null or pol.data_baixa > pol.data_ultima_lectura)
AND pol.data_ultima_lectura < CURRENT_DATE - '1 MONTH'::INTERVAL -'7 DAY'::INTERVAL;
