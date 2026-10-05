# -*- coding: utf-8 -*-
from __future__ import absolute_import

from osv import osv


class GiscedataSignaturaProcess(osv.osv):
    _name = 'giscedata.signatura.process'
    _inherit = 'giscedata.signatura.process'

    def send_poweremail(self, cursor, uid, ids, template_id=None, context=None):
        """Generate and immediately send the signature PowerEmail."""
        if context is None:
            context = {}
        if not isinstance(ids, (list, tuple)):
            ids = [ids]

        result = super(
            GiscedataSignaturaProcess, self
        ).send_poweremail(
            cursor, uid, ids, template_id=template_id, context=context
        )

        mailbox_obj = self.pool.get('poweremail.mailbox')
        for signature in self.browse(cursor, uid, ids, context=context):
            search_params = [
                ('reference', '=', 'giscedata.signatura.process,{}'.format(
                    signature.id
                )),
                ('template_id', '=', template_id or signature.template_id.id),
                ('folder', '=', 'outbox'),
            ]
            mail_ids = mailbox_obj.search(
                cursor, uid, search_params, context=context
            )
            if mail_ids:
                mailbox_obj.send_this_mail(
                    cursor, uid, mail_ids, context=context
                )

        return result


GiscedataSignaturaProcess()
