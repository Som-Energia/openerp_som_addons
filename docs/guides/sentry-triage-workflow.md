# Sentry Triage Workflow

Guia curta per triar i documentar incidències de Sentry relacionades amb els repositoris ERP de Som Energia.

## Objectiu

Evitar dubtes quan una incidència es detecta a producció però el fix s'ha de preparar en un altre repositori o branca.

## Regles bàsiques

1. El Sentry consultat és el de producció.
2. Moltes incidències vindran d'entorns basats en `Som-Energia/erp:rolling_erp01`.
3. Els fixes i PRs s'han de preparar a `gisce/erp:developer` quan el codi afectat viu a `erp/`.
4. El repositori de la issue depén del mòdul on peta l'error:
   - si el stack apunta a `/home/erp/src/erp/...` o a mòduls del repo `erp/`, la issue va a `gisce/erp`
   - si el stack apunta a mòduls d'aquest repo `openerp_som_addons/`, la issue ha d'anar al repo corresponent d'addons

## Quan crear una issue a partir de Sentry

1. Prioritzar errors reals abans que `slow request`, si l'objectiu és arreglar bugs.
2. Triar una incidència amb stack clar i codi de primer nivell.
3. Evitar copiar dades personals o valors operatius sensibles des de Sentry.
4. Incloure sempre el link directe de Sentry dins de la issue.

Dades que no s'han de publicar MAI en issues, comentaris o PRs:

- noms i cognoms
- adreces postals o poblacions
- emails
- telèfons
- CUPS
- qualsevol altre identificador personal o dada operativa sensible

Si un cas real és útil per explicar el bug, cal anonimitzar-lo o generalitzar-lo abans de publicar-lo.

## Convencions per a la issue

1. Afegir labels `bug` i `autotask`.
2. Descriure el comportament antic i el comportament esperat.
3. Explicar la causa tècnica amb referències a fitxers i línies si són conegudes.
4. Indicar explícitament si l'error es veu a producció però el fix s'ha de fer en una altra branca o repo.

## Convencions per a la PR

1. Seguir la plantilla descrita a `AGENTS.md` i la documentació de PR del repositori objectiu.
2. En el cas de `gisce/erp`, la descripció ha d'estar en castellà i seguir la plantilla del repo.
3. La PR ha d'eixir des de la branca de desenvolupament correcta, no des de `rolling_erp01`.

## MCP de Sentry

Per a entorns self-hosted, el MCP de Sentry es configura en mode local/STDIO.

Exemple de configuració per a OpenCode:

```json
{
  "$schema": "https://opencode.ai/config.json",
  "mcp": {
    "sentry": {
      "type": "local",
      "command": ["npx", "@sentry/mcp-server@0.2.0"],
      "environment": {
        "SENTRY_HOST": "<SENTRY_HOST>",
        "SENTRY_ACCESS_TOKEN": "<TOKEN>",
        "MCP_DISABLE_SKILLS": "seer"
      }
    }
  }
}
```

Notes:

1. `SENTRY_HOST` ha de ser el host del servidor Sentry, sense `https://`.
2. No guardar el token real en documentació ni en fitxers versionats.
3. Si es volen eines de cerca en llenguatge natural, cal configurar també el proveïdor LLM corresponent.

## Checklist ràpid

- error triat i no només problema de rendiment
- repo correcte identificat segons el mòdul del stack
- issue amb link directe a Sentry
- sense dades personals ni secrets
- labels `bug` i `autotask`
- PR oberta contra la branca de desenvolupament correcta
