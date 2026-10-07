---
name: erp-apply-pr-divergent
description: >
  Aplica una Pull Request sobre una branca ERP divergent quan el merge directe
  genera conflictes massius per una base històrica diferent. Analitza la base
  real de la PR, aplica els commits en ordre, resol els conflictes reals i
  valida l'arbre resultant.
  Trigger: Quan cal aplicar una PR de gisce/erp sobre una branca rolling o una
  altra branca que no comparteix la mateixa base recent.
metadata:
  author: som-energia
  version: "1.0"
---

## Quan utilitzar-la

Utilitza aquesta skill quan:

- Una PR s'ha d'incorporar a una branca rolling o de desplegament.
- El merge directe de la branca de la PR produeix centenars de conflictes.
- La PR està basada en una branca diferent de la branca objectiu.
- El resultat s'ha de deixar en una branca nova sense modificar la branca base.

No utilitzis aquesta skill per a un merge normal on la PR i la branca objectiu
comparteixen una base recent.

## Principi de resolució

No resolguis un conflicte massiu escollint globalment `ours` o `theirs`.
Això pot perdre canvis de la branca objectiu o incorporar canvis aliens a la
PR. El procediment correcte és aplicar el conjunt de commits que formen la PR
sobre la branca objectiu, resolent només les col·lisions reals.

Quan el conflicte sigui en imports, registres de tests o fitxers d'índex, mantén
els elements de la branca objectiu i afegeix els nous elements de la PR. Per a
codi funcional, revisa ambdues versions i conserva el comportament existent de
la branca objectiu, incorporant explícitament el canvi de la PR.

## Precondicions

1. Identifica el repositori actiu:

   ```bash
   git rev-parse --show-toplevel
   git status --short --branch
   git remote -v
   ```

2. Revisa els `AGENTS.md` del workspace i del repositori abans d'editar.
3. No descartis ni incloguis canvis locals no relacionats. Especialment, no
   eliminis fitxers no seguits com `.codegraph/`.
4. Confirma l'abast: repositori, branca objectiu, nom de la branca resultant i
   número o URL de la PR.
5. No facis `push` sense una petició explícita.

## Procediment

### 1. Descarregar la PR i identificar la base real

Descarrega el cap de la PR:

```bash
git fetch origin \
  refs/pull/<PR>/head:refs/remotes/origin/pr-<PR>
```

Si GitHub ho ofereix, descarrega també el merge ref:

```bash
git fetch origin \
  refs/pull/<PR>/merge:refs/remotes/origin/pr-<PR>-merge
```

El merge ref permet identificar la base que GitHub utilitza:

```bash
git rev-list --parents -n 1 origin/pr-<PR>-merge
git show -s --format=fuller origin/pr-<PR>-merge
```

El primer pare és la base de la PR i el segon pare és el cap de la PR.
Comprova si la base és ancestre de la branca objectiu:

```bash
git merge-base --is-ancestor <pr-base> <target>
echo $?
```

Un resultat `1` indica que el merge directe pot generar conflictes històrics
massius i cal seguir aquesta skill.

### 2. Crear la branca resultant

Parteix exactament de la branca objectiu actualitzada:

```bash
git switch <target>
git pull --ff-only <remote> <target>  # només si correspon i està acordat
git switch -c <result-branch>
```

Abans de crear-la, verifica que la branca resultant no existeix o confirma com
s'ha de tractar si ja existeix.

### 3. Inspeccionar els commits de la PR

Comprova l'abast real respecte de la base de la PR:

```bash
git log --reverse --oneline <pr-base>..origin/pr-<PR>
git diff --stat <pr-base>...origin/pr-<PR>
```

Per a una PR lineal, aplica els commits en ordre cronològic:

```bash
git log --reverse --format='%H %s' <pr-base>..origin/pr-<PR>
```

No assumeixis que la diferència directa entre `<target>` i el cap de la PR és
l'abast de la PR: inclourà tota la divergència entre les dues branques.

Si la PR conté merge commits o una història no lineal, atura't i analitza'ls
abans de fer cherry-pick automàtic. No facis `cherry-pick` d'un merge commit
sense determinar quin pare conté el canvi funcional.

### 4. Aplicar els commits i resoldre conflictes

Aplica cada commit individualment, en ordre:

```bash
git cherry-pick <commit-1>
git cherry-pick <commit-2>
# ...
```

Si hi ha conflicte:

```bash
git status
git diff --cc -- <fitxer>
git show <commit>^:<fitxer>
git show <commit>:<fitxer>
git show <target>:<fitxer>
```

Resol el fitxer, elimina tots els marcadors (`<<<<<<<`, `=======`, `>>>>>>>`),
revisa el diff i continua:

```bash
git add <fitxer>
git cherry-pick --continue
```

Si el canvi ja existeix a la branca objectiu, verifica que sigui realment
redundant abans d'utilitzar `git cherry-pick --skip`.

En cas d'error o d'una resolució incorrecta, torna a l'estat anterior sense
perdre canvis locals:

```bash
git cherry-pick --abort
```

### 5. Validació obligatòria

Quan tots els commits s'hagin aplicat:

```bash
git status --short --branch
git diff --check <target>..<result-branch>
git diff --name-only --diff-filter=U
```

La llista de fitxers sense resoldre ha d'estar buida i `git diff --check` no ha
de retornar errors. Cerca marcadors de conflicte al contingut versionat:

```bash
git grep -n -E '^(<<<<<<<|=======|>>>>>>>)' <result-branch> -- ':!*.lock'
```

Revisa també els tests afectats i executa la skill de testing corresponent si
l'entorn ho permet. Com a mínim, documenta si els tests no s'han executat.

## Resultat i informe

L'informe final ha d'indicar:

- branca resultant i commit final;
- commits de la PR aplicats;
- conflictes resolts i criteri utilitzat;
- resultat de `git diff --check` i dels tests;
- fitxers locals no relacionats que s'han preservat;
- que no s'ha fet `push`, si no s'ha demanat explícitament.

## Errors freqüents

| Error | Causa | Solució |
|---|---|---|
| Centenars de conflictes en un merge directe | La PR i la branca objectiu tenen bases diferents | Aplicar els commits de la PR en ordre |
| `git diff target..PR` mostra milers de fitxers | Compara també tota la divergència històrica | Comparar `pr-base...PR` per conèixer l'abast real |
| Es perden imports o tests locals | S'ha triat globalment `theirs` | Fer una unió explícita durant la resolució |
| El merge queda a mig resoldre | S'ha interromput un cherry-pick | `git status`, resoldre, `git add` i `git cherry-pick --continue` |
