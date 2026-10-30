# Verificació del canvi de preus

## Abast de la simplificació

Aquesta revisió retira totes les herències i camps de campanya dels models
compartits, els snapshots, les restriccions editorials i els helpers que les
sostenien. Restaura el POT a la base de la PR. Les proves d'aquestes garanties
descartades es reemplacen per comprovacions del comportament estàndard acordat;
no es presenten els resultats de revisions anteriors com a proves del disseny
actual.

La suite específica comprova:

- absència de camps de campanya a lots/enviaments;
- delegació al resolver existent de banners amb plantilla, data actual i ID
  real de l'enviament, sense modificar el context del cridador;
- dates i assumpte coherents amb la resolució habitual de preus futurs;
- idioma del titular i fallback de traducció estàndard;
- selecció per domini, vigència i prioritat, sense restriccions noves als
  solapaments;
- lectura actualitzada dels banners a cada renderització, sense snapshot ni
  escriptures a lots/enviaments;
- permisos habituals de Banner Manager i HTML sense una allowlist nova;
- contingut editorial que no es torna a executar com a Mako;
- còpia normal d'enviaments i tractament d'errors normal de Poweremail;
- renderer Poweremail, contracte de selecció PDF i migració idempotent;
- regressions de càlculs, dates de preus, fiscalitat i decimals.

## Resultats de la simplificació

- Selecció específica: **25 tests, 24 passen i 1 omès**, sense errors. La DB
  s'ha creat de zero per aquesta revisió i s'ha reutilitzat per a l'execució
  final. L'omès és el smoke de conversió PDF real.
- Mako: **2 tests passen amb Python 2.7 i 2 amb Python 3**, cobrint les deu
  fixtures registrades i apuntant al worktree de la simplificació.
- Lint dels fitxers Python afectats, compilació Python 2.7/3, parseig XML,
  existència dels recursos del manifest i `git diff --check`: passen.
- `pre-commit` no està instal·lat en aquest entorn; no es declara executat
  ni passat. Les comprovacions estàtiques anteriors s'han executat directament.
- El POT té el mateix blob que a la base de la PR:
  `089a1fb8dfd0ad4a43c04bac0f1d1638f3459dad`. El diff acumulat del POT és buit.
- No s'introdueix cap `_inherit` sobre els cinc models compartits indicats a
  la review. La suite comprova també l'absència de camps de campanya.
- `flake8 .` continua fallant: els 4.658 diagnòstics són idèntics als de la
  versió anterior de la PR. No s'han corregit errors aliens.
- El generador de migracions s'ha executat amb `--dry-run`. Compara amb el
  `main` local i també informa de fitxers absents/candidats aliens a la PR.
  No s'ha aplicat cap candidat. La reconciliació manual confirma que la
  migració només ha de carregar seguretat del backend propi i les dades XML,
  sense inicialitzar camps de models compartits ni regenerar traduccions.

### Suite completa i comparació

Les dues versions s'han executat serialitzades amb el wrapper segur, les
mateixes dependències actuals i DB de proves separades. La base de comparació
és el worktree conservat a `ef345599`, anterior a les correccions de review.

| Versió | Tests | Fallades | Errors | Omesos |
| --- | --- | --- | --- | --- |
| PR anterior (`ef345599`) | 93 | 4 | 16 | 3 |
| Simplificació | 88 | 4 | 16 | 3 |

Els 20 noms de casos fallits coincideixen. La suite global **no està verda**.
El cas de traduccions continua fallant: ara indica vuit cadenes absents al POT,
incloses dues expressions de la nova plantilla. Es conserva el fitxer original
per petició expressa; no es regenera ni es desactiva el test per ocultar-ho.
Les proves dels snapshots, permisos especials i validators descartats no es
mantenen com a requisits: s'han substituït per proves del comportament acordat.

Logs locals:

- `/tmp/price-change-simplified-final.log`: selecció específica, exit 0.
- `/tmp/price-change-simplified-full.log`: suite completa, exit 1.
- `/tmp/price-change-simplified-baseline.log`: comparació anterior, exit 1.
- `/tmp/price-change-simplified-flake8.log`: lint global preexistent.
- `/tmp/price-change-simplified-migration.log`: proposta revisada, no aplicada.

## Entorn i reproducció

PostgreSQL, MongoDB i Redis es reutilitzen des del projecte Compose del checkout
principal. S'usa Python 2.7 de l'entorn `erp` i el wrapper amb lock, declarant
els dos addons; no es canvien symlinks manualment.

```bash
WORKSPACE=/ruta/al/workspace PYENV_VERSION=erp \
OPENERP_TEST_DB_REF=price_change_simplified scripts/run-tests-worktree.sh \
  --addon som_polissa_condicions_generals --addon som_indexada -- \
  --no-requirements -m som_polissa_condicions_generals \
  -t TestPriceChangeCampaign -t TestPriceChangeCalculations
```

La primera execució d'aquesta selecció utilitza una DB nova per comprovar que
no s'afegeixen camps als models compartits. Les columnes residuals d'una DB
que hagués instal·lat una versió descartada de la PR no es destrueixen.

La sincronització de dependències s'ha omès per autorització expressa de
l'usuari després del fals positiu del symlink `poweremail2 -> poweremail`.
No s'ha corregit aquell script ni canviat la branca/commit d'ERP.

## Límits

El smoke de conversió PDF real és optatiu (`SOM_PRICE_CHANGE_PDF_SMOKE=1`) i
requereix Puppeteer/Chromium. Si no s'activa, es declara omès, no passat.
No s'han enviat correus, activat campanyes ni provat clients reals.

La suite completa i el lint global ja tenien errors abans de la review.
El POT restaurat no es regenera per fer passar el test genèric de catàlegs.
Cal separar aquests resultats dels de la selecció específica i no declarar
la suite global verda si no ho està.

Per als casos Mako sintètics de la PR 237:

```bash
export OPENERP_TEMPLATE_ADDONS_PATH=/ruta/al/worktree/openerp_som_addons
PYENV_VERSION=erp python -m unittest -v test_price_change_render
python3 -m unittest -v test_price_change_render
```

Aquests tests cobreixen les deu fixtures registrades sense DB ni SMTP; no
validen destinataris, adjunts o textos de producció. La revisió funcional i
jurídica i les comprovacions abans d'enviar continuen pendents.
