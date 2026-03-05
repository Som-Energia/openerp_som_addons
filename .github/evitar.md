# Coses que s’han d’evitar en aquest projecte

## API i sintaxi moderna
- No utilitzar `@api.model`, `@api.depends`, `@api.onchange`.
- No utilitzar `fields.Many2one`, `fields.Char`, etc. de l’API nova.
- No utilitzar Python 3 (print(), f-strings, dict comprehensions, etc.).

## Arquitectura moderna d’Odoo
- No crear carpetes com `models/`, `views/`, `security/` amb estructura Odoo 8+.
- No utilitzar QWeb, assets, web controllers, ni res relacionat amb Odoo Web.

## Llibreries externes
- No afegir dependències no aprovades.
- No utilitzar frameworks moderns (Flask, Django, etc.).

## Estils no desitjats
- No generar receptes, exemples no relacionats amb el projecte.
- No proposar patrons de disseny complexos.
- No generar codi massa màgic o difícil de mantenir.
