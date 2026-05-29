---
name: git-branch
description: >
  Crea branques de git seguint convencions de naming: IMP_, FIX_, MOD_, ADD_, etc.
  Trigger: Quan necessites crear una branca nova per treballar.
metadata:
  author: oriol
  version: "1.0"
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
3. **Espais**: Utilitzar guions (-) dins la descripció si cal
4. **Longitud**: Màxim 50 caràcters

## Workflow

### Pas 1: Actualitzar main/master

```bash
git fetch origin
git pull origin main
```

### Pas 2: Crear branca nova

```bash
git checkout -b <type>_<description>
```

### Pas 3: Fer canvis i commit

(Utilitza la skill `git-commit`)

### Pas 4: Fer push

```bash
git push -u origin <branch_name>
```

## Exemples

```bash
# Nova funcionalitat
git checkout -b ADD_user_registration

# Millora
git checkout -b IMP_payment_validation

# Bug fix
git checkout -b FIX_invoice_total_calculation

# Canvi de comportament
git checkout -b MOD_renewal_process

# Refactor
git checkout -b REF_extract_partner_service

# Tests
git checkout -b TEST_contract_validation

# Documentació
git checkout -b DOCS_api_reference
```

## Errors Comuns

| Error | Causa | Solució |
|-------|-------|----------|
| Branch already exists | Branca ja existent | Canvia el nom o elimina la branca existent |
| Invalid branch name | Caràcters invàlids | Utilitza només lletres, números, guions i guions baixos |
| Not on main | No estàs a main | `git checkout main` abans de crear branca |

## Integració amb SDD

Aquesta skill s'utilitza a les fases:
- `sdd-propose`: Per crear branca des del proposal
- `sdd-apply`: Per crear branca de treball
