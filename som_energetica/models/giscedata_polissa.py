# -*- coding: utf-8 -*-
from osv import osv
from tools import cache
import netsvc


class GiscedataPolissa(osv.osv):
    """Per gestionar els"""

    _name = "giscedata.polissa"
    _inherit = "giscedata.polissa"

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
        imd_obj = self.pool.get("ir.model.data")
        return imd_obj.get_object_reference(
            cursor, uid, "som_energetica", "res_partner_energetica"
        )[1]

    @cache()
    def get_soci_candela(self, cursor, uid, ids, context=None):
        """
        Returns Candela soci id
        :param cursor:
        :param uid:
        :param ids:
        :param context:
        :return: id soci Candela
        """
        rp_obj = self.pool.get("res.partner")
        return rp_obj.search(
            cursor, uid, [("ref", "=", "S076331")], limit=1, context=context
        )[0]

    def is_energetica(self, cursor, uid, contract_id, context=None):
        """
        Detecta si un contracte és d'energética si el seu soci és d'energética
        :param cursor:
        :param uid:
        :param contract_id: id del contracte
        :param context:
        :return: True o False si és d'energética o no
        """
        soci_id = self.read(cursor, uid, contract_id, ["soci"])["soci"]

        if soci_id:
            id_soci_energetica = self.get_soci_energetica(cursor, uid, [])
            return soci_id[0] == id_soci_energetica

        return False

    def is_candela(self, cursor, uid, contract_id, context=None):
        """
        Detecta si un contracte és de Candela si el seu soci és de Candela
        :param cursor:
        :param uid:
        :param contract_id: id del contracte
        :param context:
        :return: True o False si és de Candela o no
        """
        soci_id = self.read(cursor, uid, contract_id, ["soci"])["soci"]

        if soci_id:
            id_soci_candela = self.get_soci_candela(cursor, uid, [])
            return soci_id[0] == id_soci_candela

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

        imd_obj = self.pool.get("ir.model.data")

        if not isinstance(contract_ids, (list, tuple)):
            contract_ids = [contract_ids]

        cat_energetica_id = imd_obj.get_object_reference(
            cursor, uid, "som_energetica", "res_partner_category_energetica"
        )[1]

        partners_list = []

        for contract_id in contract_ids:
            if not self.is_energetica(cursor, uid, contract_id):
                continue

            contract = self.browse(cursor, uid, contract_id, context)

            if contract.titular and cat_energetica_id not in [
                x.id for x in contract.titular.category_id
            ]:
                partners_list.append(contract.titular.id)

            if contract.pagador and cat_energetica_id not in [
                x.id for x in contract.pagador.category_id
            ]:
                partners_list.append(contract.pagador.id)

            if contract.altre_p and cat_energetica_id not in [
                x.id for x in contract.altre_p.category_id
            ]:
                partners_list.append(contract.altre_p.id)

            if contract.administradora and cat_energetica_id not in [
                x.id for x in contract.administradora.category_id
            ]:
                partners_list.append(contract.administradora.id)

            if (
                contract.bank
                and contract.bank.partner_id
                and cat_energetica_id not in [x.id for x in contract.bank.partner_id.category_id]
            ):
                partners_list.append(contract.bank.partner_id.id)

            if (
                contract.direccio_pagament
                and contract.direccio_pagament.partner_id
                and cat_energetica_id
                not in [x.id for x in contract.direccio_pagament.partner_id.category_id]
            ):
                partners_list.append(contract.direccio_pagament.partner_id.id)

            if (
                contract.direccio_notificacio
                and contract.direccio_notificacio.partner_id
                and cat_energetica_id
                not in [x.id for x in contract.direccio_notificacio.partner_id.category_id]
            ):
                partners_list.append(contract.direccio_notificacio.partner_id.id)

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
        imd_obj = self.pool.get("ir.model.data")
        partner_obj = self.pool.get("res.partner")

        if not isinstance(contract_ids, (list, tuple)):
            contract_ids = [contract_ids]

        cat_energetica_id = imd_obj.get_object_reference(
            cursor, uid, "som_energetica", "res_partner_category_energetica"
        )[1]

        bad_partners_ids = self.get_bad_energetica_partners(
            cursor, uid, contract_ids, context=context
        )

        for bad_id in bad_partners_ids:
            p_data = partner_obj.read(cursor, uid, bad_id, ["name"])
            partner_obj.write(cursor, uid, bad_id, {"category_id": [(6, 0, [cat_energetica_id])]})
            logger.notifyChannel(
                "energetica",
                netsvc.LOG_WARNING,
                "Added partner {} to Energética category".format(p_data["name"]),
            )

    def create(self, cursor, uid, vals, context=None):
        res_id = super(GiscedataPolissa, self).create(cursor, uid, vals, context)

        if self.is_energetica(cursor, uid, res_id):
            self.set_energetica(cursor, uid, [res_id], context)

        return res_id


GiscedataPolissa()
