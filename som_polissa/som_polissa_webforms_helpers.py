from osv import osv

class SomPolissaWebformsHelpers(osv.osv_memory):

    _name = 'som.polissa.webforms.helpers'

    def www_get_iban(self, cursor, uid, ids, context=None):
        if context is None:
            context = {}
        if isinstance(ids, (list, set, tuple)):
            polissa_id = ids[0]
        else:
            polissa_id = ids

        pol_obj = self.pool.get('giscedata.polissa')
        bank = pol_obj.read(
            cursor, uid, polissa_id, ['bank'], context=context
        )
        iban = ''
        if bank.get('bank'):
            iban_suffix = bank['bank'][1][-4:]
            iban = '**** **** **** **** **** {}'.format(iban_suffix)
        return iban

    def www_check_iban(self, cursor, uid, iban, context=None):
        if context is None:
            context = {}

        pol_obj = self.pool.get('giscedata.polissa')
        result = pol_obj.www_check_iban(cursor, uid, iban, context=context)

        return result

    def www_set_iban(self, cursor, uid, ids, iban, context=None):
        if context is None:
            context = {}
        if isinstance(ids, (list, set, tuple)):
            polissa_id = ids[0]
        else:
            polissa_id = ids

        wiz_obj = self.pool.get('wizard.bank.account.change')

        vals = {
            'account_iban': iban,
            'print_mandate': False,
            'state': 'end'
        }

        context = {
            'active_id': polissa_id
        }

        wiz_id = wiz_obj.create(cursor, uid, vals, context=context)
        wizard_result = wiz_obj.action_bank_account_change_confirm(
            cursor, uid, [wiz_id], context=context
        )

        result = False
        if wizard_result == {}:
            result = True
        return result


SomPolissaWebformsHelpers()
