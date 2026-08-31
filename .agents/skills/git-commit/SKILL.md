---
name: git-commit
description: >
  Crea commits seguint les convencions de gitmoji del projecte.
  Trigger: Quan necessites fer un commit de codi.
metadata:
  author: oriol
  version: "1.3"
---

## When to Use

Utilitza aquesta skill quan:
- Has fet canvis que vols guardar en un commit
- Necessites seguir la convenció de commits del projecte
- Vols preparar només els fitxers de l'abast acordat

## Format de Commit

[gitmoji.dev](https://gitmoji.dev/) és la font canònica del significat dels
emojis. [`.github/docs/desenvolupament.md`](../../../.github/docs/desenvolupament.md)
recull la selecció habitual i les regles de format pròpies del projecte.

El format és: `<emoji> <description>`

L'emoji indica el tipus de commit; no cal duplicar la informació amb un type
textual com `feat:` o `fix:`.

### Selecció habitual

| Emoji | Significat oficial |
|-------|---------------------|
| ✨ | Introduir funcionalitat nova |
| 🐛 | Corregir un bug |
| 🩹 | Fer una correcció senzilla i no crítica |
| 👔 | Afegir o actualitzar lògica de negoci |
| 🗃️ | Fer canvis relacionats amb la base de dades |
| 🏗️ | Fer canvis arquitectònics |
| 🔧 | Afegir o actualitzar fitxers de configuració |
| 👷 | Afegir o actualitzar el sistema de CI |
| 📝 | Afegir o actualitzar documentació |
| ⚡️ | Millorar el rendiment |
| ♻️ | Refactoritzar codi |
| 🎨 | Millorar l'estructura o el format del codi |
| 🔥 | Eliminar codi o fitxers |
| ⚰️ | Eliminar codi mort |
| 🦺 | Afegir o actualitzar validacions |
| ✅ | Afegir, actualitzar o fer passar tests |
| 🚧 | Marcar treball en curs |
| ⬆️ | Actualitzar dependències a versions superiors |
| 🌐 | Internacionalització i localització |
| 💄 | Afegir o actualitzar la interfície i els fitxers d'estil |
| 🔨 | Afegir o actualitzar scripts de desenvolupament, incloses migracions |

Per a qualsevol emoji no llistat, consultar [gitmoji.dev](https://gitmoji.dev/)
en lloc d'inventar o redefinir-ne el significat.

### Regles

1. **Idioma**: Tota la descripció en anglès
2. **Longitud màxima**: 72 caràcters
3. **Imperatiu**: Descripció en forma imperativa (`add feature`, no `added feature`)
4. **Emoji**: Obligatori, seguit d'un espai
5. **Sense type textual**: No escriure `feat:`, `fix:` ni equivalents

## Workflow

### Pas 1: Verificar els canvis

```bash
git status --short
git diff
```

Identificar els fitxers de l'abast acordat. No descartar ni incloure canvis
aliens, i no utilitzar `git add -A`.

### Pas 2: Preparar fitxers explícits

```bash
git add <fitxer> [<fitxer> ...]
git diff --cached --check
git diff --cached
```

### Pas 3: Executar pre-commit

Activar l'entorn virtual habitual del projecte i executar pre-commit sobre els
fitxers preparats:

```bash
pyenv activate erp
pre-commit run
```

Si algun hook modifica fitxers, revisar els canvis, tornar a preparar només els
fitxers corresponents i repetir `pre-commit run` fins que passi.

### Pas 4: Crear el commit

```bash
git commit -m "<emoji> <description>"
```

### Pas 5: Verificar el resultat

```bash
git status --short
git show --stat --oneline HEAD
```

## Exemples

```bash
# Nova funcionalitat
git commit -m "✨ add user authentication flow"

# Bug fix
git commit -m "🐛 resolve null pointer in invoice calculation"

# Refactor
git commit -m "♻️ extract payment logic to service"

# Tests
git commit -m "✅ add unit tests for contract validation"

# Documentació
git commit -m "📝 update API endpoint documentation"

# Millora de rendiment
git commit -m "⚡️ optimize database query performance"

# Estil de codi
git commit -m "🎨 format code with autopep8"

# Actualització de dependències
git commit -m "⬆️ upgrade build dependencies"

# Script de migració
git commit -m "🔨 migrate contract status values"
```

## Errors Comuns

| Error | Causa | Solució |
|-------|-------|----------|
| Nothing to commit | No hi ha fitxers preparats | Revisa `git status` i prepara fitxers explícits amb `git add <fitxer>` |
| Hooks pass without checking files | Pre-commit s'ha executat abans de preparar fitxers | Prepara els fitxers i torna a executar `pre-commit run` |
| Unrelated files staged | S'han preparat canvis fora de l'abast | Retira'ls de l'staging sense descartar-los i revisa `git diff --cached` |
| Commit message too long | Descripció massa llarga | Redueix-la a un màxim de 72 caràcters |
| No emoji | Falta l'emoji inicial | Utilitza un emoji de la taula canònica |

## Integració amb SDD

Aquesta skill s'utilitza a les fases:
- `sdd-apply`: Per guardar canvis implementats
- `sdd-verify`: Per guardar correccions
