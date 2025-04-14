select
distri.ref as codi_distri, cups.name as CUPS, auto.cau as CAU,
pol.autoconsumo as TipoAutoconsumo, coalesce(nullif(auto.subseccio, ''), 'aa') as TipoSubseccion,
auto.collectiu as Colectivo, gen.cil as CIL, gen.tec_generador as TecGenerador,
gen.combustible as Combustible, gen.pot_instalada_gen as PotInstaladaGen,
gen.tipus_installacio as TipoInstalacion, gen.esquema_mesura as EsquemaMedida, gen.ssaa as SSAA
from giscedata_autoconsum_cups_autoconsum hist
left join giscedata_cups_ps cups on hist.cups_id = cups.id
left join giscedata_autoconsum auto on hist.autoconsum_id = auto.id
left join giscedata_autoconsum_generador gen on auto.id = gen.autoconsum_id
left join giscedata_polissa pol on cups.polissa_polissa = pol.id
left join res_partner distri on pol.distribuidora = distri.id
where
hist.data_inici <= %(data_inici)s and (hist.data_final is null or hist.data_final >= %(data_final)s)
order by
distri.ref asc, cups.name asc, auto.cau asc, gen.cil asc;

