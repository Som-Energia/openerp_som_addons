# -*- coding: utf-8 -*-
from osv import osv, fields
from tools import cache
import netsvc

class GiscedataPolissa(osv.osv):
    """Per gestionar els
    """
    _name = 'giscedata.polissa'
    _inherit = 'giscedata.polissa'

    @cache()
    def get_soci_energetica(self, cursor, uid, ids, context=None):
        """
        Returns energética soci id
        :param cursor:
        :param uid:
        :param ids:
        :param context:
        :return: id soci energética
        """
        imd_obj = self.pool.get('ir.model.data')
        return imd_obj.get_object_reference(
            cursor, uid, 'som_energetica', 'res_partner_energetica'
        )[1]


    def is_energetica(self, cursor, uid, contract_id, context=None):
        """
        Detecta si un contracte és d'energética si el seu soci és d'energética
        :param cursor:
        :param uid:
        :param contract_id: id del contracte
        :param context:
        :return: True o False si és d'energética o no
        """
        soci_id = self.read(cursor, uid, contract_id, ['soci'])['soci']

        if soci_id:
            id_soci_energetica = self.get_soci_energetica(cursor, uid, [])
            return soci_id[0] == id_soci_energetica

        return False

    def get_bad_energetica_partners(self, cursor, uid, contract_ids, context=None):
        """
        Retorna els ids dels partners amb la categoria incorrecte
        :param cursor:
        :param uid:
        :param contract_ids: id del contracte o llista de contractes
        :param context:
        :return: llista amb les partners a modificar
        """
        contract_fields = ['titular', 'pagador', 'altre_p', 'propietari_bank']
        imd_obj = self.pool.get('ir.model.data')
        partner_obj = self.pool.get('res.partner')

        if not isinstance(contract_ids, (list, tuple)):
            contract_ids = [contract_ids]

        contracts_data = self.read(cursor, uid, contract_ids, contract_fields)

        cat_energetica_id = imd_obj.get_object_reference(
            cursor, uid, 'som_energetica', 'res_partner_category_energetica'
        )[1]

        partners_list = []
        for contract_data in contracts_data:
            contract_id = contract_data['id']
            if not self.is_energetica(cursor, uid, contract_id):
                continue
            for contract_field in contract_fields:
                if not contract_data[contract_field]:
                    continue
                partner_id = contract_data[contract_field][0]
                partner_data = partner_obj.read(
                    cursor, uid, partner_id, context=context
                )
                if cat_energetica_id not in partner_data['category_id']:
                    partners_list.append(partner_id)

        return list(set(partners_list))

    def set_energetica(self, cursor, uid, contract_ids, context=None):
        """
        Afegeix tots el partners del contracte a la categoria energética si cal
        :param cursor:
        :param uid:
        :param contract_ids: id de contract or contract ids list
        :param context:
        :return: retorna True si ha modificat algun partner
        """
        logger = netsvc.Logger()
        imd_obj = self.pool.get('ir.model.data')
        partner_obj = self.pool.get('res.partner')

        if not isinstance(contract_ids, (list, tuple)):
            contract_ids = [contract_ids]

        cat_energetica_id = imd_obj.get_object_reference(
            cursor, uid, 'som_energetica', 'res_partner_category_energetica'
        )[1]

        bad_partners_ids = self.get_bad_energetica_partners(
            cursor, uid, contract_ids, context=context
        )

        for bad_id in bad_partners_ids:
            p_data = partner_obj.read(cursor, uid, bad_id, ['name'])
            partner_obj.write(
                cursor, uid, bad_id,
                {'category_id': [(6, 0, [cat_energetica_id])]}
            )
            logger.notifyChannel(
                'energetica', netsvc.LOG_WARNING,
                'Added partner {} to Energética category'.format(p_data['name'])
            )


GiscedataPolissa()
