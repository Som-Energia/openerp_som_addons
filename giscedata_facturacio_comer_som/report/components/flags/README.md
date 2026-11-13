# Banderoles de la factura

Per a cada banderola aplicable, una imatge de `report.banner` té prioritat sobre
el PNG de reserva del mòdul. Per canviar-la, creeu un registre amb el codi de la
taula, configureu-ne la vigència i el domini, i adjunteu-hi una imatge PNG o JPG.
Els registres no es creen automàticament.

| Tipus | Codi de `report.banner` | Fitxers de reserva en aquest directori |
| --- | --- | --- |
| Autoconsum | `invoice_flag_autoconsum_ca` / `invoice_flag_autoconsum_es` | `flag_auto_little_ca.png` / `flag_auto_little_es.png` |
| Generation kWh | `invoice_flag_gkwh` | `flag_gkwh_little.png` (comú als idiomes) |
| Tarifa social | `invoice_flag_social` | `flag-dte-social_ca.png` / `flag-dte-social_es.png` |

## Configuració i idioma

- Model associat: `giscedata.facturacio.factura`.
- Data inicial i, opcionalment, data final, ordre i domini de selecció sobre la
  factura. La selecció usa la data de factura o, si no en té, la data final del
  període, amb el codi i l'ID de la factura.
- Imatge PNG o JPG al camp d'imatge; el contingut HTML no s'utilitza.

Autoconsum usa un codi diferent per idioma. Generation kWh i tarifa social
comparteixen codi entre idiomes: per seleccionar imatges diferents, configureu
registres amb el mateix codi i dominis com `[('lang_partner', '=', 'ca_ES')]` o
`[('lang_partner', '=', 'es_ES')]`. El selector no afegeix cap filtre d'idioma
automàtic.

Els fitxers de reserva d'autoconsum i tarifa social es trien amb les dues
primeres lletres de l'idioma del destinatari, en minúscules. Els dos PNG socials
de la taula existeixen; el sufix selecciona el fitxer, però no en tradueix el
contingut. Feu servir una imatge amb el text adequat a cada idioma.

La reserva social només s'utilitza si el fitxer existeix. Sense banner ni
fitxer per a l'idioma, s'omet la banderola sense reservar-li espai; els textos
socials s'apliquen independentment de la imatge. La banderola social només es
consulta si el detector existent identifica la tarifa social: preu al final
del període o presència de totes dues categories actuals, empresa i tarifa social.

Cal incloure els PNG de reserva al repositori i al desplegament. Copiar altres
PNG al directori no els activa automàticament: autoconsum i Generation kWh
continuen usant els noms de reserva de la taula.

Les dates permeten mantenir imatges diferents per a períodes diferents. Canviar
la imatge d'un banner existent també afecta les reimpressions de factures de
la seva vigència.

## Ordre i disposició

El backend construeix una única llista `flag_images`, en ordre autoconsum,
Generation kWh i tarifa social, només amb imatges disponibles. La plantilla
recorre la llista tant amb una com amb tres o més imatges; si és buida, no
renderitza el bloc. Cada imatge té una amplada de 65 px i conserva la proporció.
El bloc flota a la dreta: el text s'ajusta a l'espai restant i les imatges poden
passar a una altra línia. Cal revisar un PDF real si canvien les mides de les
imatges o la disposició. Les dades antigues sense llista usen el mateix
constructor per mantenir les banderoles existents.
