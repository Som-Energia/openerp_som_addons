# Evidències i punts de verificació

Patrons extrets dels diffs de GitHub, contrastats amb el codi local. Base del
repositori en redactar la skill: `bfcb743b` (`origin/main`). Revalida les eines
en cada entorn: una PR integrada no converteix totes les seves decisions en
regles universals.

## PRs de referència

### #1518 — Text font, placeholders, duplicats i càrrega

[Fix extended phone support hours in invoice pdf](https://github.com/Som-Energia/openerp_som_addons/pull/1518),
integrada el 2026-11-03.

- Canvia l'horari d'atenció a
  `giscedata_facturacio_comer_som/report/components/emergency_complaints_td/emergency_complaints_td.mako`.
- Sincronitza el literal complet al POT i a `i18n/es_ES.po`, incloent l'espai
  que substitueix un `<br />`, i conserva el `%s` del telèfon interpolat.
- Unifica l'entrada duplicada `Maxímetre (kW)` afegint la ubicació a l'entrada
  ja existent, tant al POT com al PO.
- Afegeix `post-0008_reload_support_hours_translations.py` amb `trans_load`.

**Lliçó:** tracta conjuntament el font, la clau exacta, les ubicacions, el
text traduït i la càrrega. No copiïs la versió/numeració històrica de migració.

### #1501 — Una traducció existent pot necessitar referències noves

[Correct Spanish translations in contract summary](https://github.com/Som-Energia/openerp_som_addons/pull/1501),
integrada el 2026-10-20.

- No canvia els `msgstr`: afegeix referències a `summary_identification.mako`
  i `summary_offer.mako` a entrades ja existents.
- Ho fa a `som_polissa_condicions_generals.pot` i a `es_ES.po`.
- Carrega el PO amb
  `post-0003_FIX_summary_translations_migrate_translations.py`.

**Lliçó:** en reutilitzar textos en altres components, revisa també les
ubicacions i recarrega el PO. No dedueixis que tots els lookups de totes les
versions d'ERP fallen sempre sense la ubicació: poden existir fallbacks.

### #1484 — Contraexemple: regenerar només el POT

[Arreglar traduccions incomplertes al resum del document contractual](https://github.com/Som-Energia/openerp_som_addons/pull/1484),
tancada **sense integrar** en el moment de la revisió.

El diff només actualitza `som_polissa_condicions_generals.pot`, sense PO ni
càrrega. Les intencions de la descripció no són prova que el comportament
quedi resolt; un POT prepara l'inventari, no aporta la traducció castellana.

### #1398 — Idioma local del helper i coincidència exacta

[Subcomponents amb problemes de traduccions](https://github.com/Som-Energia/openerp_som_addons/pull/1398),
integrada el 2026-08-17.

- Introdueix `context = {"lang": get_lang_partner(fact)}` en helpers del
  backend de factures, encara que no el passin explícitament a `_()`.
- Canvia `Total periode ` per `Total període ` i `Maximetre (kW)` per
  `Maxímetre (kW)` a Mako, POT i PO.
- Afegeix una migració de càrrega d'`es_ES.po`.

**Lliçó:** ni els accents ni els espais finals són irrellevants per al
lookup. El `context` aparentment no usat pot ser llegit per introspecció.

### #1448 — El català també pot ser l'idioma destí

[Afegir ajudant de pagament amb targeta](https://github.com/Som-Energia/openerp_som_addons/pull/1448),
integrada el 2026-11-03. Exemple concret:
[commit 8e62eab4](https://github.com/Som-Energia/openerp_som_addons/commit/8e62eab48a1780441081660d1dc6570578a192df).

Afegeix `som_card_payment/i18n/ca_ES.po` amb fonts angleses, com
`Missing required card fields: %s`, traduïdes al català mantenint `%s`.
És un exemple de direcció de traducció, no una plantilla de cobertura ni
de desplegament per copiar sense revisar el diff complet.

### #1466 — Localització que no passa pel catàleg

[Localitza els noms dels documents de Signaturit](https://github.com/Som-Energia/openerp_som_addons/pull/1466),
integrada el 2026-09-22.

Localitza noms de documents segons l'idioma del lead i manté el nom original
com a fallback si no identifica l'idioma/report. El diff final retorna noms
localitzats sense extensió, malgrat que la descripció de la PR afirma que la
conserva: contrasta sempre la descripció amb la implementació i els tests.
El mecanisme és una regla explícita del flux, no PO/POT. No s'ha d'exportar
aquest patró a tots els missatges d'usuari ni canviar-lo per gettext
automàticament en una correcció de text.

## Implementació contrastada

Les rutes següents són relatives al repositori indicat, no al directori de
la skill. S'han consultat en lectura; aquesta skill no autoritza a modificar
repositoris germans ni a sincronitzar-los fora de la política del workspace.

| Repositori / ruta | Què comprovar |
|------------------|---------------|
| `openerp_som_addons/scripts/create_migration_script.py` | `git diff --name-only main`, `TARGET_VERSION` manual i càrrega generada només per `i18n/es_ES.po`. |
| `openerp_som_addons/scripts/run-tests.sh` | Fixa `DESTRAL_TESTING_LANGS` a `['en_US','ca_ES','es_ES']`; executar-lo només a través del wrapper en worktrees. |
| `openerp_som_addons/som_polissa_condicions_generals/i18n/babel.cfg` | Configuració existent per a Mako UTF-8. |
| `erp/server/bin/tools/translate.py` | `GettextAlias` inspecciona el context local; `TinyPoFile` interpreta `#:`; `trans_load`/`trans_load_data` carreguen el PO i gestionen recursos `noupdate`. |
| `erp/server/bin/addons/base/module/wizard/wizard_export_lang.py` | `append_report_translations` requereix un mòdul i format intern `pot`; extreu Mako i genera ubicacions `rml:`. Pot crear `babel.cfg` si falta: revisa l'estat després de validar/exportar. |
| `erp/server/bin/addons/c2c_webkit_report/webkit_report.py` | `translate_call` consulta tipus `rml`, plantilla i idioma del parser. |
| `erp/server/bin/addons/base/ir/ir_translation.py` | `_get_source` fa lookup per idioma/tipus/nom/font i, en la versió revisada, fallback sense nom; utilitza cache. |
| `destral/destral/testing.py` | `OOBaseTests.test_translate_modules` exporta un POT temporal, afegeix Mako i compara PO/POT; sense idiomes configurats no valida. |
| `destral/destral/utils.py` | `compare_pofiles` compara IDs i valors no buits, no garanteix la correcció d'ubicacions ni del render. |

Versions locals consultades per als mecanismes interns: `erp` a
`e7736ff00bc` i `destral` a `d3b20a9`. Si no coincideixen amb l'entorn de la
tasca, inspecciona la implementació efectiva abans d'assumir-ne el comportament.
