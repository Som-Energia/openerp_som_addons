from osv import osv


class GiscedataPolissa(osv.osv):
    _name = "giscedata.polissa"
    _inherit = "giscedata.polissa"

    def _modified_partners(self, cursor, uid, ids, vals):
        """
        Given some fields to be changed in a set of contracts,
        it returns the partners that will need to update their token.
        """
        # TODO: unify definition with the one in ResPartner.assign_token
        # TODO: notifica not suported (is a partner address)
        # TODO: consider administradora as allowed_relations
        allowed_relations = [
            "pagador",
            "titular",
        ]
        if type(ids) not in (list, tuple):
            ids = [ids]
        relations = set(vals.keys()).intersection(allowed_relations)
        if not relations:
            return []  # avoid reading
        polisses = self.read(cursor, uid, ids, list(relations))
        result = set()
        for relation in relations:
            newpartner = vals[relation]
            for polissa in polisses:
                oldpartner = polissa[relation][0] if polissa[relation] else False
                if oldpartner == newpartner:
                    continue
                if oldpartner:
                    result.add(oldpartner)
                if newpartner:
                    result.add(newpartner)
        return list(result)

    def write(self, cursor, uid, ids, vals, context=None):
        """Assign new token if partner not have"""

        partners_to_update = self._modified_partners(cursor, uid, ids, vals)

        res = super(GiscedataPolissa, self).write(cursor, uid, ids, vals, context)

        if partners_to_update:
            partner_obj = self.pool.get("res.partner")
            partner_obj.assign_token(cursor, uid, partners_to_update, context)

        return res


GiscedataPolissa()
# vim: et ts=4 sw=4
