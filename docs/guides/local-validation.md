# Validació local

## Serveis compartits

Des de qualsevol checkout o worktree d'addons:

```bash
scripts/start-local-services.sh
```

El helper resol el checkout principal amb Git i usa el seu
`docker-compose.yaml`, directori de projecte i nom de projecte. Ignora els
valors heretats de `COMPOSE_FILE` i `COMPOSE_PROJECT_NAME`; així un worktree no
crea una segona pila sobre els mateixos ports. Reutilitza els contenidors i el
volum PostgreSQL existents: no elimina contenidors ni volums.

Després d'arrencar els tres serveis, espera `pg_isready`, el ping de MongoDB i
el ping de Redis dins dels contenidors. El límit d'espera conjunt és de 120
segons; es pot canviar amb `OPENERP_LOCAL_SERVICES_TIMEOUT`. Un error d'arrencada
o un timeout retorna un codi no zero abans d'iniciar els tests.

Si una pila antiga d'un worktree ocupa els ports, identifica'n primer el
propietari. El helper no atura serveis aliens ni elimina volums per alliberar-los.

## Preparar les eines locals

Amb el virtualenv ERP Python 2.7 activat i el workspace base ja instal·lat:

```bash
PYENV_VERSION=erp scripts/setup-local-validation.sh
```

El setup es pot repetir: instal·la les versions de
`requirements-local-validation.txt`, registra `somenergia-generationkwh` en
editable sense actualitzar-ne les dependències, comprova els imports i instal·la
els hooks Git amb els seus entorns. Els hooks són compartits pels worktrees del
mateix repositori. No clona repositoris, no sincronitza branques i no modifica el
Python del sistema. Les versions dels hooks continuen a `.pre-commit-config.yaml`.
El workflow de pre-commit usa el mateix fitxer de versions d'eines.

Si falta una dependència base de l'ERP, el setup falla i la identifica; cal
preparar l'entorn ERP abans de repetir-lo. No executis el bootstrap de CI damunt
d'un workspace existent: està pensat per clonar un entorn nou.

Per comprovar l'entorn sense instal·lar res:

```bash
PYENV_VERSION=erp python scripts/check_local_env.py
```

La comprovació mostra l'intèrpret i els camins dels imports de les eines,
Destral i `generationkwh.investmentmodel`. `run-tests.sh` l'executa abans de
preparar la base de dades o instal·lar addons; qualsevol error retorna un codi
no zero. El wrapper de worktrees continua mantenint el lock i restaurant els
enllaços encara que aquesta comprovació falli.

El setup fixa la cadena d'eines de Python 2.7. Per a proves locals amb Python 3,
cal proveir eines compatibles al seu virtualenv: el checker comprova els imports
però no força les versions de Python 2. `--tools-only` omet els imports ERP i
permet comprovar les eines sense workspace.

Si un entorn de hooks de la cache està corrupte (per exemple, hi falta
`typing`), `pre-commit clean` permet regenerar-lo després de revisar l'error.
No s'eliminen caches ni s'instal·len paquets automàticament durant els tests.

## Tests dels scripts

Els tests de `scripts/tests/*-test.sh` usen fixtures temporals i dobles de les
comandes externes. No necessiten l'ERP, Docker ni credencials. Els tests
Destral continuen passant obligatòriament per `scripts/run-tests-worktree.sh`
quan es treballa des d'un worktree; vegeu la skill
[erp-test](../../.agents/skills/erp-test/SKILL.md).
