# -*- coding: utf-8 -*-
from datetime import datetime
from gestionatr.defs import *
from gestionatr.input.messages.R1 import get_minimum_fields
from osv import osv, fields, orm
from tools.translate import _
import xml.etree.ElementTree as ET


class WizardAtcMultiChange(osv.osv_memory):
    _name = 'wizard.change.state.atc'
    _inherit = 'wizard.change.state.atc'

    def get_subtype_privacy(self, cursor, uid):
        imd_obj = self.pool.get('ir.model.data')
        return imd_obj.get_object_reference(
            cursor, uid, 'giscedata_subtipus_reclamacio', 'subtipus_reclamacio_038'
        )[1]

    def get_section_autoconsum(self, cursor, uid):
        imd_obj = self.pool.get('ir.model.data')
        return imd_obj.get_object_reference(
            cursor, uid, 'giscedata_switching', 'crm_case_section_autoconsum'
        )[1]

    def _do_additional_actions(self, cursor, uid, case_ids, resultat,  context=None):
        if not context:
            context = {}
        case_obj = self.pool.get('giscedata.atc')
        sw_obj = self.pool.get('giscedata.switching')
        partner_obj = self.pool.get('res.partner')
        part_event_obj = self.pool.get('res.partner.event')
        gen_obj = self.pool.get('giscedata.autoconsum.generador')

        # Autoconsum/generacio section
        section_autoconsum_id = self.get_section_autoconsum(cursor, uid)

        for case in case_obj.browse(cursor, uid, case_ids, context=context):
            # for Autoconsum/generacio  cases
            if case.section_id.id == section_autoconsum_id:
                if resultat == '01':
                    sw_model, sw_id = case.ref.split(',')
                    res = sw_obj.notifica_a_client(cursor, uid, int(sw_id))
                elif resultat == '02':
                    partner_to_delete = case.partner_id.id
                    gen_partner = imd_obj.get_object_reference(
                        cursor, uid, 'giscedata_switching', 'res_partner_gen_missing_partner'
                    )[1]
                    # Let's remove partner from ATC case
                    case.write({
                        'partner_id': gen_partner,
                        'partner_address_id': False,
                        'email_from': False,
                    })
                    # Let's remove partner from generators
                    gen_ids = gen_obj.search(cursor, uid, [('partner_id', '=', partner_to_delete)])
                    gen_obj.write(cursor, uid, gen_ids, {'partner_id': gen_partner})

                    # Let's remove related partner events
                    event_ids = part_event_obj.search(cursor, uid, [('partner_id', '=', partner_to_delete)])
                    part_event_obj.write(cursor, uid, event_ids, {'partner_id': gen_partner})

                    # At last let's delete the partner
                    partner_obj.unlink(cursor, uid, partner_to_delete)

                    # Let's remove partner from switching_generators

        return {}

    def _do_additional_actions_on_open(self, cursor, uid, case_ids, result, context=None):
        if not context:
            context = {}

        case_obj = self.pool.get('giscedata.atc')
        sw_obj = self.pool.get('giscedata.switching')

        # Autoconsum/generacio section and subtypes
        section_autoconsum_id = self.get_section_autoconsum(cursor, uid)
        subtipus_id = self.get_subtype_privacy(cursor, uid)

        for case in case_obj.browse(cursor, uid, case_ids, context=context):
            if case.section_id.id == section_autoconsum_id and case.subtipus_id.id == subtipus_id:
                sw_model, sw_id = case.ref.split(',')
                res = sw_obj.notifica_a_client(cursor, uid, int(sw_id),
                    template='notificacioTractamentDadesGeneradorAutoconsum')
        return True


WizardAtcMultiChange()