# 1. Estil i format del repositori openerp_som_addons

Data: 28-12-2022

## Estat

Proposat

## Context

Actualment no hi ha un estil definit pel codi del repositori. Això comporta que divergeixi molt en tot el repositori, inclús en un mateix fitxer. Complica la lectura del codi, hi ha molts `imports` i variables sense fer servir, etc.

## Decisió

El codi ha de complir els següents requisits:

- Passar `Flake8` (complir `PEP8`)
- XML i YAML sense errors
- Les línies no poden superar els 100 caràcters

### Decisió llargada línies

La llargada de mida que defineix PEP8 és de 79, que considerem massa poc. També vam considerar una llargada de 88 que és la que fa servir per defecte `black` (formatador de Python 3), però analitzant el codi del repositori també ens va resultar curt.

Llavors, després d'analitzar diferents llargades en fitxers del repositori i tenint en compte el principi "Explicit is better than implicit" de "Zen of Python", ens va semblar que el millor per la llegibilitat del codi del repositori seria de 120 caràcters.

Tot i això, finalment, per raons d'accessibilitat i facilitar els `diff` de `git` ens vam decantar per una llargada de línia de 100 caràcters.

### Decisió formatadors i comprovacions

Es fa servir `autoflake` per eliminar variables sense fer servir, per eliminar _imports_ sense fer servir, etc. Amb `autopep8` formatem el codi per complir `PEP8`. Amb `flake8` es fa la comprovació final de si el codi compleix els requisits.

S'ha descartat afegir `bugbear` per incompatibilitat amb Python 2. També s'ha descartat fer servir versions antigues de `black` que permeten formatar codi Python 2 des de Python 3 (les noves no ho permeten) per simplificar l'entorn.

### Comprovació a GitHub Actions

S'ha de passar una comprovació del format del codi per poder fer _merge_. Aquesta comprovació es faria amb el `pre-commit` adaptat per Python 2.7 (fitxer `.pre-commit-config.yaml` del repositori).

La comprovació la faria GitHub Actions com fa l'organització OCA ([Exemple](https://github.com/OCA/account-analytic/blob/14.0/.github/workflows/pre-commit.yml)). Si algun formatador modifica algun fitxer o alguna comprovació no es compleix, la comprovació amb GitHub Actions seria fallida.

S'apliquen les configuracions dels fitxers `.flake8` i `.pycodestyle` del repositori.

_Permetem 'star imports' als fitxers `__init__.py` per no haver d'importar un per un tots els testos._

### Desenvolupament

Pel que fa a formatar el codi al desenvolupar és una decisió pròpia de cada persona desenvolupadora. Dues formes en les quals es podria fer són les següents (o fer servir les dues alhora):

#### Integrat amb VSCode

1. Instal·lem l'extensió de Python
2. Instal·lem `autopep8` (1.5.7) i `flake8` (3.9.2) al `venv` de `erp`
3. Activem el `venv` de `erp` a VSCode (barra blava de baix a la dreta dins d'un fitxer Python)
4. A la configuració de VSCode `settings.json` definim el següent:

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

Al programar veurem els errors que ens marca `flake8` i al guardar se'ns formata automàticament el codi amb `autopep8`. Aquestes dues eines tindran en compte la configuració dels fitxers `.flake8` i `.pycodestyle` del repositori.

#### Amb l'eina `pre-commit

1. Instal·lem `pre-commit` al `venv` de `erp`: `pip install pre-commit`
2. Activem el `pre-commit` dins el repositori: `pre-commit install`

Al fer un _commit_ ens formatarà el codi automàticament amb `autoflake` i `autopep8`. També farà les comprovacions amb `flake8` i algunes altres pels XML i fitxer YAML.

- Si algun formatador fa algun canvi o no passen totes les comprovacions el _commit_ no es farà.
- Els fitxers modificats pel `pre-commit` queden _unstaged_.
- Fa el mateix que farà el GitHub Actions (definit al fitxer `.pre-commit-config.yaml`).

#### Amb l'eina `pre-commit manualment, sense força que es passi al fer cada commit
1.- Anem a la carpeta del repositori
2.- Executem `pre-commit run -a`

## Conseqüències

El codi del repositori quedaria més net, més llegible i més uniforme. S'ha de fer un format de tot el repositori abans de començar a aplicar-ho.
