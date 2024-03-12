select
 partner_id
,ss.data_baixa_soci as date_expiry
from somenergia_soci ss
where ss.baixa=true and ss.data_baixa_soci <= %(data_limit)s
and not exists
(
    select gp2.titular
    from giscedata_polissa gp2
    where (gp2.state = 'activa' or (gp2.state = 'baixa' and gp2.data_baixa > %(data_limit)s))
    and gp2.titular = ss.partner_id
)
