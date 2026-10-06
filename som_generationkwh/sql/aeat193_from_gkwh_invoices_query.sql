SELECT owner_id AS partner_id, owner_vat AS vat, SUM(savings) AS amount
FROM (SELECT gkwh_owner.factura_line_id AS factura_line_id,
             max(gkwh_owner.saving_gkw_amount) AS savings,
             max(gkwh_owner.id) AS gkwh_id,
             max(gkwh_owner.owner_id) AS owner_id,
             max(par.vat) AS owner_vat
      FROM generationkwh_invoice_line_owner gkwh_owner
      INNER JOIN giscedata_facturacio_factura f ON f.id=gkwh_owner.factura_id
      INNER JOIN account_invoice i ON i.id=f.invoice_id
      INNER JOIN res_partner par ON par.id = gkwh_owner.owner_id
      WHERE i.date_invoice BETWEEN %(start)s AND %(end)s
      GROUP BY gkwh_owner.factura_line_id, gkwh_owner.owner_id ORDER BY gkwh_owner.factura_line_id  DESC) AS parcial
GROUP BY owner_id, owner_id, owner_vat
ORDER BY owner_id;
