# Manteniment del codi a testing
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
