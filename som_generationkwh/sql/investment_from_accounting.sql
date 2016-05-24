--- Returns tuples to create new investments
--- from info in accounting move lines.
--- TODO: Not used because it turns to be very slow when run from the erp
SELECT
    soci.id AS member_id,
    DIV(credit-debit,100) AS nshares,
    line.purchase_date AS purchase_date,
    line.id AS move_line_id,
    line.purchase_date
        + %(waitingDays)s * interval '1 day'
        AS first_effective_date,
    line.purchase_date
        + %(waitingDays)s * interval '1 day'
        + %(expirationYears)s * interval '1 year'
        AS last_effective_date
FROM (
    SELECT
        line.credit AS credit,
        line.debit AS debit,
        line.date_created AS purchase_date,
        line.id AS id,
        line.partner_id AS partner_id,
        account.code AS account_code
    FROM
        account_account AS account
    INNER JOIN
        account_move_line AS line
        ON line.account_id = account.id
    WHERE
        account.code ILIKE %(generationAccountPrefix)s AND
        COALESCE(line.date_created <=%(stop)s, TRUE) AND
        COALESCE(line.date_created >=%(start)s, TRUE) AND
        TRUE
    ) AS line
JOIN
    res_partner AS partner
    ON partner.id = line.partner_id
--    OR partner.ref = 'S' || LPAD(RIGHT(line.account_code,6),6,'0')

JOIN
    somenergia_soci AS soci
    ON soci.partner_id = partner.id
LEFT JOIN
    generationkwh_investment AS investment
    ON investment.move_line_id = line.id
WHERE
    investment.move_line_id IS NULL
ORDER BY
    move_line_id
