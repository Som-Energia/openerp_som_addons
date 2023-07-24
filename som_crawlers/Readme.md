# Massive Importer - mòdul som_crawlers
Mòdul compatible amb PowerERP per descarregar fitxers de distribuidores elèctriques del sistema ibèric

## Models
### Tasca planificada: som.crawlers.task
Té hores i dies d’execució i un seguit de passes que s’han d’executar.

### Pas d’acció planificada: som.crawlers.task.step
Pas d'una tasca planificada

### Acció executada: som.crawlers.task.result
Conté el resultat de l’execució de a tasca determinada en una hora determinada.

### Configuració: som.crawlers.config
Conté la configuració d'una tasca
