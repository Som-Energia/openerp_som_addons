SELECT
    pol.id as contract_id,
    soci.id AS member_id,
    cups.conany_kwh as annual_use,
    CASE
        WHEN pol.pagador=partner.id THEN 1
        WHEN pol.titular=partner.id THEN 2
        END AS payerOwner
FROM somenergia_soci AS soci
LEFT JOIN
    res_partner AS partner ON
        soci.partner_id = partner.id
LEFT JOIN
    giscedata_polissa AS pol ON
        pol.pagador = partner.id OR
        pol.titular = partner.id OR
        FALSE
LEFT JOIN
    giscedata_cups_ps AS cups ON
        cups.id = pol.cups
WHERE
    soci.id in %(socis)s AND
    -- Next filters not supported by tests
    partner.active AND
    pol.state = 'activa' AND
    pol.active AND
    cups.active AND
    TRUE
ORDER BY
    partner.id,
    payerOwner ASC,
    annual_use DESC,
    pol.id,
    TRUE
