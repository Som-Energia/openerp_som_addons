# -*- coding: utf-8 -*-
from osv import osv


class WizardCrearConsultaPobresa(osv.osv_memory):

    _name = "wizard.crear.consulta.pobresa"

    def crear_consulta_pobresa(self, cursor, uid, ids, context=None):

        if not context:
            return False

        if not isinstance(ids, (tuple, list)):
            ids = [ids]

        scp_obj = self.pool.get('som.consulta.pobresa')
        pol_obj = self.pool.get('giscedata.polissa')
        gff_obj = self.pool.get('giscedata.facturacio.factura')
        imd_obj = self.pool.get('ir.model.data')

        active_ids = context.get("active_ids")
        scp_creades = []
        sec_pobresa = imd_obj.get_object_reference(
            cursor, 1, 'giscedata_facturacio_comer_bono_social',
            'crm_section_bono_social_consulta_pobresa'
        )[1]

        for _id in active_ids:
            pol_id = gff_obj.read(cursor, uid, _id, ['polissa_id'])['polissa_id'][0]
            pol = pol_obj.browse(cursor, uid, pol_id)
            scp_id = scp_obj.create(cursor, uid, {
                'polissa_id': pol_id,
                'section_id': sec_pobresa,
                'name': '[{}] {} ({})'.format(
                    pol.name, pol.titular.name, pol.cups.id_municipi.name),
                'partner_id': pol.titular.id,
            })
            scp_creades.append(scp_id)

        return {
            "domain": "[('id','in', %s)]" % str(scp_creades),
            "name": "Consultes pobresa creades",
            "view_type": "form",
            "view_mode": "tree,form",
            "res_model": "som.consulta.pobresa",
            "type": "ir.actions.act_window",
        }


WizardCrearConsultaPobresa()
