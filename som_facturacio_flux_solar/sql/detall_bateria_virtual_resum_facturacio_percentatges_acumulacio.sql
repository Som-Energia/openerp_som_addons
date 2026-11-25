SELECT
    info_bat.id AS id,
    info_bat.fact_id AS factura_id,
    info_bat.rectificative_type,
    info_bat.num_rect,
    info_bat.date_invoice,
    info_bat.data_inici,
    info_bat.data_final,
    info_bat.bateria_id,
    info_bat.bateria_polissa_id,
    sum(info_bat.sols_generats) AS sols_generats,
    sum(info_bat.sols_aplicats) AS sols_aplicats,
    sum(info_bat.sols_totals) AS sols_totals
FROM (
    SELECT
        info_batf.fact_id::text || '_0' AS id,
        info_batf.fact_id AS fact_id,
        info_batf.rectificative_type,
        info_batf.num_rect,
        info_batf.date_invoice,
        info_batf.data_inici,
        info_batf.data_final,
        info_batf.bateria_id,
        info_batf.bateria_polissa_id,
        SUM(CASE
                WHEN pp.default_code = 'SEA' THEN CASE
                        WHEN ai.type = 'out_refund' THEN ROUND((ail.price_subtotal * -1 * info_batf.percentatge * 0.01), 2)
                        ELSE ROUND((ail.price_subtotal * info_batf.percentatge * 0.01), 2)
                        END
                ELSE 0
                END) AS "sols_generats",
        SUM(CASE
                WHEN pp.default_code = 'PBV' THEN CASE
                        WHEN ai.type = 'out_refund' THEN ROUND((ail.price_subtotal * -1), 2)
                        ELSE ROUND((ail.price_subtotal), 2)
                        END
                ELSE 0
                END) AS "sols_aplicats",
        SUM(CASE
                WHEN pp.default_code = 'SEA' THEN CASE
                        WHEN ai.type = 'out_refund' THEN ROUND((ail.price_subtotal * -1 * info_batf.percentatge * 0.01), 2)
                        ELSE ROUND((ail.price_subtotal * info_batf.percentatge * 0.01), 2)
                        END
                ELSE 0 END
        ) + SUM(CASE
                WHEN pp.default_code = 'PBV' THEN CASE
                        WHEN ai.type = 'out_refund' THEN ROUND((ail.price_subtotal * -1), 2)
                        ELSE ROUND((ail.price_subtotal), 2)
                        END
                ELSE 0
                END
        ) AS "sols_totals"
    FROM
        account_invoice_line ail
    INNER JOIN (
    SELECT
        fact.id AS fact_id,
        Null as desc_id,
        ac.id AS invoice_id,
        ac.rectificative_type,
        coalesce(acr.number,'') AS num_rect,
        ac.date_invoice,
        fact.data_inici,
        fact.data_final,
        bat.bateria_id AS bateria_id,
        bat.id AS bateria_polissa_id,
        btpa.percentatge as percentatge,
        0 as import
    FROM
            giscedata_bateria_virtual_polissa bat
    INNER JOIN
            giscedata_polissa pol ON bat.polissa_id = pol.id
    INNER JOIN
            giscedata_facturacio_factura fact ON fact.polissa_id=pol.id
    INNER JOIN
            account_invoice ac ON (ac.id = fact.invoice_id AND ac.type IN ('out_invoice', 'out_refund') AND ac.state IN ('open', 'paid'))
    LEFT JOIN
            account_invoice acr ON (acr.id = ac.rectifying_id)
    LEFT JOIN
            giscedata_bateria_virtual_origen bto ON bto.bateria_id = bat.bateria_id
    LEFT JOIN
            giscedata_bateria_virtual_percentatges_acumulacio btpa ON btpa.origen_id = bto.id
    WHERE
            ac.type IN ('out_invoice', 'out_refund')
            AND ac.date_invoice >= (
                SELECT MIN(dia)
                FROM giscedata_bateria_virtual_polissa_descompte
            )
    ) AS info_batf ON info_batf.invoice_id = ail.invoice_id

    INNER JOIN
            product_product pp ON ail.product_id = pp.id
    INNER JOIN
            account_invoice ai ON ail.invoice_id = ai.id
    WHERE
            ai.type IN ('out_invoice', 'out_refund')
            AND pp.default_code IN ('SEA', 'PBV')
            AND info_batf.date_invoice >= (
                SELECT MIN(dia)
                FROM giscedata_bateria_virtual_polissa_descompte
            )
            AND info_batf.data_inici >= (
                SELECT MIN(data_inici_descomptes)
                FROM giscedata_bateria_virtual_origen orig_bat
                WHERE orig_bat.bateria_id = info_batf.bateria_id
            )
    GROUP BY
            info_batf.fact_id, info_batf.desc_id,
            info_batf.rectificative_type, info_batf.num_rect,
            info_batf.date_invoice, info_batf.data_inici, info_batf.data_final, info_batf.bateria_id, info_batf.bateria_polissa_id

    UNION

    SELECT
            '0_' || btod.id::text AS id,
            Null as fact_id,
            NULL rectificative_type,
            NULL num_rect,
            NULL date_invoice,
            NULL data_inici,
            NULL data_final,
            bat.bateria_id,
            bat.id,
            btod.import as importf,
            0 as percentatgef,
            btod.import as importf2
    FROM
            giscedata_bateria_virtual_polissa bat
    INNER JOIN
            giscedata_bateria_virtual_polissa_descompte btod ON btod.bateria_id = bat.bateria_id
    WHERE
            origen is null

) as info_bat

GROUP BY
    info_bat.id,
    info_bat.fact_id ,
    info_bat.rectificative_type,
    info_bat.num_rect,
    info_bat.date_invoice,
    info_bat.data_inici,
    info_bat.data_final,
    info_bat.bateria_id,
    info_bat.bateria_polissa_id