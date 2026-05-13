---
name: sentry-triage
description: >
  Executa el workflow complet de triage d'incidències de Sentry.
  Automatitza: identificar repo objectiu, analitzar stack, crear issue/PR sense PII.
  Trigger: Quan necessites fer triage d'incidències de Sentry, "analitzar sentry", "triar incidents".
metadata:
  author: oriol
  version: "1.0"
---

## When to Use

Utilitza aquesta skill quan:
- Una incidència de Sentry arriba a producció
- Necessites identificar on fer el fix (gisce/erp vs openerp_som_addons)
- Vols crear una issue a partir d'un error de Sentry
- Necessites obrir una PR contra la branca correcta

## Prerequisits

MCP de Sentry configurat a OpenCode. Consulta la guia:
  [docs/guides/sentry-triage-workflow.md](../docs/guides/sentry-triage-workflow.md)

## Workflow de Triage

### Pas 1: Identificar el tipus d'incidència

Executa per llistar incidències actives:

```python
sentry_list_issues(
    organizationSlug="som-energia",
    regionUrl="<SENTRY_URL>",
    query="is:unresolved",
    sort="date",
    limit=10
)
```

**Decisió**:
- Errors reals → Procedir amb triage
- `slow request` → Deprioritzar (no és bug)

### Pas 2: Determinar el repositori objectiu

Per cada error, mira el stack trace:

| Stack | Repositori | Branca |
|-------|------------|--------|
| `/home/erp/src/erp/...` o mòduls `erp/` | `gisce/erp` | `developer` |
| `openerp_som_addons/` | `Som-Energia/openerp_som_addons` | `main` |

Executa per veure detall de l'error:

```bash
sentry_get_sentry_resource(url="<URL_SENTRY_ISSUE>")
```

Convencions del repositori:
* Mòduls de gisce/erp. Codi en anglès, text en castellà. El codi el trobaràs a la branca `rolling_erp01` però les PR han de sortir de la branca `developer`.
* Mòduls de Som-Energia/openerp_som_addons. Codi en anglès, texts en català, sortir de la branca main.

### Pas 3: Crear la Issue

Seguir les convencions del repo objectiu

**Dades obligatòries**:
- Link directe a Sentry
- Labels: `bug` + `autotask`
- Comportament antic vs esperat

**Dades PROHIBIDES** (mai en issues):
- Noms, cognoms, adreces, emails, telèfons
- CUPS, identificadors personals
- Valors operatius sensibles

**Per anonimitzar**: Reemplaça valors reals per `<EXAMPLE>` o descripcions generals.

### Pas 4: Obrir la PR
Seguir les convencions del repo objectiu

1. Crear branca seguint convencions del repo objectiu
2. Descriure seguint la plantilla del repo
3. Obrir contra branca que toqui.

## Comandes Ràpides

```python
# Llistar incidències sense resoldre
sentry_list_issues(
    organizationSlug="som-energia",
    regionUrl="<SENTRY_URL>",
    query="is:unresolved level:error"
)

# Veure detalls d'un error específic
sentry_get_sentry_resource(url="<SENTRY_URL>")

# Analitzar error amb Seer (opcional, si tens API key configurada)
sentry_analyze_issue_with_seer(issueUrl="<SENTRY_URL>")

# Actualitzar estat d'una issue
sentry_update_issue(
    organizationSlug="som-energia",
    regionUrl="<SENTRY_URL>",
    issueId="<ID>",
    status="resolved"
)
```

## Integració amb SDD

Aquesta skill s'utilitza a les fases:
- `sdd-explore`: Quan una incidència de Sentry arriba i cal investigar
- `sdd-propose`: Per documentar el repo i branca on es farà el fix
- `sdd-apply`: Per implementar el fix i crear PR

## Referències

- **Guia completa**: Veure [docs/guides/sentry-triage-workflow.md](../docs/guides/sentry-triage-workflow.md)
- **MCP Sentry**: Configuració a la guia (no versionar tokens reals)
