# Patró: Estendre una vista XML

## Problema

Necessites afegir camps nous o modificar la interfície d'un model existent.

## Solució

1. Crear un fitxer XML al mòdul
2. Definir una extensió de vista (`record` amb `id` i `model`)

## Tipus de vistes

| Tipus | Descripció |
|-------|-----------|
| `form` | Vista de formulari (edició) |
| `tree` | Vista de llista |
| `search` | Vista de cerca |
| `graph` | Vista de gràfics |
| `calendar` | Vista de calendari |

## Exemple: Afegir camps a un formulari

```xml
<?xml version="1.0" encoding="utf-8"?>
<openerp>
    <data>
        <!-- Extensió de vista de formulari -->
        <record id="view_giscedata_polissa_form" model="ir.ui.view">
            <field name="name">giscedata.polissa.form</field>
            <field name="model">giscedata.polissa</field>
            <field name="inherit_id" ref="original_module.view_form_id"/>
            <field name="type">form</field>
            <field name="arch" type="xml">
                <field name="x_new_field" position="after">
                    <field name="existing_field"/>
                </field>
            </field>
        </record>
    </data>
</openerp>
```

## Posicions

| Posició | Descripció |
|--------|-----------|
| `replace` | Substitueix el camp |
| `before` | Insereix abans del camp |
| `after` | Insereix après del camp |
| `inside` | Insereix dins (per grups) |

## Exemple: Afegir grup de camps

```xml
<field name="arch" type="xml">
    <group colspan="4" col="4">
        <field name="x_field_1"/>
        <field name="x_field_2"/>
    </group>
</field>
```

## Exemple: Ocultar camp

```xml
<field name="existing_field" position="replace"/>
```

## Exemple: Vista de cerca

```xml
<record id="view_partner_search" model="ir.ui.view">
    <field name="name">res.partner.search</field>
    <field name="model">res.partner</field>
    <field name="inherit_id" ref="base.view_res_partner_filter"/>
    <field name="type">search</field>
    <field name="arch" type="xml">
        <field name="x_custom_field" position="after">
            <field name="x_new_field"/>
        </field>
    </field>
</record>
```

**Font:** `som_leads_polissa/views/giscedata_crm_lead_view.xml`, `som_gurb/views/som_gurb_group_view.xml`
