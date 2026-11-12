# Banderoles de la factura

Les banderoles d'autoconsum i Generation kWh es poden substituir amb registres
`report.banner`. Per a cada imatge, creeu un banner amb:

- Model associat: `giscedata.facturacio.factura`.
- Codi: `invoice_flag_autoconsum_ca`, `invoice_flag_autoconsum_es` o
  `invoice_flag_gkwh`.
- Data inicial i, opcionalment, data final, ordre i domini de selecció sobre la
  factura. La selecció usa la data de factura (o la data final del període si
  no té data de factura), l'idioma del destinatari i l'ID de la factura.
- Una imatge PNG o JPG al camp d'imatge. El contingut HTML no s'utilitza per a
  aquestes banderoles.

Les dates permeten mantenir imatges diferents per a períodes diferents. Canviar
la imatge d'un banner existent també afectarà les reimpressions de factures de
la seva vigència. Si no existeix una imatge aplicable, es manté el PNG original
del mòdul. Els registres no es creen automàticament; configureu-los quan es
vulguin gestionar les imatges des de l'ERP.
