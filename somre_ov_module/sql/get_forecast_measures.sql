WITH filtered_data AS (
    SELECT
        gp."timestamp" AT TIME ZONE 'UTC' AS "timestamp",
        gp.generacio
    FROM
        giscere_previsio_publicada gp
    WHERE
        gp.publicada = TRUE
        AND gp.codi_previsio = %(forecast_code)s
        AND gp."timestamp" AT TIME ZONE 'UTC' BETWEEN %(first_timestamp_utc)s AND %(last_timestamp_utc)s
),
filled_data AS (
    SELECT
        generate_series AS "timestamp",
        NULL::numeric AS generacio
    FROM
        generate_series(
            %(first_timestamp_utc)s,
            %(last_timestamp_utc)s,
            INTERVAL '1 HOUR'
        ) generate_series
    LEFT JOIN
        filtered_data fd ON generate_series.generate_series = fd."timestamp"
    WHERE
        fd."timestamp" IS NULL
),
final_data AS (
    SELECT
        COALESCE(fd."timestamp", fd2."timestamp") AS "timestamp",
        COALESCE(fd.generacio, fd2.generacio) AS generacio
    FROM
        filtered_data fd
    FULL JOIN
        filled_data fd2 ON fd."timestamp" = fd2."timestamp"
)
SELECT
    COALESCE(ARRAY_AGG(generacio ORDER BY "timestamp" ASC), ARRAY[]::numeric[]) AS foreseen_kwh
FROM
    final_data;
