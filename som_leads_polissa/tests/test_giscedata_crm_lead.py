# -*- coding: utf-8 -*-

from destral import testing
from destral.transaction import Transaction


class TestGiscedataCrmLead(testing.OOTestCase):

    def setUp(self):
        self.txn = Transaction().start(self.database)
        self.cursor = self.txn.cursor
        self.uid = self.txn.user
        self.lead_o = self.openerp.pool.get('giscedata.crm.lead')
        self.poweremail_template_o = self.openerp.pool.get('poweremail.templates')
        self.imd_o = self.openerp.pool.get('ir.model.data')
        # Crea una plantilla de prova
        self.test_template = self.poweremail_template_o.create(self.cursor, self.uid, {
            'name': 'Test Template',
            'template_language': 'mako',
        })

        # Crea un lead de prova
        self.test_lead = self.lead_o.create(self.cursor, self.uid, {
            'name': 'Test Lead',
            'crm_lead_type': 'activation',  # o 'renovation' segons el cas
            'signature_template_id': self.test_template,
        })

    def tearDown(self):
        self.txn.stop()

    def test_get_contract_template_from_delivery_type_email(self):
        # Test per delivery_type 'email' i no renovació
        tmpl_id = self.lead_o.get_contract_template_from_delivery_type(
            self.cursor, self.uid, self.test_lead, delivery_type='email'
        )
        self.assertEqual(
            tmpl_id, self.test_template,
            "El template ID no coincideix amb el camp signature_template_id"
        )

    def test_get_contract_template_from_delivery_type_renovation(self):
        # Test per renovació
        self.lead_o.write(
            self.cursor, self.uid, self.test_lead, {'crm_lead_type': 'renovation'}
        )
        tmpl_id = self.lead_o.get_contract_template_from_delivery_type(
            self.cursor, self.uid, self.test_lead, delivery_type='email'
        )
        # Aquí hauries de posar l'ID esperat per a la renovació
        expected_renovation_template_id = self.imd_o.get_object_reference(
            self.cursor, self.uid, 'giscedata_crm_leads_signatura', 'renovacio_lead_signatura'
        )[1]
        self.assertEqual(
            tmpl_id, expected_renovation_template_id,
            "El template ID no coincideix amb l'esperat per renovació"
        )
