# Manteniment del codi a testing
Al servidor de testing treballem sobre la branca Rolling. Per aplicar una PR, cal fer:
*  git pull origin
*  git checkout NOM_BRANCA
*  git pull
*  git checkout rolling
*  git merge NOM_BRANCA

Si hi ha conflictes, cal arreglar els conflictes

*  git status
*  vim fitxers_amb_conflictes
*  git add
*  git commit

Si no hi ha conflictes, ja està.
