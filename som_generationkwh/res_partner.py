# -*- coding: utf-8 -*-

from osv import osv, fields
from datetime import datetime, date
from tools.translate import _


class ResPartner(osv.osv):

    _name = 'res.partner'
    _inherit = 'res.partner'

    def www_generationkwh_investments(self, cursor, uid, id, context=None):
        """
        Returns the list of investments
        """
        Investment =self.pool.get('generationkwh.investment')
        Dealer =self.pool.get('generationkwh.dealer')
        idmap = dict(Dealer.get_members_by_partners(cursor, uid, [id]))
        if not idmap: # Not a member
            return []
        return Investment.list(cursor, uid, idmap[id], context=context)

    def www_generationkwh_assignments(self, cursor, uid, id, context=None):
        Dealer =self.pool.get('generationkwh.dealer')
        idmap = dict(Dealer.get_members_by_partners(cursor, uid, [id]))
        if not idmap: return [] # Not a member

        Assignments =self.pool.get('generationkwh.assignment')
        assignment_ids = Assignments.search(cursor, uid, [
            ('member_id', '=', idmap[id]),
            ('end_date', '=', False),
            ])
        def process(x):
            x['contract_name'] = x['contract_id'][1]
            x['contract_id'] = x['contract_id'][0]
            x['member_name'] = x['member_id'][1]
            x['member_id'] = x['member_id'][0]
            x['annual_use_kwh'] = x.pop('cups_anual_use')
            x['contract_address'] = x.pop('cups_direction')
            del x['end_date']
            return x

        return sorted([
            process(x)
            for x in Assignments.read(cursor, uid, assignment_ids, [])
        ], key=lambda x: (x['priority'],x['id']))

    def verifica_baixa_soci(self, cursor, uid, ids, context=None):
        #- Comprovar si té generationkwh: Existeix atribut al model generation que ho indica. Altrament es poden buscar les inversions.
        #- Comprovar si té inversions vigents: Buscar inversions vigents.
        #- Comprovar si té contractes actius: Buscar contractes vigents.
        #- Comprovar si té Factures pendents de pagament: Per a aquesta comprovació hi ha una tasca feta a la OV que ens pot ajudar feta per en Fran a la següent PR: https://github.com/gisce/erp/pull/7997/files

        """Mètode per donar de baixa un soci.
        """
        if not context:
            context = {}
        if not ids:
            return
        if isinstance(ids, (int, long)):
            ids = [ids]
        if len(ids) !=1:
            raise osv.except_osv(_('adsads'), _('asdads11'))#TODO:

        imd_obj = self.pool.get('ir.model.data')
        invest_obj = self.pool.get('generationkwh.investment')
        pol_obj = self.pool.get('giscedata.polissa')
        fact_obj = self.pool.get('giscedata.facturacio.factura')
        soci_obj = self.pool.get('somenergia.soci')
        today = datetime.today().strftime('%Y-%m-%d')
        res_partner_id = ids[0] 

        member_id = soci_obj.search(cursor, uid, [('partner_id', '=', res_partner_id)])[0]

        baixa = soci_obj.read(cursor, uid, [member_id], ['baixa'])[0]['baixa']

        if baixa:
            raise osv.except_osv(_('El soci no pot ser donat de baixa!'), _('Ja ha estat donat de baixa baixa anteriorment!'))

        gen_invest = invest_obj.search(cursor, uid, [('member_id','=', member_id),
                                                     ('emission_id','=', 1), 
                                                     ('last_effective_date','>=', today)])
        if gen_invest:
            raise osv.except_osv(_('El soci no pot ser donat de baixa!'), _('El soci té inversions de generation actives.'))

        apo_invest = invest_obj.search(cursor, uid, [('member_id','=', member_id),
                                                     ('emission_id','=', 2),
                                                     '|', ('last_effective_date','=', False), ('last_effective_date','>=', today)])
        if apo_invest:
            raise osv.except_osv(_('El soci no pot ser donat de baixa!'), _('El soci té aportacions actives.'))

        factures_pendents = fact_obj.search(cursor, uid, [('partner_id', '=', res_partner_id), 
                                                          ('state', 'not in', ['cancel','paid']), 
                                                          ('type', '=', 'out_invoice')])
        if factures_pendents:
            raise osv.except_osv(_('El soci no pot ser donat de baixa!'), _('El soci té factures pendents.'))

        polisses = pol_obj.search(cursor, uid, 
                [('titular','=', res_partner_id),
                 ('state','!=','baixa'),
                 ('state','!=','cancelada')])
        if polisses:
            raise osv.except_osv(_('El soci no pot ser donat de baixa!'), _('El soci té al menys un contracte actiu.'))
                
        #- Anar a la fitxa de persona sòcia (No fitxa client)
        #- Treure categoria sòcia a General a Categories.
        #- Clicar a Soci, soci de baixa i posar la data de la baixa.
        #- A Notes afegir inicials de la persona que fa la baixa i data i les observacions  que facin falta.
        #- Deixar fitxa activa.

        soci_category_id = imd_obj.get_object_reference(
            cursor, uid, 'som_partner_account', 'res_partner_category_soci'
        )[1]
        
        def delete_rel(cursor, uid, categ_id, res_partner_id):
            cursor.execute('delete from res_partner_category_rel where category_id=%s and partner_id=%s',(categ_id, res_partner_id))
        
        res_users = self.pool.get('res.users')
        usuari = res_users.read(cursor, uid, uid, ['name'])['name']
        old_comment = soci_obj.read(cursor, uid, [member_id], ['comment'])[0]['comment']
        old_comment = old_comment + '\n' if old_comment else '' 
        comment =  "{}Baixa efectuada a data {} per: {}".format(old_comment, today, usuari)
        soci_obj.write(cursor, uid, [member_id], {'baixa': True,
                                                'data_baixa_soci': today,
                                                'comment': comment })
        delete_rel(cursor, uid, soci_category_id, res_partner_id)




ResPartner()

# vim: et sw=4 ts=4
