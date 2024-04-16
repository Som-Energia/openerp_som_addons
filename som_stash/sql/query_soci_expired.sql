select
 partner_id
,ss.data_baixa_soci as date_expiry
from somenergia_soci ss
where ss.baixa=true and ss.data_baixa_soci <= %(data_limit)s
