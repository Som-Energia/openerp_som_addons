# Manteniment del codi a testing
Al servidor de testing treballem sobre la branca Rolling. Per aplicar una PR, cal fer:
*  git checkout main
*  git pull origin
*  git branch -D NOM_BRANCA
*  git checkout NOM_BRANCA
*  git rebase rolling

Si no hi ha conflictes, ja està.

Si hi ha conflictes, arreglar-los i fer commit.
