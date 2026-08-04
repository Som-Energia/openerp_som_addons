# Skill Registry

**Delegator use only.** Any agent that launches sub-agents reads this registry to resolve compact rules, then injects them directly into sub-agent prompts. Sub-agents do NOT read this registry or individual SKILL.md files.

See `_shared/skill-resolver.md` for the full resolution protocol.

## User Skills

> **Configuració inicial** (executar una vegada):
> ```bash
> cd $HOME/.config/opencode/skills
> ln -s $HOME/somenergia/src/openerp_som_addons/.agents/skills openerp_som_addons
> ```
> OpenCode cercarà `.agents/skills/` dins del projecte.

| Trigger | Skill | Path |
|---------|-------|------|
| Quan necessites crear una branca nova per treballar | git-branch | .agents/skills/git-branch/SKILL.md |
| Quan necessites fer un commit de codi | git-commit | .agents/skills/git-commit/SKILL.md |
| Quan necessites crear una Pull Request | git-pr | .agents/skills/git-pr/SKILL.md |
| Quan necessites executar tests d'un mòdul OpenERP amb destral | erp-test | .agents/skills/erp-test/SKILL.md |
| Quan necessites arrencar el servei ERP, executar l'ERP, o obrir l'entorn de desenvolupament | erp-start | .agents/skills/erp-start/SKILL.md |
| Quan necessites crear un script de migració, modificar el model, o actualitzar un mòdul a producció | erp-migration | .agents/skills/erp-migration/SKILL.md |
| Quan necessites afegir casos de test/demo XML en un mòdul OpenERP | erp-demo-testcase | .agents/skills/erp-demo-testcase/SKILL.md |
| Quan necessites fer triage d'incidències de Sentry, "analitzar sentry", "triar incidents" | sentry-triage | .agents/skills/sentry-triage/SKILL.md |
| Quan necessites actualitzar un report legal o contractual `.mako` a partir d'un `docx` o `md` | update-contract-report | .agents/skills/update-contract-report/SKILL.md |

## Compact Rules

### git-branch
- Format de branca: `<type>_<description>` (ex: `ADD_user_registration`)
- Tipus: IMP_ (millora), FIX_ (bug), MOD_ (canvi), ADD_ (nova), REF_ (refactor), TEST_, DOCS_, CI_
- Descripció: 2-3 paraules en anglès, lowercase, max 50 caràcters
- Separador: guió baix entre tipus i descripció
- Sempre fer `git fetch origin && git pull origin main` abans de crear branca

### git-commit
- Format: `<emoji> <description>` (ex: `✨ add user auth`)
- L'emoji ja indica el tipus; no afegir `feat:`, `fix:`, etc.
- Emoji obligatori seguit d'un espai
- Descripció en anglès, max 72 caràcters, imperatiu
- Context: utilitzar per guardar canvis implementats

### git-pr
- PLANTILLA OBLIGATÒRIA: Omplir totes les seccions (Objectiu, Targeta, Comportament antic, Comportament nou, Comprovacions)
- Totes les sections: Omple-les totes, no deixis espais buits
- Idioma: Català per a la descripció
- Títols: Clar i descriptiu

### erp-test
- Requisits: Virtualenv activat + Docker (PostgreSQL, MongoDB, Redis)
- Command: `scripts/run-tests.sh <database> -m <module_name>`
- Contenidors esperats: src_db_1, src_mongo_1, src_redis_1

### erp-start
- Requisits: Virtualenv activat + Docker (PostgreSQL, MongoDB, Redis)
- Command: `erpserver -d <database>`
- Full path: `/home/oriol/somenergia/src/erp/server/bin/openerp-server.py --no-netrpc --price_accuracy=6 --config=$HOME/conf/erp.conf -d <database>`
- Opcions: --update=<module> per actualitzar mòdul, --run-scripts=<module> per migracions
- Interfície: http://localhost:8069

### erp-migration
- Format: `<pre|post>-<0001>_<descripcio>.py`
- Script automàtic: `python scripts/create_migration_script.py`
- Estructura: `<modul>/migrations/5.0.25.5.0/post-0001_*.py`
- Executar: `erpserver -d <db> --run-scripts=<module>` o `--update=<module>`

### erp-demo-testcase
- Inputs mínims: `module_name`, `model_name`, `record_id_prefix`
- Detectar camps `required=True` del model abans d'escriure XML
- Per `many2one` obligatoris, reutilitzar XML IDs existents o crear prerequisits
- Escriure a `demo/*.xml` i registrar el fitxer al manifest si cal

### sentry-triage
- MCP Sentry requerit: Configurar a OpenCode (self-hosted mode)
- Workflow: 1) Llista incidents → 2) Identifica tipus (error vs slow) → 3) Determina repo (erp vs addons) → 4) Crea issue sense PII → 5) Obrir PR
- Repo segons stack: `/home/erp/src/erp/...` → gisce/erp (branca developer), `openerp_som_addons/` → openerp_som_addons (branca main)
- Labels obligatoris: bug + autotask
- Prohibit: Noms, emails, telèfons, CUPS, dades personals
- branca PR: developer (gisce/erp) o main (openerp_som_addons), MAI rolling_erp01

### update-contract-report
- La font de veritat (`docx` o `md`) l'ha de confirmar l'usuari; no barrejar fonts sense confirmar
- Ignorar colors, highlights i marques editorials del document font; només conservar contingut i estructura
- Tocar només plantilles `.mako`/HTML del report, no backend Python o lògica de render, tret que l'usuari ho demani explícitament
- Preservar fórmules, subíndexs/superíndexs, notes al peu i enllaços en HTML net
- Si existeixen versions CA i ES, revisar consistència de contingut entre idiomes

## Project Conventions

| File | Path | Notes |
|------|------|-------|
| AGENTS.md | AGENTS.md | Index — references files below |
| .github/docs/estil.md | .github/docs/estil.md | Estil de codi |
| .github/docs/evitar.md | .github/docs/evitar.md | Evitar patrons |
| .github/docs/arquitectura.md | .github/docs/arquitectura.md | Arquitectura |
| .github/docs/desenvolupament.md | .github/docs/desenvolupament.md | Desenvolupament |
| pull_request_template.md | pull_request_template.md | Plantilla PR |

Read the convention files listed above for project-specific patterns and rules. All referenced paths have been extracted — no need to read index files to discover more.
