SELECT
  f.id
FROM giscedata_facturacio_factura f
INNER JOIN account_invoice i
  ON i.id = f.invoice_id
WHERE
  i.number IS NOT NULL
  AND f.enviat_mail_id IS NULL
  AND i.type IN ('out_invoice', 'out_refund')
  AND i.date_invoice >= '2020-01-01'
  AND i.date_invoice < %s
  AND (
    SELECT id
    FROM ir_attachment a
    WHERE a.res_model = 'giscedata.facturacio.factura' AND a.res_id = f.id
    AND a.datas_fname = ('STORED_' || i."number" || '.pdf')
  ) IS NULL
ORDER BY i.date_invoice
