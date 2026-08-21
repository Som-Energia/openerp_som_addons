# Dispatcher d'AGENTS.md del workspace

Aquest directori manté sota control de versions el context compartit de Pi per al workspace multirepositori de Som Energia.

## Per què cal un enllaç simbòlic?

Pi descobreix automàticament `AGENTS.md` des del directori actual cap als directoris pare, però no descobreix fitxers de repositoris germans. Per això, si els checkouts estan sota un directori com `~/src`, el dispatcher ha d'estar a:

```text
~/src/AGENTS.md
```

No fem de `~/src` un repositori Git: conté molts repositoris independents. El contingut versionat viu aquí i `~/src/AGENTS.md` n'és un enllaç simbòlic.

## Instal·lació

Amb `openerp_som_addons` clonat directament dins del workspace:

```bash
cd ~/src
ln -sfn openerp_som_addons/.agents/workspace/AGENTS.md AGENTS.md
```

Si el workspace és en una altra ruta, executa la mateixa comanda des de la seva arrel i adapta el camí relatiu al checkout d'`openerp_som_addons`.

Comprova-ho amb:

```bash
ls -l ~/src/AGENTS.md
```

Ha d'apuntar a `openerp_som_addons/.agents/workspace/AGENTS.md`.

## Ús i manteniment

- Pi carregarà el dispatcher quan s'iniciï des de l'arrel del workspace, qualsevol repositori fill o un worktree situat sota el workspace.
- Després de modificar-lo, inicia una sessió nova de Pi o usa `/reload`.
- Mantén aquí només normes transversals i un mapa de repositoris. Les normes específiques d'`openerp_som_addons` continuen a `../../AGENTS.md`.
- No facis un enllaç directe a l'`AGENTS.md` específic d'`openerp_som_addons`: aplicaria regles d'ERP a repositoris que no les comparteixen.
- Qualsevol canvi en aquests fitxers s'ha de revisar i versionar amb la resta del repositori `openerp_som_addons`.
