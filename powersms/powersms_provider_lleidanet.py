from __future__ import absolute_import, unicode_literals
from osv import osv, fields


class PowersmsProviderLleidaNet(osv.osv):
    _inherit = 'powersms.provider'

    def send_sms_lleida(self, cursor, uid, _id, account_id, from_name, numbers_to, body='', context=None):
        from lleida_net.sms import Client
        account_obj = self.pool.get('powersms.core_accounts')
        values = account_obj.read(cursor, uid, account_id, ['api_uname', 'api_pass'])
        c = Client(user=str(values['api_uname']), password=str(values['api_pass']))
        headers = {'content-type': 'application/x-www-form-urlencoded', 'accept': 'application/json'}
        response = c.API.post(
            headers=headers,
            resource='',
            json={
                "sms": {
                    "txt": body,
                    "dst": {
                        "num": numbers_to,
                    },
                    "src": from_name,
                }
            },
        )
        return response.result['code'] == 200 and response.result['status'] == 'Success'


PowersmsProviderLleidaNet()
