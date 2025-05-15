/* Partners titular d'una pòlissa que està de baixa abans de la data_limit i que NO son o estan:
 * SOCIS ACTIUS
 * COM A TITULAR d'alguna pòlissa activa o de baixa menys després de la data_limit
 * COM A ADMINISTRADORA d'alguna pòlissa activa o de baixa després de la data_limit
 * COM A SOCI d'alguna pòlissa activa o de baixa després de la data_limit
 * COM A NOTIFICACIÓ d'alguna pòlissa activa o de baixa després de la data_limit
 * AMB INVERSIONS, APORTACIONS, GNKWH amb darrera data efectiva després de la data_limit
 */
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
	(
		select distinct partner_id
		from
		(
			--SOCIS ACTIUS
			select
			 partner_id
			from somenergia_soci ss
			where ss.baixa = false

			union all

			--COM A TITULAR
			select gp2.titular as partner_id
			from giscedata_polissa gp2
			where (gp2.state = 'activa' or (gp2.state = 'baixa' and gp2.data_baixa > %(data_limit)s))

			union all

			--COM A ADMINISTRADORA
			select gp2.administradora as partner_id
			from giscedata_polissa gp2
			where gp2.administradora is not null and
			(gp2.state = 'activa' or (gp2.state = 'baixa' and gp2.data_baixa > %(data_limit)s))

			union all

			--COM A SOCI
			select gp2.soci as partner_id
			from giscedata_polissa gp2
			where gp2.soci is not null and
			(gp2.state = 'activa' or (gp2.state = 'baixa' and gp2.data_baixa > %(data_limit)s))

			union all

			--COM A NOTIFICACIÓ
			select gp2.altre_p as partner_id
			from giscedata_polissa gp2
			where gp2.altre_p is not null and
			(gp2.state = 'activa' or (gp2.state = 'baixa' and gp2.data_baixa > %(data_limit)s))

			union all

			--INVERSIONS, APORTACIONS, GNKWH
			select ss.partner_id as partner_id
			from generationkwh_investment gi
			inner join somenergia_soci ss on ss.id = gi.member_id
			where gi.last_effective_date is null or gi.last_effective_date > %(data_limit)s

		) as sq_partners_to_exclude where sq_partners_to_exclude.partner_id = gp.titular
	)
) as sq where rn = 1
