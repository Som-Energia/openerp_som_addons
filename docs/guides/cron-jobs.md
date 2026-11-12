# Crons gestionats des de `crontab`

Els registres `ir.cron` s'han de crear desactivats (`active=False`). El
planificador del servidor OpenERP no els ha d'executar: el `crontab` del servei
n'invoca l'acció explícitament amb `erp/scripts/cron/crontab_actions.py`.

## Afegir un cron

1. Defineix l'acció en un registre `ir.cron` amb un identificador XML estable,
   però desactivada.
2. Implementa la funció al model i afegeix tests.
3. Programa la invocació externa amb `crontab`. La utilitat cerca el registre,
   fins i tot si és inactiu, i en registra l'execució a OpenERP.

Format de la comanda:

```bash
PYENV_VERSION=erp <ERP_ROOT>/scripts/cron/crontab_actions.py \
    <ModelCamelCase>.<funcio> <base_de_dades> <port> <usuari> <contrasenya>
```

Exemple de programació trimestral, a les 02:00 UTC el primer dia dels mesos
indicats:

```cron
0 2 1 1,4,7,10 * PYENV_VERSION=erp <ERP_ROOT>/scripts/cron/crontab_actions.py <ModelCamelCase>.<funcio> <base_de_dades> <port> <usuari> <contrasenya> >> <fitxer_de_log> 2>&1
```

El calendari efectiu és el del `crontab`; els camps d'interval del registre
inactiu només documenten la freqüència prevista.
