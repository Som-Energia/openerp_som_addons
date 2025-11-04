SELECT
    sub.name AS soci,
    max(pol.name) AS assigned_polissa
FROM (
   SELECT
        soci.id AS soci_id,
        soci.name AS name,
        max(CASE
            WHEN pol.pagador=soci.id THEN 2
            WHEN pol.titular=soci.id THEN 1
            END) AS PRIORIDAD,
        COALESCE(
            MAX(
                CASE WHEN POL.PAGADOR=soci.id THEN cups.conany_kwh
                ELSE NULL
                END), 
            MAX(CASE
                WHEN POL.PAGADOR!=soci.id AND POL.TITULAR=soci.id THEN cups.conany_kwh
                ELSE NULL END)
            ) AS consumprioritario,
        FALSE
    FROM res_partner AS soci
    LEFT JOIN
        giscedata_polissa AS pol ON 
            pol.titular = soci.id OR
            pol.pagador = soci.id
    LEFT JOIN
        giscedata_cups_ps AS cups ON
            cups.id = pol.cups
    WHERE
        soci.active AND 
        pol.state = 'activa' AND 
        cups.active AND
        pol.active AND
        TRUE
    GROUP BY 
        SOCI.ID
    ORDER BY
        soci.id ASC
) AS sub
INNER JOIN giscedata_polissa pol ON CASE
    WHEN PRIORIDAD = 2 THEN POL.PAGADOR=SOCI_ID
    WHEN PRIORIDAD=1 THEN POL.TITULAR=SOCI_ID
    ELSE FALSE
    END
INNER JOIN giscedata_cups_ps cups ON
    cups.conany_kwh=consumprioritario AND
    cups.id = pol.cups
INNER JOIN (
    SELECT 
        sum(LINE.AMOUNT) AS inversion,
        max(partner_id) AS already_invested
    FROM payment_line AS line
    LEFT JOIN
        payment_order AS remesa ON remesa.id = line.order_id 
    WHERE
        remesa.mode = 19
    GROUP BY partner_id
    ) AS investments on already_invested=soci_id
WHERE
    POL.STATE = 'activa' AND
    cups.active AND
    pol.active
GROUP BY sub.name
