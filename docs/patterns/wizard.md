# Patró: Crear un Wizard

## Problema

Necessites crear un formulari temporal per executar una acció (importar dades, executar processos, etc.).

## Solució

1. Crear un fitxer Python pel wizard
2. Crear un fitxer XML per la vista
3. Crear un fitxer XML per registrar-lo

## Wizard senzill

### Python

```python
# -*- coding: utf-8 -*-
from osv import osv, fields
import pooler


class WizardMyAction(osv.osv_memory):
    """Wizard per executar una acció."""

    _name = "wizard.my.action"

    _columns = {
        "name": fields.char(u"Nom", size=256, required=True),
        "partner_id": fields.many2one("res.partner", u"Client"),
    }

    def action_execute(self, cursor, uid, ids, context=None):
        """Executa l'acció."""
        pool = pooler.get_pool(cursor.dbname)
        wiz = self.browse(cursor, uid, ids[0], context=context)

        # Fer alguna cosa
        return {"type": "ir.actions.act_window_close"}


WizardMyAction()
```

### Vista XML

```xml
<?xml version="1.0" encoding="utf-8"?>
<openerp>
    <data>
        <record id="view_wizard_my_action_form" model="ir.ui.view">
            <field name="name">wizard.my.action.form</field>
            <field name="model">wizard.my.action</field>
            <field name="type">form</field>
            <field name="arch" type="xml">
                <form string="Acció">
                    <group colspan="4" col="4">
                        <field name="name"/>
                        <field name="partner_id"/>
                    </group>
                    <group colspan="4" col="4">
                        <button name="action_execute" string="Executar" type="object"/>
                        <button name="oe_dialog_button_cancel" string="Cancel·lar" special="cancel" type="object"/>
                    </group>
                </form>
            </field>
        </record>
    </data>
</openerp>
```

### Registre (action)

```xml
<record id="action_wizard_my_action" model="ir.actions.act_window">
    <field name="name">Acció</field>
    <field name="res_model">wizard.my.action</field>
    <field name="view_type">form</field>
    <field name="view_mode">form</field>
    <field name="target">new</field>
    <field name="context">{}</field>
</record>
```

## Wizard amb assistent (steps)

```python
class WizardMultiStep(osv.osv_memory):
    _name = "wizard.multi.step"

    def _default_step(self, cursor, uid, context=None):
        return 1

    _columns = {
        "step": fields.integer(),
        "name": fields.char(u"Nom", size=256),
    }

    _defaults = {
        "step": _default_step,
    }

    def step_1(self, cursor, uid, ids, context=None):
        return {"name": u"Pagament 2"}

    def step_2(self, cursor, uid, ids, context=None):
        # Executar acció final
        return {"type": "ir.actions.act_window_close"}
```

**Font:** `som_autoreclama/wizard/wizard_som_autoreclama_set_correct_state.py`, `som_stash/wizard/wizard_som_stasher.py`
