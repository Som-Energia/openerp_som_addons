        SELECT
            soci_id,
            name,
            nsoci,
            nif,
            lang,
            consumannual,
            consumprioritario,
            ncontractes,
            polizas_titular,
            polizas_pagador,
            email,
            CEIL((0-inversion)/100) as acciones,
	    already_invested,
            ARRAY[8] @> categories AS essoci,
            FALSE
        FROM (
            SELECT DISTINCT ON (sub.soci_id)
                sub.soci_id as soci_id,
                sub.name AS name,
                sub.nsoci AS nsoci,
                sub.nif AS nif,
                sub.lang AS lang,
                sub.consumannual AS consumannual,
		sub.consumprioritario as consumprioritario,
                sub.ncontractes AS ncontractes,
		sub.polizas_titular AS polizas_titular,
		sub.polizas_pagador AS polizas_pagador,
                address.email,
                categories,
                FALSE
            FROM (
                SELECT
                    soci.id AS soci_id,
                    soci.name AS name,
                    soci.ref AS nsoci,
                    soci.vat AS nif,
                    soci.lang AS lang,
                    SUM(cups.conany_kwh) AS consumannual,
                    COALESCE(	MAX(CASE when POL.PAGADOR=soci.id THEN cups.conany_kwh ELSE NULL END), 
				MAX(CASE when POL.PAGADOR!=soci.id AND POL.TITULAR=soci.id THEN cups.conany_kwh ELSE NULL END)
			    ) as consumprioritario,
                    COUNT(CUPS.ID) AS ncontractes,
                    SUM(CASE WHEN POL.PAGADOR!=soci.id and pol.titular=soci.id then 1 else 0 end) AS polizas_titular,
                    ARRAY_AGG(cat.category_id) as categories,
                    SUM(CASE WHEN POL.PAGADOR=soci.id then 1 ELSE 0 end) AS polizas_pagador,
                    FALSE
                FROM res_partner AS soci
                LEFT JOIN
                    giscedata_polissa AS pol ON 
                        pol.titular = soci.id OR
                        pol.pagador = soci.id AND 
                        pol.active AND 
                        pol.state = 'activa'
		LEFT JOIN
		    giscedata_cups_ps AS cups ON
			cups.id = pol.cups
                LEFT JOIN
                    res_partner_category_rel AS cat ON
                    cat.partner_id = soci.id
                WHERE
                    soci.active AND 
                    pol.state = 'activa' AND 
                    cups.active and
                    TRUE
                GROUP BY 
		    SOCI.ID
                ORDER BY
                    soci.id ASC
            ) AS sub
            LEFT JOIN
                res_partner_address AS address ON (address.partner_id = sub.soci_id)
            WHERE
                address.active AND
                address.email IS NOT NULL AND
                address.email != '' AND
                TRUE
            GROUP BY
                sub.soci_id,
                sub.name,
                sub.nsoci,
                sub.nif,
                sub.lang,
                sub.consumannual,
                sub.consumprioritario,
                sub.ncontractes,
		sub.polizas_titular,
		sub.polizas_pagador,
                address.email,
                categories,
                TRUE
        ) AS result
        RIGHT JOIN (
            SELECT 
		sum(LINE.AMOUNT) as inversion,
                max(partner_id) AS already_invested
            FROM payment_line AS line
            LEFT JOIN
                payment_order AS remesa ON remesa.id = line.order_id 
            WHERE
                remesa.mode = 19
            GROUP BY partner_id
            ) AS investments ON already_invested = soci_id 
        WHERE
            soci_id is null
        ORDER BY
            name ASC
