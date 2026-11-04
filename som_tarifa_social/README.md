# som_tarifa_social

Mòdul que conté la lògica per posar i treure la tarifa social

## Propietat de les tarifes

`som_tarifa_social` defineix les tarifes i els mètodes de canvi. `www_som` hi
depèn i els utilitza per herència, sense tornar a carregar les dades socials.
Els identificadors antics `www_som.*` es conserven com a àlies protegits sobre
els mateixos registres, per mantenir la compatibilitat.

El fitxer `www_som/data/pricelist_social_data.xml` es manté perquè hi apunten
migracions històriques, però ja no figura al manifest de `www_som`. No és una
segona font de configuració: els canvis nous corresponen a aquest mòdul.

## Primera instal·lació (24.5.1)

La instal·lació reutilitza les tarifes existents de `www_som` abans de carregar
l'XML. No es modifiquen contractes ni es copien o eliminen tarifes.

| Estat de les dades | Comportament |
| --- | --- |
| ID XML vàlid | Conserva el registre i hi vincula els dos identificadors |
| ID trencat o absent i una tarifa amb el nom exacte | Reutilitza aquesta tarifa |
| Cap tarifa existent | L'XML la crea i el pas posterior completa els àlies |
| Dos IDs vàlids sobre registres diferents o noms ambigus | Atura el procés sense fusionar registres |

Els àlies de `www_som` queden protegits amb `noupdate=True`. Les versions,
regles de preus i configuració de renovació existents es conserven; els camps
de la tarifa definits a l'XML continuen subjectes a la càrrega estàndard de l'ERP.
Una tarifa creada sense regles de preus requereix configurar-les abans de facturar.

Abans de desplegar, feu una còpia de seguretat i proveu el procés en una còpia
de la base de dades. Si apareix un conflicte, reviseu els IDs indicats al log;
no elimineu tarifes per forçar la instal·lació.

La conciliació consta només de dos scripts a `installation/5.0.24.5.1/`:
un pas anterior a l'XML que reutilitza els registres i un de posterior que
completa els àlies. No fan `commit`: la transacció correspon al carregador.

Aquests scripts només s'executen en la primera instal·lació. No hi ha migració
automàtica per a bases locals que ja tinguin instal·lada una versió anterior:
actualitzar el mòdul o reiniciar l'ERP no executarà aquesta conciliació.
Per validar la instal·lació, utilitzeu una còpia on el mòdul encara no estigui
instal·lat; no el desinstal·leu d'una base amb dades per forçar-ne l'execució.

### Proves de regressió

Des del checkout principal, amb l'entorn virtual del ERP activat i els serveis de
tests preparats. Substituïu `/path/to/workspace` per la carpeta que conté els
repositoris `erp`, `destral` i `openerp_som_addons`:

```bash
WORKSPACE="/path/to/workspace" scripts/run-tests.sh \
  --no-requirements -m som_tarifa_social \
  -t test_pricelist_migration.TestPricelistMigration
```

Les proves d'integració amb `www_som` comproven els àlies, els mètodes heretats
i la recàrrega de les dades declarades als manifests, amb la neteja de metadata,
en tots dos ordres. Verifiquen que es conserven els IDs i els preus configurats:

```bash
WORKSPACE="/path/to/workspace" scripts/run-tests.sh \
  --no-requirements -m www_som \
  -t test_social_tariff_integration.TestSocialTariffIntegration
```
