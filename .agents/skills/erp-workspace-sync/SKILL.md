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
   `--workspace /ruta/al/workspace`.
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
- `latest-tag`: queda en detached HEAD al tag més recent, igual que el
  bootstrap.

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

Això escriu `.agents/workspace-repositories.local`, que està ignorat per Git.
Es poden retirar posteriorment amb:

```bash
scripts/sync-workspace-repositories.sh --clear-branch erp --persist
```

Un `erp/` compartit només pot tenir una branca activa alhora. Per tant, les
excepcions persistents són específiques del worktree que les documenta, però
no aïllen les dependències d'altres worktrees simultanis. Coordina-les amb
l'equip o usa worktrees de les dependències si calen dos entorns incompatibles
alhora.

## Proteccions

- El script falla abans de fer fetch o checkout si qualsevol dependència
  present té canvis rastrejats o no rastrejats.
- No fa `reset --hard`, `stash` ni descarta commits locals. També bloqueja una
  branca de destí que no es pugui avançar amb fast-forward.
- `--dry-run` mostra el pla sense canviar refs ni checkouts.
- Si falla després d'un fetch, no canvia cap working tree; resol primer el
  problema indicat i torna'l a executar.
