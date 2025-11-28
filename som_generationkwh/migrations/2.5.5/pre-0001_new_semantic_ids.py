# coding=utf-8
from oopgrade import DataMigration
from addons import get_module_resource


def up(cursor, installed_version):
    if not installed_version:
        return

    xml_content = '''<?xml version="1.0" encoding="UTF-8" ?>
    <openerp>
        <data noupdate="1">
                <record model="product.category" id="categ_inversions">
                    <field name="name">Inversions</field>
                </record>
                <record id="apo_journal" model="account.journal">
                    <field name="code">APO</field>
                    <field name="user_id" ref="base.user_root"/>
                    <field eval="False" name="centralisation"/>
                    <field eval="False" name="group_invoice_lines"/>
                    <field name="type">cash</field>
                    <field name="default_credit_account_id" model="account.account" search="[('code','=','555000000010')]"/>
                    <field name="default_debit_account_id" model="account.account" search="[('code','=','555000000010')]"/>
                    <field name="view_id" ref="account.account_journal_bank_view"/>
                    <field name="sequence_id" ref="account.sequence_journal"/>
                    <field eval="True" name="active"/>
                    <field eval="True" name="update_posted"/>
                    <field name="name">Factures Liquidació Aportacions</field>
                    <field eval="False" name="refund_journal"/>
                    <field eval="True" name="entry_posted"/>
                </record>
                <record id="apo_product_template_ae" model="product.template">
                    <field name="name">Aportacions</field>
                </record>
                <record id="apo_product_ae" model="product.product">
                    <field name="product_tmpl_id" ref="apo_product_template_ae"/>
                    <field name="default_code">APO_AE</field>
                </record>
                <record id="apo_investment_payment_mode" model="payment.mode">
                   <field name="name">APORTACIONS (Enginyers)</field>
                   <field name="type" model="payment_type" search="[('code', '=', 'RECIBO_CSB')]"/>
                   <field name="journal" ref="apo_journal"/>
                   <field name="bank_id" model="res_partner_bank" search="[('partner_id', '=', 1)]"/>
                   <field name="tipo">sepa19</field>
                   <field name="nombre">Som Energia SCCL</field>
                   <field name="sufijo">000</field>
                   <field name="require_bank_account" eval="True"/>
                   <field name="partner_id">1</field>
                   <field name="sepa_creditor_code">ES24000F55091367</field>
                </record>
        </data>
    </openerp>
    '''

    dm = DataMigration(xml_content, cursor, 'som_generationkwh', {
        'payment.mode': ['name']
    })
    dm.migrate()

migrate = up
