select partner_id, date_expiry
from
(
	select
	--array_agg(gp.titular) as partner_ids
	 gp.titular as partner_id
	,gp.data_baixa as date_expiry
	,ROW_NUMBER () OVER (
	    PARTITION BY gp.titular
	    ORDER BY gp.data_baixa desc
	  ) as rn
	from giscedata_polissa gp
	where
	state = 'baixa'
	and data_baixa <=  %(data_limit)s
	and titular is not null
	and not exists
	(   select gp2.titular
	    from giscedata_polissa gp2
	    where (gp2.state = 'activa' or (gp2.state = 'baixa' and gp2.data_baixa > %(data_limit)s))
	    and gp2.titular = gp.titular
	)
) as sq where rn = 1
