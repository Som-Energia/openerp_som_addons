from __future__ import absolute_import, unicode_literals
import base64
from osv import osv


class PowersmsProviderLleidaNet(osv.osv):
    _inherit = 'powersms.provider'

    def _get_json_body(self, number_to, message, from_name, context=None):
        special_characters = [
            u"€",
        ]
        dict_sms = {
            "txt": message,
        }
        if any(special_char in message for special_char in special_characters):
            dict_sms = {
                "charset":"utf-16",
                "data_coding":"unicode",
                "txt": base64.b64encode(message.encode('utf-16')),
            }
        json_body = {"sms": dict(dst={"num": number_to}, src=from_name, **dict_sms)}
        return json_body


    def send_sms_lleida(self, cursor, uid, _id, account_id, from_name, numbers_to, body='', files=None, context=None):
        from lleida_net.sms import Client
        account_obj = self.pool.get('powersms.core_accounts')
        values = account_obj.read(cursor, uid, account_id, ['api_uname', 'api_pass'])
        c = Client(user=str(values['api_uname']), password=str(values['api_pass']))
        headers = {'content-type': 'application/x-www-form-urlencoded', 'accept': 'application/json'}
        json_body = self._get_json_body(numbers_to, body, from_name, context)
        response = c.API.post(resource='', json=json_body, headers=headers)
        return response.result['code'] == 200 and response.result['status'] == 'Success'


PowersmsProviderLleidaNet()
