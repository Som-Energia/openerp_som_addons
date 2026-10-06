---
name: git-branch
description: >
  Crea branques de git seguint convencions de naming: IMP_, FIX_, MOD_, ADD_, etc.
  Trigger: Quan necessites crear una branca nova per treballar.
metadata:
  author: oriol
  version: "1.2"
---

## When to Use

Utilitza aquesta skill quan:
- Començar a treballar en una nova feature
- Corregir un bug
- Fer qualsevol canvi que requerixi una branca separada

## Convencions de Naming

El format és: `<type>_<description>`

### Tipus de Branca

| Prefix | Tipus | Descripció |
|--------|-------|------------|
| IMP_ | Improvement | Millora d funcionalitat existent |
| FIX_ | Bug Fix | Correcció de bug |
| MOD_ | Modification | Canvi de comportament |
| ADD_ | Addition | Afegir nova funcionalitat |
| REF_ | Refactor | Refactorització sense canvi funcional |
| TEST_ | Test | Afegir o corregir tests |
| DOCS_ | Documentation | Canvis de documentació |
| CI_ | CI/CD | Canvis a pipelines |

### Regles

1. **Descripció**: 2-3 paraules en anglès, lowercase
2. **Separador**: Guió baix (_) entre tipus i descripció
3. **Separador de paraules**: Utilitzar guions baixos (_) dins la descripció si cal
4. **Longitud**: Màxim 50 caràcters

## Workflow

### Pas 1: Verificar l'estat local

```bash
git status --short
```

Abans de canviar de branca, identificar qualsevol canvi local. No descartar-lo,
fer `stash` ni incloure'l a la branca nova sense confirmar-ne l'abast.

### Pas 2: Actualitzar `main`

```bash
git fetch origin
git switch main
git pull --ff-only origin main
```

`--ff-only` evita crear un merge accidental durant l'actualització.

### Pas 3: Crear branca nova

```bash
git switch -c <type>_<description>
```

### Pas 4: Fer canvis i commit

(Utilitza la skill `git-commit`)

### Pas 5: Fer push

```bash
git push -u origin <branch_name>
```

## Exemples

```bash
# Nova funcionalitat
git switch -c ADD_user_registration

# Millora
git switch -c IMP_payment_validation

# Bug fix
git switch -c FIX_invoice_total_calculation

# Canvi de comportament
git switch -c MOD_renewal_process

# Refactor
git switch -c REF_extract_partner_service

# Tests
git switch -c TEST_contract_validation

# Documentació
git switch -c DOCS_api_reference
```

## Errors Comuns

| Error | Causa | Solució |
|-------|-------|----------|
| Branch already exists | Branca ja existent | Canvia el nom o elimina la branca existent |
| Invalid branch name | Caràcters invàlids | Utilitza només lletres, números, guions i guions baixos |
| Not on main | No estàs a main | `git switch main` abans de crear branca |
| Not possible to fast-forward | La branca local ha divergit de `origin/main` | Atura't i revisa l'historial; no forcis el pull |

## Integració amb SDD

Aquesta skill s'utilitza a les fases:
- `sdd-propose`: Per crear branca des del proposal
- `sdd-apply`: Per crear branca de treball
