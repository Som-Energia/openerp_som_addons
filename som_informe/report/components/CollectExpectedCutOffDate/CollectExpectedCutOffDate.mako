<%page args="d" />
${_(u"En cas que no s’abonin les factures pendents, a partir del dia %s podrem sol·licitar un tall de subministrament per impagament a l’empresa de distribució %s") % (d.expected_cut_off_date, d.distri_name)} <br />
<br />
