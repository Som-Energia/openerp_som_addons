-- Given a contract id returns a table with
-- members whom take the generationkwh rights from
-- and newest date you can get rights from them.
-- Such date is given by the existance of any contract
-- having more priority than ours that has not invoiced
-- beyond that date yet.
SELECT
    ass.member_id AS member_id,
    COALESCE(
        MIN(contracte.last_usable_date),
        DATE(NOW()) /* no peers, so now */
    ) AS last_usable_date,
    FALSE
FROM generationkwh_assignment AS ass
LEFT JOIN generationkwh_assignment AS peer
    ON ass.member_id = peer.member_id
    AND peer.contract_id != ass.contract_id
    AND peer.priority < ass.priority
    AND peer.end_date IS NULL
LEFT JOIN (
    SELECT
        id,
        COALESCE(
            data_ultima_lectura,
            data_alta
        ) AS last_usable_date
    FROM giscedata_polissa AS polissa
    WHERE
        polissa.active AND -- UNTESTED
        polissa.state != 'esborrany' AND -- UNTESTED
        TRUE
    ) AS contracte
    ON contracte.id = peer.contract_id
WHERE
    ass.contract_id = %(contract_id)s AND
    ass.end_date IS NULL AND
    TRUE
GROUP BY
    ass.id,
    ass.member_id,
    FALSE
ORDER BY
    ass.id,
    FALSE
