# Manteniment del codi a testing, serp...
## Mètode 1
Millor fer servir el sastre, ja que podem amb el mètode 2 podem aplicar coses que no volem aplicar, però que venen amb la branca (ex. bateria virtual)
`sastre deploy --host somdevel@serp01.somenergia.lan:port --pr 472 --owner Som-Energia --repository openerp_som_addons --environ test`


## Mètode 2
Al servidor de testing treballem sobre la branca Rolling. Per aplicar una PR, cal fer:
*  git pull
*  git merge origin/NOM_BRANCA

Si has fet merge de la branca **prèviament**, pots fer:
*  git pull origin NOM_BRANCA

Si hi ha conflictes, cal arreglar els conflictes

*  git status
*  vim fitxers_amb_conflictes
*  git add
*  git commit

Si no hi ha conflictes, ja està.
