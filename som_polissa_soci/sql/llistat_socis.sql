WITH FirstAddress AS (
    SELECT pa.*, ROW_NUMBER() OVER (PARTITION BY pa.partner_id ORDER BY pa.id) AS rn
    FROM res_partner_address AS pa
    WHERE pa.active
)
SELECT
    pc.name AS categoria,
    m.name AS municipi,
    p.ref AS num_soci,
    p.vat AS nif,
    fa.email AS email,
    fa.name AS nom,
    prov.name AS provincia,
    fa.zip AS codi_postal,
    p.lang AS idioma,
    com.name AS comarca,
    ccaa.name AS comunitat_autonoma
FROM res_partner AS p
INNER JOIN FirstAddress AS fa ON (p.id = fa.partner_id AND fa.rn = 1)
INNER JOIN res_partner_category_rel AS p__c ON (fa.partner_id = p__c.partner_id)
INNER JOIN res_partner_category AS pc ON (pc.id = p__c.category_id AND pc.name = 'Soci')
INNER JOIN somenergia_soci AS ss ON (ss.partner_id = p.id AND ss.baixa IS False)
LEFT JOIN res_municipi AS m ON (m.id = fa.id_municipi)
LEFT JOIN res_country_state AS prov ON (prov.id = fa.state_id)
LEFT JOIN res_comunitat_autonoma AS ccaa ON (ccaa.id = prov.comunitat_autonoma)
LEFT JOIN res_comarca AS com ON (com.id = m.comarca)
WHERE p.active
ORDER BY p.ref
