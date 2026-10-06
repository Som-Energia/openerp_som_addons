---
name: erp-workspace-sync
description: >
  Sincronitza les dependències compartides del workspace OpenERP amb el perfil
  de refs de CI, admetent excepcions locals per repositori. Utilitza-la abans
  de crear una branca o un worktree nou per a una funcionalitat ERP.
---

# ERP workspace sync

Utilitza aquesta skill abans de crear una branca de funcionalitat o un
worktree d'`openerp_som_addons`. El perfil per defecte replica les refs de
`.github/actions/bootstrap-erp/bootstrap-erp-env.sh`: en particular,
`erp` usa `rolling_erp01`.

No és un hook Git deliberadament. Un hook `post-checkout` s'executaria també
quan es canvia a una branca existent, no pot distingir de manera fiable una
branca nova i modificaria repositoris germans fora de la transacció Git. El
script versionat dóna un punt d'entrada explícit, auditable i amb proteccions
contra canvis locals.

## Procediment

1. Situa't en el checkout o worktree d'`openerp_som_addons` que prepara el
   desenvolupament i revisa `git status` de cada repositori afectat.
2. Executa el perfil de CI:

   ```bash
   scripts/sync-workspace-repositories.sh
   ```

   Des d'un worktree sota `openerp_som_addons-worktrees/`, el script detecta
   automàticament el directori pare del workspace. Es pot indicar un altre amb
   `--workspace /ruta/al/workspace`. El perfil Python es detecta de l'intèrpret
   actiu o de `PYTHON_VERSION`; fixa'l explícitament, per exemple amb
   `--python-version 3.10`, si l'entorn no és l'habitual.
3. Només quan la sincronització acaba correctament, crea la branca o el
   worktree. Per crear worktrees, continua respectant la política d'aprovació,
   `git fetch origin` i la base `origin/main` d'`AGENTS.md`.

## Perfil de dependències

La font de veritat local és `.agents/workspace-repositories.tsv`. Defineix el
nom del directori, el remote que cal fer servir i una estratègia per a cada
dependència del bootstrap de CI:

- `branch`: fa checkout de la branca indicada i només l'avança amb
  fast-forward;
- `default-branch`: usa la branca HEAD anunciada pel remote;
- `latest-tag`: queda en detached HEAD al tag més recent del remote
  seleccionat;
- el perfil `py2` només s'inclou amb Python 2.x (`somenergia-utils`); el perfil
  `all` s'aplica a totes les versions.

El perfil no actualitza el worktree d'`openerp_som_addons` mateix. Tampoc
clona repositoris absents: CI els clona amb credencials, mentre que el
workspace local no ha de crear repositoris de manera implícita. Per defecte,
un repositori absent és un error; `--allow-missing` només serveix per a una
tasca que sap que no el necessita i no valida un entorn equivalent a CI.

## Excepcions de branca

Per fer una prova o desenvolupament amb una branca diferent, passa una o més
excepcions puntuals:

```bash
scripts/sync-workspace-repositories.sh --branch erp=developer
scripts/sync-workspace-repositories.sh \
    --branch erp=developer \
    --branch giscedata_facturacio_indexada_som=FIX_invoice_rounding
```

Per recordar-les només en aquest checkout/worktree, afegeix `--persist`:

```bash
scripts/sync-workspace-repositories.sh --branch erp=developer --persist
```

L'override només s'escriu si la sincronització acaba correctament. Per desar o
retirar una preferència sense sincronitzar, usa explícitament `--persist-only`:

```bash
scripts/sync-workspace-repositories.sh --clear-branch erp --persist-only
```

Això escriu `.agents/workspace-repositories.local`, que està ignorat per Git,
dins del checkout des d'on s'executa el script. En crear un worktree, la
sincronització prèvia s'executa des del checkout principal; si cal persistir
l'override al worktree nou, crea'l i executa després el script des d'aquell
worktree amb `--branch ... --persist`.

Un `erp/` compartit només pot tenir una branca activa alhora. Per tant, les
excepcions persistents són específiques del worktree que les documenta, però
no aïllen les dependències d'altres worktrees simultanis. Coordina-les amb
l'equip o usa worktrees de les dependències si calen dos entorns incompatibles
alhora.

Si una branca remota ha estat reescrita, el comportament per defecte és aturar
la sincronització. Només després de revisar-ho, es pot acceptar de manera
explícita: `--accept-rewritten-branch poweremail2`. El script crea una branca
`workspace-sync-backup/...` abans del reset necessari.

## Proteccions

- El script falla abans de canviar cap working tree si una dependència té
  canvis rastrejats/no rastrejats, o un fitxer ignorat que la ref destí
  versionaria.
- Un lock del workspace serialitza les sincronitzacions. Després s'adquireix
  el mateix lock de `scripts/run-tests-worktree.sh` i es mantenen tots dos
  fins al final: no es canvien dependències mentre un test del wrapper usa
  l'ERP. Si hi ha un manifest de test sense restaurar, la sincronització
  s'atura; cal recuperar-lo de manera segura amb el wrapper abans de continuar.
  `OPENERP_WORKSPACE_SYNC_LOCK_TIMEOUT` i `OPENERP_WORKTREE_TEST_LOCK_TIMEOUT`
  (600 segons per defecte) controlen els temps d'espera respectius.
- No fa `stash` ni descarta commits locals. També bloqueja una branca de destí
  que no es pugui avançar amb fast-forward, excepte amb
  `--accept-rewritten-branch`, que en conserva una còpia de seguretat.
- `--dry-run` mostra el pla sense canviar refs, checkouts ni overrides.
- Si falla després d'un fetch, no canvia cap working tree; resol primer el
  problema indicat i torna'l a executar.
