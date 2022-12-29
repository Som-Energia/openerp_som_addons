# 1. Estil i format del repositori openerp_som_addons

Data: 28-12-2022

## Estat

Proposat

## Context

Actualment no hi ha un estil definit pel codi del repositori. Això comporta que divergeixi molt en tot el repositori, inclús en un mateix fitxer. Complica la lectura del codi, hi ha molts `imports` i variables sense fer servir, etc.

## Decisió

El codi ha de complir els següents requisits:

- Passar `Flake8`
- Complir `PEP8`
- XML i YAML sense errors
- Les línies no poden superar els 88 caràcters


S'ha de passar una comprovació del format del codi per poder fer _merge_. Aquesta comprovació es faria amb el següent `pre-commit` adaptat per Python 2.7. La comprovació la faria GitHub Actions com fa l'organització OCA ([Exemple](https://github.com/OCA/account-analytic/blob/14.0/.github/workflows/pre-commit.yml)):

```
default_language_version:
  python: python2.7
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v2.4.0
    hooks:
      - id: trailing-whitespace
      - id: check-yaml
      - id: check-xml
  - repo: https://github.com/myint/autoflake
    rev: v1.4
    hooks:
      - id: autoflake
        args:
          - --expand-star-imports
          - --ignore-init-module-imports
          - --in-place
          - --remove-all-unused-imports
          - --remove-duplicate-keys
          - --remove-unused-variables
  - repo: https://github.com/pre-commit/mirrors-autopep8
    rev: v1.5.7
    hooks:
      - id: autopep8
  - repo: https://github.com/PyCQA/flake8
    rev: 3.9.2
    hooks:
      - id: flake8
        name: flake8

```

S'apliquen les següents configuracions (fitxer `setup.cfg` dins del repositori):


```
[pycodestyle]
max-line-length = 88

[flake8]
max-line-length = 88
max-complexity = 18

select = B,C,E,F,W
ignore = W503
per-file-ignores=
    __init__.py:F401
```

La llargada de mida que defineix PEP8 és de 79, que considerem massa poc. S'ha decidit fer servir una llargada de 88 que és la que fa servir per defecte `black` (descartat per incompatibilitat amb Python 2).

Pel que fa a formatar el codi al desenvolupar és una decisió pròpia de cada persona desenvolupadora. Dues formes en les quals es podria fer són les següents:

### Integrat amb VSCode

- Instal·lem extensió de Python
- Instal·lem `autopep8` i `flake8` al `venv` de `erp`
- Activem el `venv` de `erp` a VSCode (barra blava de baix a la dreta dins d'un fitxer Python)
- A la configuració `settings.json` definim el següent:

```
{
    "[python]": {
        "editor.defaultFormatter": "ms-python.python",
        "editor.formatOnSave": true,
    },
    "python.formatting.provider": "autopep8",
    "python.linting.enabled": true,
    "python.linting.flake8Enabled": true,
    "python.linting.flake8CategorySeverity.W": "Error",
    "python.terminal.activateEnvInCurrentTerminal": true,
    "python.terminal.activateEnvironment": true,
}
```

Al programar veurem els errors que ens marca `flake8` i al guardar se'ns formata automàticament el codi amb `autopep8`. Aquestes dues eines tindran en compte la configuració del fitxer `setup.cfg` del repositori.

### Amb l'eina `pre-commit`

- Instal·lem `pre-commit` al `venv` de `erp`: `pip install pre-commit`
- Activem el `pre-commit` dins el repositori: `pre-commit install`

Al fer un _commit_ passarà les mateixes comprovacions que el GitHub Actions (les del fitxer `.pre-commit-config.yaml`). Si alguna comprovació no es compleix no es fa el _commit_. A més, ens formatarà el codi automàticament (tampoc fa el _commit_ i si modifica fitxers no queden _staged_)

## Conseqüències

El codi del repositori quedaria més net, més llegible i més uniforme. S'ha de fer un format de tot el repositori abans de començar a aplicar-ho.