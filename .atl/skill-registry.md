# Skill Registry

**Delegator use only.** Any agent that launches sub-agents reads this registry to resolve compact rules, then injects them directly into sub-agent prompts. Sub-agents do NOT read this registry or individual SKILL.md files.

See `_shared/skill-resolver.md` for the full resolution protocol.

## User Skills

> **Configuració inicial** (executar una vegada):
> ```bash
> cd $HOME/.config/opencode/skills
> ln -s $HOME/somenergia/src/openerp_som_addons/.atl/skills openerp_som_addons
> ```
> OpenCode cercarà `.atl/skills/` dins del projecte.

| Trigger | Skill | Path |
|---------|-------|------|
| Quan necessites crear una branca nova per treballar | git-branch | .atl/skills/git-branch/SKILL.md |
| Quan necessites fer un commit de codi | git-commit | .atl/skills/git-commit/SKILL.md |
| Quan necessites crear una Pull Request | git-pr | .atl/skills/git-pr/SKILL.md |
| Quan necessites executar tests d'un mòdul OpenERP amb destral | erp-test | .atl/skills/erp-test/SKILL.md |
| When creating a GitHub issue, reporting a bug, or requesting a feature | issue-creation | ~/.config/opencode/skills/issue-creation/SKILL.md |
| When creating a pull request, opening a PR, or preparing changes for review | branch-pr | ~/.config/opencode/skills/branch-pr/SKILL.md |
| When user asks to create a new skill, add agent instructions, or document patterns for AI | skill-creator | ~/.config/opencode/skills/skill-creator/SKILL.md |
| When writing Go tests, using teatest, or adding test coverage | go-testing | ~/.config/opencode/skills/go-testing/SKILL.md |
| When user says "judgment day", "judgment-day", "review adversarial", "dual review", "doble review", "juzgar", "que lo juzguen" | judgment-day | ~/.config/opencode/skills/judgment-day/SKILL.md |

## Compact Rules

### git-branch
- Format de branca: `<type>_<description>` (ex: `ADD_user_registration`)
- Tipus: IMP_ (millora), FIX_ (bug), MOD_ (canvi), ADD_ (nova), REF_ (refactor), TEST_, DOCS_, CI_
- Descripció: 2-3 paraules en anglès, lowercase, max 50 caràcters
- Separador: guió baix entre tipus i descripció
- Sempre fer `git fetch origin && git pull origin main` abans de crear branca

### git-commit
- Format: `<emoji> <type>: <description>` (ex: `✨ feat: add user auth`)
- Tipus: feat, fix, refactor, perf, test, docs, style, chore, build, ci, revert
- Emoji obligatori seguit d'un espai
- Descripció en anglès, max 72 caràcters, imperatiu
- Context: utilitzar per guardar canvis implementats

### git-pr
- PLANTILLA OBLIGATÒRIA: Omplir totes les seccions (Objectiu, Targeta, Comportament antic, Comportament nou, Comprovacions)
- Totes les sections: Omple-les totes, no deixis espais buits
- Idioma: Català per a la descripció
- Títols: Clar i descriptiu

### erp-test
- Requisits: Docker (PostgreSQL, MongoDB, Redis), pyenv (`erp`), OpenERP a `~/somenergia/src/erp/server/bin`
- Variables d'entorn obligatòries: PYTHONPATH, OPENERP_PRICE_ACCURACY, OORQ_ASYNC, OPENERP_DB_*, OPENERP_MONGODB_HOST, OPENERP_REDIS_URL
- Command: `dodestral <database> -m <module_name>`
- Contenidors esperats: src_db_1, src_mongo_1, src_redis_1

### issue-creation
- Blank issues disabled — ALWAYS use template (bug_report.yml o feature_request.yml)
- Every issue gets status:needs-review automatically
- Maintainer MUST add status:approved abans de PR
- Questions → Discussions, NOT issues

### branch-pr
- EVERY PR MUST link an approved issue — no exceptions
- Automated checks must pass before merge
- Branch naming: `type/description` (lowercase, regex: `^(feat|fix|chore|docs|style|refactor|perf|test|build|ci|revert)/[a-z0-9._-]+$`)
- PR body MUST contain: Linked Issue (Closes #N), PR Type (exactly one type:* label), Summary, Changes Table, Test Plan
- Conventional commits: `type(scope): description` or `type: description`

### skill-creator
- Skill structure: `skills/{skill-name}/SKILL.md`, optional assets/, references/
- Frontmatter obligatori: name, description (inclou trigger), license (Apache-2.0), metadata.author, metadata.version
- NO duplicar contingut existing (referenciar en lloc)
- Referencies: LOCAL paths, no URLs externes

### go-testing
- Table-driven tests: `t.Run(tt.name, func(t *testing.T) { ... })`
- Bubbletea testing: test Model.Update() directly, no Render()
- Teatest per flows interactius: `teatest.NewTestModel(t, m)`
- Golden file testing per output visual
- Mock dependencies amb interfaces

### judgment-day
- Launch TWO independent sub-agents via delegate (async, parallel)
- Pattern 0 OBLIGATORI: Resoldre skill registry abans de llançar judges
- Classificar warnings: WARNING (real) vs WARNING (theoretical)
- Verdicte: Confirmed (ambós), Suspect (un), Contradiction (desacord)
- After 2 fix iterations: ASK user abans de continuar
- Blocking rules: NO git push/commit fins re-judgment completa

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
