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

## Tests dels scripts

Els tests de `scripts/tests/*-test.sh` usen fixtures temporals i dobles de les
comandes externes. No necessiten l'ERP, Docker ni credencials. Els tests
Destral continuen passant obligatòriament per `scripts/run-tests-worktree.sh`
quan es treballa des d'un worktree; vegeu la skill
[erp-test](../../.agents/skills/erp-test/SKILL.md).
