with CTE as (
	select pm.id as mail_id, gff.id as fact_id
	from poweremail_mailbox pm
	inner join giscedata_facturacio_factura gff on gff.id = split_part(pm.reference, ',', 2)::integer
	where pm.reference like 'giscedata.facturacio.factura,%'
	and (
		pm.pem_subject like 'Factura %'
		or pm.pem_subject like 'Som Energia: Factura %'
		or pm.pem_subject like 'Factura electricitat %'
		or pm.pem_subject like 'Factura electricidad %'
		or pm.pem_subject like 'Abonament factura electricitat % \\ Abono factura electricidad %'
		or pm.pem_subject like 'Reenviament % (adjunt correcte) / Reenvío % (adjunto correcto)'
		or pm.pem_subject like 'Reenvío de factura %'
		or pm.pem_subject like 'Reenviament Factura %'
		or pm.pem_subject like 'Reenvío Factura %'
		or pm.pem_subject like 'Factura complementària per expedient %'
		or pm.pem_subject like 'Factura complementaria por expediente %'
		or pm.pem_subject like 'Factura % - Factura expedient distribuïdora'
		or pm.pem_subject like 'Factura % - factura expedient distribuïdora'
		or pm.pem_subject like 'Factura % - Factura expediente distribuidora'
		or pm.pem_subject like 'Factura % - factura expediente distribuidora'
		or pm.pem_subject like 'Factura % associada a expedient'
		or pm.pem_subject like 'Factura % de expediente de la empresa distribuidora'
		or pm.pem_subject like 'Factura % per expedient distribuïdora'
		or pm.pem_subject like 'Factura abonadora %'
		or pm.pem_subject like 'Factura % amb facturació complementària de la distribuïdora'
		or pm.pem_subject like 'Factura % con expediente de la empresa distribuidora'
		or pm.pem_subject like 'Factura % amb expedient distribuïdora'
		or pm.pem_subject like 'Factura % amb expedient empresa distribuïdora'
		or pm.pem_subject like 'Factura % amb lectures estimades per la distribuïdora'
		or pm.pem_subject like 'Factura % - Import elevat'
		or pm.pem_subject like 'Facturación atrasada + Factura %'
		or pm.pem_subject like 'Factura % - diciembre'
		or pm.pem_subject like 'Factura % amb estimacions reiterades de la distribuïdora'
		or pm.pem_subject like 'Factura % con lectura estimada por la distribuidora'
		or pm.pem_subject like 'Factura % amb lectura estimada per la distribuïdora'
		or pm.pem_subject like 'Factura % amb lectures estimades de la distribuïdora'
		or pm.pem_subject like 'Factura % amb estimacions de la ditribuïdora'
	)
	order by pm.id
	limit 100000 -- remove this limit to make a full migration
)
update giscedata_facturacio_factura gff
SET enviat_mail_id = CTE.mail_id
from CTE
where CTE.fact_id = gff.id and gff.enviat_mail_id is null;
