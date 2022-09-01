SELECT pc.name categoria,
       m.name municipi,
       p.ref num_soci,
       p.vat nif,
       pa.email email,
       pa.name nom,
       prov.name provincia,
       pa.zip codi_postal,
       p.lang idioma,
       com.name comarca,
       ccaa.name comunitat_autonoma
FROM res_partner_address AS pa
LEFT JOIN res_partner AS p ON (p.id=pa.partner_id)
LEFT JOIN res_partner_category_rel AS p__c ON (pa.partner_id=p__c.partner_id)
LEFT JOIN res_partner_category AS pc ON (pc.id=p__c.category_id and pc.name='Soci')
LEFT JOIN res_municipi AS m ON (m.id=pa.id_municipi)
LEFT JOIN res_country_state AS prov ON (prov.id=pa.state_id)
LEFT JOIN res_comunitat_autonoma AS ccaa ON (ccaa.id=prov.comunitat_autonoma)
LEFT JOIN res_comarca AS com ON (com.id=m.comarca)
WHERE pa.active AND p__c.category_id IS NOT NULL AND
  p__c.category_id = (SELECT id FROM res_partner_category WHERE name='Soci')
ORDER BY p.ref
