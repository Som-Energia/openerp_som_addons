from osv import osv
from oorq.decorators import job


class CrmLead(osv.osv):

    def move_to_error_stage(self, cursor, uid, lead_id, context=None):
        raise NotImplementedError

    @job(queue='peticions_webforms')
    def inici_proces_alta_socia_async(self, cursor, uid, lead_id, context=None):
        if context is None:
            context = {}
        savepoint = 'create_entities_{}'.format(id(cursor))
        cursor.savepoint(savepoint)
        try:
            msg = self.create_entities(cursor, uid, [lead_id], context)
        except Exception as e:
            cursor.rollback(savepoint)
            if hasattr(e, "value"):
                msg = e.value
            else:
                msg = str(e)
            self.move_to_error_stage(cursor, uid, lead_id, context)
        self.historize_msg(cursor, uid, [lead_id], msg)

    def inici_proces_alta_socia(self, cursor, uid, lead_id, context=None):
        if context is None:
            context = {}

        response_obj = self.pool.get('gisceov.contractacio.response')
        self.inici_proces_alta_socia_async(cursor, uid, lead_id, context)

        lead = self.read(cursor, uid, lead_id, [
            'polissa_id', 'partner_id', 'ref'
        ])
        response_id = response_obj.search(cursor, uid, [], limit=1)
        if response_id:
            response_id = response_id[0]
            ctx = context.copy()
            ctx['lead_id'] = lead['id']
            ctx['model'] = self._name
            template = response_obj.read(
                cursor, uid, response_id, ['rendered', 'format'], context=ctx
            )
        else:
            template = {
                'rendered': '',
                'format': 'html'
            }
        return {
            'id': lead['id'],
            'response': template
        }
