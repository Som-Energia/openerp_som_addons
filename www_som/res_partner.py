# -*- coding: utf-8 -*-

from osv import osv


class ResPartner(osv.osv):

    _name = "res.partner"
    _inherit = "res.partner"

    def www_ov_attachments(self, cursor, uid, partner_id, context=None):
        """
        Returns the list of the OV attachments for this parnter.
        TODO: Now only works for attachments in the res_partner and poweremail.mailbox,
        but it can be improved in the future.
        """
        attachment_obj = self.pool.get("ir.attachment")
        attachment_ids = self._query_ov_attachments_ids(cursor, uid, partner_id)
        res = []
        for attachment in attachment_obj.browse(cursor, uid, attachment_ids):
            res.append({
                'erp_id': attachment.id,
                'name': attachment.name,
                'file_name': attachment.datas_fname,
                'date': attachment.create_date,
                'res_model': attachment.res_model,
                'res_id': attachment.res_id,
                'category': attachment.category_id.code,
            })
        return res

    def www_get_ov_attachment(self, cursor, uid, attachment_id, partner_id, context=None):
        """
        Downloads an OV attachment
        TODO: Now only works for attachments in the res_partner and poweremail.mailbox,
        but it can be improved in the future.
        """
        attachment_obj = self.pool.get("ir.attachment")
        attachment_ids = self._query_ov_attachments_ids(
            cursor, uid, partner_id, attachment_id)
        if not attachment_ids:
            raise Exception("The attachment doesn't exists or you don't have permission")

        return attachment_obj.read(cursor, uid, attachment_id, ['datas_fname', 'datas'])

    def _query_ov_attachments_ids(
            self, cursor, uid, partner_id, attachment_id=None, context=None):
        """
        Gets the IDs of a partner OV attachments, also check a single attachment.
        TODO: Now only works for attachments in the res_partner and poweremail.mailbox,
        but it can be improved in the future.
        """
        cursor.execute('''
            select ia.id
            from ir_attachment ia
            inner join ir_attachment_category iac on ia.category_id = iac.id
            where iac.ov_available is true
            and (%(attachment_id)s is null or ia.id = %(attachment_id)s)
            and (
             (ia.res_model = 'res.partner' and ia.res_id = %(partner_id)s)
            or
             (ia.res_model = 'poweremail.mailbox' and (
              select partner_id from som_enviament_massiu sem where sem.id = (
               select SPLIT_PART(pm.reference, ',', 2)::int from poweremail_mailbox pm
               where pm.id = ia.res_id
               and SPLIT_PART(pm.reference, ',', 1) = 'som.enviament.massiu'
             )) = %(partner_id)s)
            )
        ''', {'partner_id': partner_id, 'attachment_id': attachment_id})
        return [line[0] for line in cursor.fetchall()]


ResPartner()


class res_partner_bank(osv.osv):
    _inherit = "res.partner.bank"

    def create(self, cr, uid, vals, context=None):
        if "acc_country_id" in vals and "acc_number" in vals:
            new_vals = self.onchange_banco(
                cr, uid, [], vals["acc_number"], vals["acc_country_id"], context
            )
            if "value" in new_vals:
                if new_vals["value"].get("bank", False):
                    vals["bank"] = new_vals["value"]["bank"]

        return super(res_partner_bank, self).create(cr, uid, vals, context=context)

    def write(self, cr, uid, ids, vals, context=None):
        if "acc_number" in vals:
            for id in ids:
                bank = self.browse(cr, uid, id)
                country_id = (
                    "acc_country_id" in vals and vals["acc_country_id"] or bank.acc_country_id.id
                )
                if country_id:
                    new_vals = self.onchange_banco(
                        cr, uid, [], vals["acc_number"], country_id, context
                    )
                    if "value" in new_vals:
                        if new_vals["value"].get("bank", False):
                            vals["bank"] = new_vals["value"]["bank"]
        return super(res_partner_bank, self).write(cr, uid, ids, vals, context=context)


res_partner_bank()
