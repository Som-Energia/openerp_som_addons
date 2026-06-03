# -*- coding: utf-8 -*-
from __future__ import print_function  # Garanteix que print() funcioni igual a Python 2 i 3
import psycopg2
from psycopg2.extras import RealDictCursor
import configdb


# 1. Marge multiplicador: 1.10 significa "Llindar + 10% de marge"
MARGE_MULTIPLICADOR = 1.10

# 2. Query SQL optimitzada amb filtres interns
SQL_QUERY = """
WITH configuracio_global AS (
    SELECT
        (
            SELECT setting::float
            FROM pg_settings
            WHERE name = 'autovacuum_vacuum_scale_factor'
        ) AS global_scale,
        (
            SELECT setting::float
            FROM pg_settings
            WHERE name = 'autovacuum_vacuum_threshold'
        ) AS global_threshold
),
llindars_calculats AS (
    SELECT
        ns.nspname AS esquema,
        cl.relname AS taula,
        cl.reltuples AS files_totals,
        st.n_dead_tup AS files_mortes,
        -- CORRECCIÓ: Afegim ([1]) per extreure el primer element de l'array abans del ::float
        COALESCE(
            (SELECT (regexp_matches(val, 'autovacuum_vacuum_scale_factor=([0-9.]+)'))[1]::float
             FROM unnest(cl.reloptions) WITH ORDINALITY AS u(val, ord)),
            g.global_scale
        ) AS scale_factor,
        -- CORRECCIÓ: Afegim ([1]) per extreure el primer element de l'array abans del ::float
        COALESCE(
            (SELECT (regexp_matches(val, 'autovacuum_vacuum_threshold=([0-9.]+)'))[1]::float
             FROM unnest(cl.reloptions) WITH ORDINALITY AS u(val, ord)),
            g.global_threshold
        ) AS base_threshold
    FROM pg_class cl
    JOIN pg_namespace ns ON ns.oid = cl.relnamespace
    JOIN pg_stat_user_tables st ON st.relid = cl.oid
    CROSS JOIN configuracio_global g
    WHERE cl.relkind = 'r'
),
taules_amb_llindar AS (
    SELECT
        esquema,
        taula,
        files_totals,
        files_mortes,
        ROUND((base_threshold + (scale_factor * files_totals))::numeric, 0) AS llindar_autovacuum
    FROM llindars_calculats
)
SELECT
    esquema,
    taula,
    files_totals,
    files_mortes,
    llindar_autovacuum,
    ROUND((files_mortes::float / NULLIF(llindar_autovacuum, 0) * 100)::numeric,
        1) AS percentatge_actual
FROM taules_amb_llindar
WHERE files_mortes > (llindar_autovacuum * %s)
ORDER BY percentatge_actual DESC;
"""


def cerca_taules_excedides():
    conn = None
    cursor = None
    try:
        conn = psycopg2.connect(**configdb.psycopg)
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        cursor.execute(SQL_QUERY, (MARGE_MULTIPLICADOR,))
        taules_alerta = cursor.fetchall()

        if not taules_alerta:
            print("✅ Cap taula ha superat el llindar modificat amb el marge definit.")
            exit(0)

        print("⚠️ S'han trobat {0} taules que han superat el límit:\n".format(len(taules_alerta)))

        # Plantilla de format compatible amb Python 2 i 3 per alinear columnes
        row_format = "{:<15} | {:<30} | {:<10} | {:<10} | {:<10}"

        print(row_format.format('ESQUEMA', 'TAULA', 'MORTES', 'LLINDAR', '% ACTUAL'))
        print("-" * 85)

        for t in taules_alerta:
            percentatge_str = "{0}%".format(t['percentatge_actual'])
            print(row_format.format(
                t['esquema'],
                t['taula'],
                t['files_mortes'],
                t['llindar_autovacuum'],
                percentatge_str
            ))

    except Exception as error:
        print("❌ Error d'execució: {0}".format(error))
        exit(-1)
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
    exit(1)


if __name__ == "__main__":
    cerca_taules_excedides()
