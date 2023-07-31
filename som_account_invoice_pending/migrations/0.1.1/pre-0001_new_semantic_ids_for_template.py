# coding=utf-8
from oopgrade import DataMigration


def up(cursor, installed_version):
    if not installed_version:
        return

    xml_content = """<?xml version="1.0" encoding="UTF-8" ?>
    <openerp>
        <data noupdate="1">
            <record model="poweremail.core_accounts" id="cobraments_mail_account">
                <field name="email_id">cobraments@somenergia.coop</field>
                <field name="company">yes</field>
                <field name="user">1</field>
                <field name="smtpserver">smtp.sendgrid.net</field>
                <field name="send_pref">html</field>
                <field name="name">Gestió de Cobraments</field>
                <field name="state">approved</field>
                <field name="smtpport">587</field>
            </record>

            <record model="poweremail.templates" id="email_impagats_annex3">
                <field name="name">Impagats: Procediment tall de llum Annex 3</field>
                <field name="object_name" model="ir.model" search="[('name', '=', 'giscedata.facturacio.factura')]"/>
                <field eval="0" name="save_to_drafts"/>
                <field name="model_int_name">giscedata.facturacio.factura</field>
                <field name="def_to">${object.address_invoice_id.email}, ${object.polissa_id.direccio_notificacio.email}</field>
                <field eval="0" name="auto_email"/>
                <field eval="0" name="single_email"/>
                <field eval="0" name="use_sign"/>
                <field name="def_subject">Procedimiento corte de luz (Anexo III) / Procediment tall de llum (Annex III)</field>
                <field name="template_language">mako</field>
                <field eval="0" name="send_on_create"/>
                <field name="lang"/>
                <field eval="0" name="send_on_write"/>
                <field name="def_bcc">support.17062.b8d9f4469fa4d856@helpscout.net</field>
                <field name="def_cc">correo@certificado.lleida.net</field>
                <field name="enforce_from_account" model="poweremail.core_accounts" search="[('name','=', 'Gestió de Cobraments')]"/>
                <field name="def_body_text"><![CDATA[<!doctype html>
                    <html>
                    <head></head>
                    <body>
                    Este correo ha estado generado automáticamente.
                    </body>
                    </html>
                    ]]></field>
            </record>
        </data>
    </openerp>
    """  # noqa: E501

    dm = DataMigration(
        xml_content,
        cursor,
        "som_account_invoice_pending",
        {
            "poweremail.core_accounts": ["email_id"],
            "poweremail.templates": ["name"],
        },
    )
    dm.migrate()


migrate = up
