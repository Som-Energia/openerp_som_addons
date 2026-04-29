---
name: git-commit
description: >
  Crea commits seguint les convencions de gitmoji.dev.
  Trigger: Quan necessites fer un commit de codi.
metadata:
  author: oriol
  version: "1.1"
---

## When to Use

Utilitza aquesta skill quan:
- Has fet canvis de codi que vols guardar
- Necessites fer un commit seguint Conventional Commits
- Vols afegir emoji al commit per fer-lo més llegible

## Format de Commit (segons gitmoji.dev)

Veure: https://gitmoji.dev/

El format és: `<emoji> <description>`

L'emoji indica el tipus de commit - no cal duplicar la informació amb el type.

### Emoji i Tipus

| Emoji | Tipus | Descripció |
|-------|-------|------------|
| ✨ | feat | Nova funcionalitat |
| 🐛 | fix | Bug fix |
| ♻️ | refactor | Refactorització |
| ⚡️ | perf | Millora de rendiment |
| ✅ | test | Afegir o corregir tests |
| 📖 | docs | Documentació |
| 💄 | style | Estil (formatting, no lògica) |
| 🔧 | chore | Tasques de manteniment |
| 📦 | build | Canvis al build o dependències |
| 👷 | ci | Canvis a CI/CD |
| ↩️ | revert | Revert de commit anterior |
| 🎨 | improve | Millora d'estructura/codi |
| 🔥 | remove | Eliminar codi o funcionalità |
| 🚚 | move | Moure o renombrar fitxers |
| 🚀 | deploy | Canvis de deployment |
| 💡 | int | Introduir nova idea sense canviar codi |

### Regles

1. **Idioma**: Tota la descripció en anglès
2. **Length màxima**: 72 caràcters
3. **Imperatiu**: Descripció en forma imperativa ("add feature" no "added feature")
4. **Emoji**: Obligatori, seguit d'un espai
5. **No cal type**: L'emoji ja indica el tipus - no escrius "feat:"

## Workflow

### Pas 0: Prerequisits (OBLIGATORI)

Abans de fer qualsevol commit, cal:

1. **Activar l'entorn virtual erp**:
   ```bash
   pyenv activate erp
   ```

2. **Executar pre-commit** per verificar que el codi passa el linting:
   ```bash
   pre-commit run
   ```
   Si hi ha errors, pre-commit els corregirà automàticament. Torna a executar fins que passi sense errors.

### Pas 1: Verificar canvis

```
git status
git diff
```

### Pas 2: Seleccionar fitxers

```bash
git add <fitxer>
# O per afegir tots:
git add -A
```

### Pas 3: Crear commit

```bash
git commit -m "<emoji> <description>"
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
git commit -m "📖 update API endpoint documentation"

# Millora de rendiment
git commit -m "⚡️ optimize database query performance"

# Estil
git commit -m "💄 format code with autopep8"

# Canvis de build
git commit -m "📦 update dependencies to latest versions"
```

## Errors Comuns

| Error | Causa | Solució |
|-------|-------|----------|
| Nothing to commit | Canvis no afegits | `git add -A` abans de commit |
| Commit message too long | Descripció massa llarga | Redueix a 72 caràcters |
| No emoji | Oblidat l'emoji | Afegeix l'emoji corresponent |

## Integració amb SDD

Aquesta skill s'utilitza a les fases:
- `sdd-apply`: Per guardar canvis implementats
- `sdd-verify`: Per guardar correccions
