# -*- coding: utf-8 -*-

from osv import osv


class GiscedataPolissa(osv.osv):
    """Funcions utilitzades pel switching
    """
    _name = 'giscedata.polissa'
    _inherit = 'giscedata.polissa'

    def escull_llista_preus(self, cursor, uid, contract_id, llista,
                            context=None):
        """ SOM chooses as default the fare's finished by '_SOM' suffix except
        when is a extrapeninsular system. In this case, uses fares finished by
        '_SOM_INSULAR' suffix"""
        if isinstance(contract_id, (tuple, list)):
            contract_id = contract_id[0]

        pricelist_obj = self.pool.get('product.pricelist')

        # enables list as an id list instead of pricelist instances list
        if llista and isinstance(llista[0], int):
            llista = pricelist_obj.browse(
                cursor, uid, llista, context
            )

        contract = self.browse(cursor, uid, contract_id, context=context)

        som_llista = llista[:]
        if len(llista) > 1:
            som_llista = contract.cups.id_municipi.filter_compatible_pricelists(
                som_llista, context)

        # si li passem una list de només una pólissa, retorna la llista única
        return super(GiscedataPolissa,
                     self).escull_llista_preus(cursor, uid, id, som_llista,
                                               context=context)


GiscedataPolissa()
