SELECT id
FROM giscedata_polissa
WHERE data_baixa IS NOT null
AND state = 'baixa'
AND lot_facturacio IS NOT null
AND data_ultima_lectura < CURRENT_DATE - '1 MONTH'::INTERVAL - '7 DAY'::INTERVAL;
