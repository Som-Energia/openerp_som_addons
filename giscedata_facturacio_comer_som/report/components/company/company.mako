<%page args="company" />
    <span style="font-weight: bold;">${company.name}</span><br />
    ${_(u"CIF:")} ${company.cif} <br />
    ${_(u"Domicili:")} ${company.street} ${company.zip} - ${company.city}<br />
    ${_(u"Adreça electrònica:")} ${company.email}<br/>
    ${_(u"Comercialitzadora del Mercat Lliure")}
