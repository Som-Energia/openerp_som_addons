/*
SQL query breakdown:

    1. Common Table Expressions (CTEs):
        * `filtered_data`: Filters data from `giscere_mhcil` based on:
            (cil, first_timestamp_utc, and last_timestamp_utc).
        * `filled_data`: Generates a series of timestamps between `first_timestamp_utc`
            and `last_timestamp_utc`, and fills in NULL values for `ae`, `maturity`, and
            `type_measure` where there are gaps in data.
        * `joined_data`: Joins the filtered and filled data, ensuring no gaps exist.
        * `ranked_data`: Adds a puntuation field to prioritize data for a same
            timestamp depending ong `type_measure` and `maturity`

    2. Main Query:
        * Selects aggregated data as a JSON object.
        * Aggregates data by `timestamp`.
        * Includes the following information in the JSON object:
            * `contract_name`: Contract name parameter.
            * `first_timestamp_utc`: Start timestamp parameter.
            * `last_timestamp_utc`: End timestamp parameter.
            * `estimated`: Array indicating whether the measurement is estimated (E)
                or measured (M), ordered by timestamp.
            * `measure_kwh`: Array of actual measurements, ordered by timestamp.
            * `maturity`: Array of maturity levels, ordered by timestamp.

    3. Final Filtering:
        * Filters the results to only include records where `maturity_rank` is equal to 1,
            meaning it selects the records with the highest maturity rank for each timestamp.
*/
WITH filtered_data AS (
    SELECT
        "timestamp" AT TIME ZONE 'UTC' AS "timestamp",
        ae,
        maturity,
        type_measure,
        version
    FROM
        giscere_mhcil
    WHERE
        cil = %(cil)s
        AND "timestamp" AT TIME ZONE 'UTC' BETWEEN %(first_timestamp_utc)s AND %(last_timestamp_utc)s
),
filled_data AS (
    SELECT
        generate_series AS "timestamp",
        NULL AS ae,
        NULL AS maturity,
        NULL AS type_measure,
        NULL AS version
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
joined_data AS (
    SELECT
        COALESCE(fd."timestamp", fd2."timestamp") AS "timestamp",
        COALESCE(fd.ae, NULL) AS ae,
        COALESCE(fd.maturity, fd2.maturity) AS maturity,
        COALESCE(fd.type_measure, fd2.type_measure) AS type_measure,
        COALESCE(fd.version, NULL) AS version
    FROM
        filtered_data fd
    FULL JOIN
        filled_data fd2 ON fd."timestamp" = fd2."timestamp"
),
ranked_data AS (
    SELECT
        *,
        CASE
            WHEN maturity = 'HC' THEN 1
            WHEN maturity = 'HP' THEN 2
            WHEN maturity = 'H3' THEN 3
            WHEN maturity = 'H2' THEN 4
            ELSE 5
        END AS ranking
    FROM
        joined_data
),
collapsed_data AS (
    SELECT DISTINCT ON("timestamp")
        *
    FROM
        ranked_data
    ORDER BY "timestamp" ASC, ranking ASC, version DESC
)
SELECT
    JSON_BUILD_OBJECT(
        'contract_name', %(contract_name)s,
        'first_timestamp_utc', %(first_timestamp_utc)s,
        'last_timestamp_utc', %(last_timestamp_utc)s,
        'estimated', COALESCE(ARRAY_AGG(CASE
            WHEN type_measure IN ('E', 'M') THEN true
            WHEN type_measure IN ('R', 'L') THEN false
            ELSE NULL
        END ORDER BY "timestamp" ASC), ARRAY[]::boolean[]),
        'measure_kwh', COALESCE(ARRAY_AGG(ae ORDER BY "timestamp" ASC), ARRAY[]::numeric[]),
        'maturity', COALESCE(ARRAY_AGG(maturity ORDER BY "timestamp" ASC), ARRAY[]::text[])
    ) AS data
FROM
    collapsed_data
