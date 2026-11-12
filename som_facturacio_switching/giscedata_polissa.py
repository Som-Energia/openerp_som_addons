# -*- coding: utf-8 -*-

from osv import osv


class GiscedataPolissa(osv.osv):
    """Funcions utilitzades pel switching"""

    _name = "giscedata.polissa"
    _inherit = "giscedata.polissa"

    def escull_llista_preus(self, cursor, uid, contract_id, llista, context=None):
        """SOM chooses as default the fare's finished by '_SOM' suffix except
        when is a extrapeninsular system. In this case, uses fares finished by
        '_SOM_INSULAR' suffix"""
        if isinstance(contract_id, (tuple, list)):
            contract_id = contract_id[0]
        if not context:
            context = {}

        pricelist_obj = self.pool.get("product.pricelist")
        tariff_obj = self.pool.get("giscedata.polissa.tarifa")

        if llista and isinstance(llista[0], int):
            llista = pricelist_obj.browse(cursor, uid, llista, context)

        contract = self.browse(cursor, uid, contract_id, context=context)

        som_llista = []
        try:
            tariff_id = context.get("tarifa_atr", False)
            if tariff_id:
                tariff = tariff_obj.browse(cursor, uid, tariff_id)
                context["forced_tariff"] = tariff.name
            wiz_o = self.pool.get("wizard.change.to.indexada")
            pricelist_id = wiz_o.get_new_pricelist(cursor, uid, contract, context=context)
            if pricelist_id in llista:
                som_llista = [pricelist_id]
        except Exception:
            # if we get an exception is because we haven't found a list price, so, empy list
            pass

        # si li passem una list de només una pólissa, retorna la llista única
        return super(GiscedataPolissa, self).escull_llista_preus(
            cursor, uid, id, som_llista, context=context
        )


GiscedataPolissa()
