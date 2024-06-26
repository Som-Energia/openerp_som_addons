# -*- coding: utf-8 -*-
from osv import osv


class WizardLoadServeiGenRecordsFromFile(osv.osv_memory):
    _name = 'wizard.load.servei.gen.records.from.file'
    _inherit = 'wizard.load.servei.gen.records.from.file'

    def validate_data_and_get_state_contract(self, cursor, uid, polissa_id, record_data, context=None):
        """
        Valida les dades aportades a record_data i retorna un estat adient a la validació.
        :param cursor:
        :param uid: <res.users> id
        :type uid: long
        :param polissa_id: <giscedata.polissa> id
        :type polissa_id: long
        :param record_data: Llista de dades obtingudes del 'giscedata.servei.generacio.polissa'
        :param record_data: Conté {'nif': str, 'data_sortida': date, 'pes': float, 'servei_gen_id': long}
        :type record_data: dict
        :param context: OpenERP context
        :type context: {}
        :return: [
            ('vinculat', _('Vinculado')),
            ('pendent', _('Pendiente')),
            ('pendent_incidencia', _('Pendiente con incidencias')),
            ('confirmat', _('Confirmado')),
            ('anullat', _('Anulado')),
        ]
        :rtype: str
        """
        if context is None:
            context = {}

        polissa_obj = self.pool.get('giscedata.polissa')
        polissa_category_obj = self.pool.get('giscedata.polissa.category')
        servei_gen_pol_obj = self.pool.get('giscedata.servei.generacio.polissa')

        read_fields = ['id', 'titular.vat', 'state', 'category_id', 'autoconsumo']
        ctx = context.copy()
        ctx.update({'prefetch': False})
        polissa = polissa_obj.browse(cursor, uid, polissa_id, context=ctx)

        # Categories GURB
        not_allowed_pol_category_ids = polissa_category_obj.search(cursor, 1, [('code', 'ilike', 'GURB')])

        # Categories AUVIDI
        auvidi_category_ids = polissa_category_obj.search(cursor, 1, [('code', 'ilike', 'AUVIDI')])

        # Te autoconsum col.lectiu
        te_auto_collectiu = polissa_obj.te_autoconsum(cursor, uid, polissa_id, amb_o_sense_excedents=5, context=context)

        # Participació en altres AUVIDIs
        altres_auvidis = servei_gen_pol_obj.search(cursor, uid, [
            ('polissa_id', '=', polissa_id),
            ('servei_generacio_id', '=', record_data['servei_gen_id'])
        ])

        # Categories coincidents que no es permeten
        matching_category_ids = [
            cat.id for cat in polissa.category_id if cat.id in not_allowed_pol_category_ids
        ]

        # Te categoria AUVIDI
        te_auvidi_category = bool(len([
            cat.id for cat in polissa.category_id if cat.id in auvidi_category_ids
        ]))

        # TODO validar generationkwh
        te_generationkwh = False

        # Condicions especifiques
        compleix_condicions = not len(altres_auvidis) and not len(matching_category_ids) \
                              and not te_auto_collectiu and not te_generationkwh

        real_state = 'vinculat'
        # Let's check VAT is the correct one
        if polissa.titular.vat not in record_data['nif'] and \
                record_data['nif'] not in polissa.titular.vat:
            real_state = 'pendent_incidencia'

        else:
            # Mirem l'estat de la pòlissa i les validacions específiques
            if polissa.state == 'esborrany':
                if compleix_condicions and te_auvidi_category:
                    real_state = 'pendent'
                else:
                    real_state = 'pendent_incidencia'
            elif polissa.state == 'activa':
                if compleix_condicions and te_auvidi_category:
                    real_state = 'confirmat'
                elif compleix_condicions:
                    real_state = 'pendent'
                else:
                    real_state = 'pendent_incidencia'
        return real_state


WizardLoadServeiGenRecordsFromFile()
