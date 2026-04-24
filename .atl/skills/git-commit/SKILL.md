---
name: git-commit
description: >
  Crea commits seguint conventional commits amb emoji.dev.
  Trigger: Quan necessites fer un commit de codi.
metadata:
  author: oriol
  version: "1.0"
---

## When to Use

Utilitza aquesta skill quan:
- Has fet canvis de codi que vols guardar
- Necessites fer un commit seguint Conventional Commits
- Vols afegir emoji al commit per fer-lo més llegible

## Format de Commit

El format és: `<emoji> <type>: <description>`

### Tipus de Commit

| Type | Emoji | Descripció |
|------|-------|------------|
| feat | ✨ | Nova funcionalitat |
| fix | 🐛 | Bug fix |
| refactor | ♻️ | Refactorització |
| perf | ⚡ | Millora de rendiment |
| test | ✅ | Afegir o corregir tests |
| docs | 📖 | Documentació |
| style | 💄 | Estil (formatting, no lògica) |
| chore | 🔧 | Tasques de manteniment |
| build | 📦 | Canvis al build o dependències |
| ci | 👷 | Canvis a CI/CD |
| revert | ↩️ | Revert de commit anterior |

### Regles

1. **Idioma**: Tota la descripció en anglès
2. **Length màxima**: 72 caràcters
3. **Case**: lowercase per al type
4. **Imperatiu**: Descripció en forma imperativa ("add feature" no "added feature")
5. **Emoji**: Obligatori, seguit d'un espai

## Workflow

### Pas 1: Verificar canvis

```bash
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
git commit -m "<emoji> <type>: <description>"
```

## Exemples

```bash
# Nova funcionalitat
git commit -m "✨ feat: add user authentication flow"

# Bug fix
git commit -m "🐛 fix: resolve null pointer in invoice calculation"

# Refactor
git commit -m "♻️ refactor: extract payment logic to service"

# Tests
git commit -m "✅ test: add unit tests for contract validation"

# Documentació
git commit -m "📖 docs: update API endpoint documentation"
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
