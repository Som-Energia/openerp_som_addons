# Coses que s’han d’evitar en aquest projecte

## API i sintaxi moderna
- No utilitzar `@api.model`, `@api.depends`, `@api.onchange`.
- No utilitzar `fields.Many2one`, `fields.Char`, etc. de l’API nova.
- No utilitzar Python 3 (print(), f-strings, dict comprehensions, etc.).

## Arquitectura moderna d’Odoo
- No utilitzar QWeb, assets, web controllers, ni res relacionat amb Odoo Web.
- No introduir patrons propis d’Odoo 8+ (nous decoradors, nou ORM, etc.).

## Llibreries externes
- No afegir dependències no aprovades.
- No utilitzar frameworks moderns (Flask, Django, etc.).

## Estils no desitjats

> Veure [docs/patterns/](../../docs/patterns/) per a les receptes oficials del projecte.

- No generar receptes, exemples no relacionats amb el projecte.
- No proposar patrons de disseny complexos.
- No generar codi massa màgic o difícil de mantenir.

## Suggerències a evitar:
- Quan posem `import pudb;pu.db` és per interrompre execució en mode debug, ja està ve com està. Sobretot volem que NO ens suggereixi `import pu`.
