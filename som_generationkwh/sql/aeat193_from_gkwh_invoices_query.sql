SELECT gkwh_owner.owner_id AS partner_id, par.vat as vat, SUM(gkwh_owner.saving_gkw_amount) as amount
FROM generationkwh_invoice_line_owner gkwh_owner
INNER JOIN giscedata_facturacio_factura f ON f.id=gkwh_owner.factura_id
INNER JOIN account_invoice i ON i.id=f.invoice_id
INNER JOIN res_partner par ON par.id = gkwh_owner.owner_id
WHERE i.date_invoice BETWEEN %(start)s AND %(end)s
GROUP BY gkwh_owner.owner_id, par.vat