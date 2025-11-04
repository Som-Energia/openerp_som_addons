# coding=utf-8
from oopgrade import DataMigration
from addons import get_module_resource


def up(cursor, installed_version):
    if not installed_version:
        return

    xml_content = '''<?xml version="1.0" encoding="UTF-8" ?>
    <openerp>
        <data>
            <record model="poweremail.core_accounts" id="generation_mail_account">
                <field name="email_id">generationkwh@somenergia.coop</field>
                <field name="company">yes</field>
                <field name="smtpserver">smtp.mandrillapp.com</field>
                <field name="send_pref">html</field>
                <field name="name">Generation kWh</field>
                <field name="state">approved</field>
                <field name="smtpport">587</field>
            </record>
            <record model="poweremail.core_accounts" id="inversions_mail_account">
                <field name="email_id">invertir@somenergia.coop</field>
                <field name="company">yes</field>
                <field name="smtpserver">smtp.mandrillapp.com</field>
                <field name="send_pref">html</field>
                <field name="name">Som Energia Invertir</field>
                <field name="state">approved</field>
                <field name="smtpport">587</field>
            </record>
        </data>
    </openerp>
    '''

    dm = DataMigration(xml_content, cursor, 'som_generationkwh', {
        'poweremail.core_accounts': ['email_id']
    })
    dm.migrate()

migrate = up
