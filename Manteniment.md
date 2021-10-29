# Manteniment del codi a testing
Al servidor de testing treballem sobre la branca Rolling. Per aplicar una PR, cal fer:
*  git pull origin
*  git checkout NOM_BRANCA
*  git rebase rolling

Si no hi ha conflictes, ja està.

Si hi ha conflictes, arreglar-los i fer commit.
