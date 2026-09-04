---
name: git-pr
description: >
  Crea Pull Requests seguint la plantilla de Som Energia.
  Trigger: Quan necessites crear una Pull Request.
metadata:
  author: oriol
  version: "1.2"
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

### Pas 1: Verificar estat i abast

```bash
git status --short
git diff --check
git log main..HEAD --oneline
git diff --stat main...HEAD
```

Comprovar que tots els commits i fitxers pertanyen a l'abast acordat. No
incloure canvis locals o fitxers no relacionats.

### Pas 2: Executar comprovacions

Revisar `AGENTS.md` i executar els tests i el linting obligatoris que apliquin.
Per codi OpenERP, utilitzar la skill `erp-test` i executar `flake8 .`. Si una
comprovació no aplica, indicar-ho explícitament a la descripció de la PR; no
marcar com a passada una comprovació que no s'ha executat.

### Pas 3: Seleccionar l'etiqueta

```bash
gh label list
```

Escollir com a mínim una etiqueta existent segons els fitxers modificats. Si
no és evident quina correspon, preguntar-ho abans de crear la PR.

### Pas 4: Fer push de la branca

```bash
git push -u origin <branch_name>
```

### Pas 5: Crear PR

```bash
gh pr create \
  --base main \
  --assignee "@me" \
  --label "<label>" \
  --title "<title descriptiu>" \
  --body "$(cat <<'EOF'
## Objectiu

<descripció de l'objectiu>

## Targeta on es demana o Incidència

<enllaç a la targeta/incidència o "No aplica">

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
gh pr create \
  --base main \
  --assignee "@me" \
  --label "<label>" \
  --title "<title descriptiu>" \
  --body-file /path/to/pr_template.md
```

## Exemples

```bash
# PR simple
gh pr create \
  --base main \
  --assignee "@me" \
  --label "feature" \
  --title "Add user registration" \
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
4. **Títols**: Clar i descriptiu; no reutilitzar automàticament el nom de la branca
5. **Assignació**: Autoassignar la PR amb `--assignee "@me"`
6. **Branca base**: Indicar explícitament `--base main`
7. **Etiqueta**: Afegir com a mínim una etiqueta existent amb `--label`
8. **Comprovacions**: Executar les obligatòries abans de crear la PR i documentar les que no apliquin

## Errors Comuns

| Error | Causa | Solució |
|-------|-------|----------|
| No branch to push | Branca no existent | Crea la branca primer amb `git-branch` |
| PR title too long | Títol massa llarg | Redueix a menys de 72 caràcters |
| No description | Descripció buida | Omple la plantilla completa |
| Label not found | L'etiqueta no existeix | Consulta `gh label list` i selecciona'n una d'existent |
| Checks failing | Tests o linting fallen | Atura la creació de la PR i corregeix els errors |

## Integració amb SDD

Aquesta skill s'utilitza a les fases:
- `sdd-apply`: Per crear PR dels canvis implementats
- `sdd-archive`: Per crear PR en tancar un canvi
