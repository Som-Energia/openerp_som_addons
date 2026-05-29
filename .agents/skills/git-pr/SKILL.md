---
name: git-pr
description: >
  Crea Pull Requests seguint la plantilla de Som Energia.
  Trigger: Quan necessites crear una Pull Request.
metadata:
  author: oriol
  version: "1.0"
---

## When to Use

Utilitza aquesta skill quan:
- Has acabat de treballar en una branca i vols crear una PR
- Necessites seguir la plantilla de PR de Som Energia

## Plantilla de PR

```markdown
## Objectiu


## Targeta on es demana o Incidència


## Comportament antic


## Comportament nou


## Comprovacions

- [ ] Hi ha testos
- [ ] Reiniciar serveis
- [ ] Actualitzar mòdul
- [ ] Script de migració
- [ ] Modifica traduccions
```

## Workflow

### Pas 1: Verificar estat

```bash
git status
git log main..HEAD --oneline
```

### Pas 2: Fer push de la branca

```bash
git push -u origin <branch_name>
```

### Pas 3: Crear PR

```bash
gh pr create --title "<title>" --body "$(cat <<'EOF'
## Objectiu

<descripció de l'objectiu>

## Targeta on es demana o Incidència

<enllaç a la targeta/jira>

## Comportament antic

<com es comportava abans>

## Comportament nou

<com es comporta ara>

## Comprovacions

- [ ] Hi ha testos
- [ ] Reiniciar serveis
- [ ] Actualitzar mòdul
- [ ] Script de migració
- [ ] Modifica traduccions
EOF
)"
```

O alternativament:
```bash
gh pr create --title "<title>" --body-file /path/to/pr_template.md
```

## Exemples

```bash
# PR simple
gh pr create \
  --title "ADD_user_registration" \
  --body "$(cat <<'EOF'
## Objectiu

Afegir formulari de registre d'usuaris amb validació de email.

## Targeta on es demana o Incidència

https://trello.com/c/abc123

## Comportament antic

No existia cap formulari de registre.

## Comportament nou

Nou formulari de registre accessible des de /register que valida email i contrasenya.

## Comprovacions

- [x] Hi ha testos
- [ ] Reiniciar serveis
- [x] Actualitzar mòdul
- [ ] Script de migració
- [x] Modifica traduccions
EOF
)"
```

## Regles

1. **Idioma**: Català per a la descripció
2. **Totes les seccions**: Omple-les totes, no deixis espais buits
3. **Comprovacions**: Marca les que apliquen amb [x]
4. **Títols**: Clar i descriptiu

## Errors Comuns

| Error | Causa | Solució |
|-------|-------|----------|
| No branch to push | Branca no existent | Crea la branca primer amb `git-branch` |
| PR title too long | Títol massa llarg | Redueix a menys de 72 caràcters |
| No description | Descripció buida | Omple la plantilla completa |

## Integració amb SDD

Aquesta skill s'utilitza a les fases:
- `sdd-apply`: Per crear PR dels canvis implementats
- `sdd-archive`: Per crear PR en tancar un canvi
