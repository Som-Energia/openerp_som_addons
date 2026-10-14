# Millores de rendiment

`_ff_get_polissa` resol els F1 per lots amb una sola consulta de contractes.
L'índex següent accelera la cerca de l'últim F1 normal durant la generació d'M1.

## Creació de l'índex

La migració del mòdul el crea en instal·lacions noves i en actualitzacions,
amb `CREATE INDEX` transaccional (pot bloquejar escriptures mentre es construeix).
`IF NOT EXISTS` evita repetir-lo si ja s'ha creat manualment, però només comprova
el nom, no la definició ni la validesa.

En bases de dades grans, es pot crear abans del desplegament amb l'opció concurrent:

Executar a la base de dades corresponent amb `psql`, amb autocommit i **fora
de qualsevol transacció**. No executar-ho com una migració d'OpenERP.

**1. Comprovar els índexs existents:**

```sql
SELECT indexrelid::regclass AS index_name,
       indisvalid, indisready, pg_get_indexdef(indexrelid) AS definition
FROM pg_index
WHERE indrelid = 'public.giscedata_facturacio_importacio_linia'::regclass;
```

Si ja hi ha un índex equivalent i vàlid, no cal crear-lo. Si el nom ja existeix
amb una altra definició, aturar-se i revisar-lo.

**2. Si no existeix, crear-lo en una franja de poca càrrega i abans
d'actualitzar el mòdul:**

```sql
\set AUTOCOMMIT on
CREATE INDEX CONCURRENTLY IF NOT EXISTS giscedata_facturacio_importacio_linia_cups_text_fecha_factura_h
ON public.giscedata_facturacio_importacio_linia
(cups_text, fecha_factura_hasta DESC)
WHERE type_factura = 'N';
```

**3. Repetir la comprovació:** confirmar la definició anterior i que
`indisvalid` i `indisready` siguin `true`. `IF NOT EXISTS` només comprova
el nom, no la definició ni la validesa.

Si una creació fallida deixa aquest índex invàlid, confirmar que ja no
s'està construint abans d'eliminar-lo i repetir els passos 2 i 3:

```sql
DROP INDEX CONCURRENTLY IF EXISTS public.giscedata_facturacio_importacio_linia_cups_text_fecha_factura_h;
```

No eliminar un índex vàlid o de definició diferent.
