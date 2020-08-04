# -*- coding: utf-8 -*-

from osv import osv, fields
from osv.expression import OOQuery
from .erpwrapper import ErpWrapper
from dateutil.relativedelta import relativedelta
from datetime import datetime, date
from yamlns import namespace as ns
from generationkwh.isodates import isodate
from tools.translate import _
from tools import config
import re
import generationkwh.investmentmodel as gkwh
from generationkwh.investmentstate import InvestmentState, AportacionsState, GenerationkwhState
from uuid import uuid4
import netsvc
from oorq.oorq import AsyncMode
from investment_strategy import AportacionsActions, GenerationkwhActions, PartnerException, InvestmentException

# TODO: This function is duplicated in other sources
def _sqlfromfile(sqlname):
    from tools import config
    import os
    sqlfile = os.path.join(
        config['addons_path'], 'som_generationkwh',
            'sql', sqlname+'.sql')
    with open(sqlfile) as f:
        return f.read()


class Generationkwh_MailMockup(osv.osv_memory):
    _name = 'generationkwh.mailmockup'
    _columns = dict(
        log=fields.text("Mail logs"),
    )
    def isActive(self, cur, uid):
        return self.search(cur, uid, [])

    def activate(self, cur, uid):
        self.deactivate(cur, uid)
        self.create(cur, uid, {})

    def deactivate(self, cur, uid):
        ids = self.search(cur, uid, [])
        self.unlink(cur, uid, ids)

    def send_mail(self, cur, uid, values):
        mock_id = self.search(cur, uid, [])[0]
        mock = self.browse(cur, uid, mock_id)
        yamllog = ns.loads(mock.log or 'logs: []')
        yamllog.logs.append(ns.loads(values))
        mock.write(dict(log=yamllog.dump()))

    def log(self, cur, uid):
        ids = self.search(cur, uid, [])
        return self.browse(cur, uid, ids[0]).log
        
        
        


Generationkwh_MailMockup()

class GenerationkwhInvestment(osv.osv):

    _name = 'generationkwh.investment'
    _order = 'purchase_date DESC'

    _columns = dict(
        name=fields.char(
            "Nom",
            size=50,
            required=False,
            unique=True,
            help="Referència única de la inversió",
            ),
        member_id=fields.many2one(
            'somenergia.soci',
            "Inversor",
            select=True,
            required=True,
            help="Inversor que ha comprat les accions",
            ),
        nshares=fields.integer(
            "Nombre d'accions",
            required=True,
            help="Nombre d'accions comprades",
            ),
        amortized_amount=fields.float(
            "Import amortitzat",
            digits=(16, int(config['price_accuracy'])),
            required=True,
            ),
        order_date=fields.date(
            "Data de comanda",
            # required=True, # TODO: activate it after migration
            help="Quin dia es varen demanar les accions",
            ),
        signed_date=fields.date(
            "Data de firma",
            help="Quin dia es va firmar el contracte de GKWH",
            ),
        purchase_date=fields.date(
            "Data de compra",
            help="Quin dia es varen comprar les accions",
            ),
        first_effective_date=fields.date(
            "Primera data efectiva",
            help="Dia que les accions començaran a generar drets a kWh",
            ),
        last_effective_date=fields.date(
            "Darrera data efectiva",
            help="Darrer dia que les accions generaran drets a kWh",
            ),
        move_line_id=fields.many2one(
            'account.move.line',
            'Línia del moviment contable',
            select=True,
            help="Línia del moviment contable corresponent a la inversió",
            ),
        active=fields.boolean(
            "Activa",
            required=True,
            help="Permet activar o desactivar la inversió",
            ),
        draft=fields.boolean(
            "Esborrany",
            required=True,
            help="Està en esborrany si encara no s'han emés factures",
            ),
        actions_log=fields.text(
            'Història',
            required=True,
            help="Història d'esdeveniments relacionats amb la inversió en format YAML",
            ),
        log=fields.text(
            'Història',
            # TODO to be required, after develop
            #required=True,
            help="Història d'esdeveniments relacionats amb la inversió",
            ),
        emission_id=fields.many2one(
            'generationkwh.emission',
            "Emissió",
            select=True,
            #required=True, # TODO to be required
            help="Campanya d'emissió de la que forma part la inversió",
            ),
        )

    _defaults = dict(
        active=lambda *a: True,
        draft=lambda *a: True,
        amortized_amount=lambda *a: 0,
        log=lambda *a:'',
        actions_log=lambda *a: '',
    )

    def investment_actions(self, cursor, uid, id):
        inv = self.browse(cursor, uid, id)
        if str(inv.emission_id.type) == 'apo':
            return AportacionsActions(self, cursor, uid, 1)
        return GenerationkwhActions(self, cursor, uid, 1)

    def state_actions(self, cursor, uid, id, user, timestamp, **values):
        inv = self.browse(cursor, uid, id)
        if str(inv.emission_id.type) == 'apo':
            return AportacionsState(user, timestamp, **values)
        return GenerationkwhState(user, timestamp, **values)

    def list(self, cursor, uid,
            member=None,
            emission_type=None,
            context=None):
        filters = [
            ]
        if member:
            filters.append(('member_id','=',member))
        if emission_type is None:
            filters.append(('emission_id.type','=','genkwh'))
        else:
            filters.append(('emission_id.type','=',emission_type))
        ids = self.search(cursor, uid, filters)
        fields = (
            "name member_id "
            "order_date purchase_date "
            "first_effective_date last_effective_date "
            "draft active amortized_amount nshares "
            ).split()
        contracts = self.read(cursor, uid, ids, fields, context=context)
        for c in contracts:
            c['nominal_amount'] = float(c['nshares'] * gkwh.shareValue)
        return contracts

    def effective_investments_tuple(self, cursor, uid,
            member=None, start=None, end=None, emission_type=None, emission_code=None,
            context=None):
        """
            List active investments between start and end, both included,
            for the member of for any member if member is None.
            If start is not specified, it lists activated before end.
            If end is not specified, it list activated and not deactivated
            before start.
            If neither start or end are specified all investments are listed
            active or not.
        """
        Emission = self.pool.get('generationkwh.emission')
        emission_filters = []
        if emission_type is None:
            emission_filters = [('type', '=', 'genkwh')]
        else:
            emission_filters = [('type', '=', emission_type)]
        if emission_code:
            emission_filters = emission_filters + [('code', '=', emission_code)]
        emission_ids = Emission.search(cursor, uid, emission_filters)

        filters = [('emission_id', 'in', emission_ids)]

        if member: filters.append( ('member_id','=',member) )
        if end: filters += [
            ('first_effective_date','<=',end), # No activation also filtered
            ]
        if start: filters += [
            '&',
            ('first_effective_date','!=',False),
            '|',
            ('last_effective_date','>=',start),
            ('last_effective_date','=',False),
            ]

        ids = self.search(cursor, uid, filters)
        contracts = self.read(cursor, uid, ids)

        def membertopartner(member_id):
            Member = self.pool.get('somenergia.soci')

            partner_id = Member.read(
                cursor, uid, member_id, ['partner_id']
            )['partner_id'][0]
            return partner_id

        return [
            (
                c['member_id'][0],
                c['first_effective_date'] and str(c['first_effective_date']),
                c['last_effective_date'] and str(c['last_effective_date']),
                c['nshares'],
            )
            for c in sorted(contracts, key=lambda x: x['id'] )
        ]

    def effective_investments(self, cursor, uid,
            member, start, end, emission_type=None, emission_code=None,
            context=None):

        return [
            ns(
                member=member,
                firstEffectiveDate=first and isodate(first),
                lastEffectiveDate=last and isodate(last),
                shares=shares,
            )
            for member, first, last, shares
            in self.effective_investments_tuple(cursor, uid, member, start, end, emission_type, emission_code, context)
        ]

    def member_has_effective(self, cursor, uid,
            member_id, first_date, last_date, emission_type=None, emission_code=None,
            context=None):

        return len(self.effective_investments_tuple(cursor, uid,
            member_id, first_date, last_date, emission_type, emission_code, context))>0

    def _effectivePeriod(self, purchaseDate, waitingDays, expirationYears):
        if waitingDays is None:
            return None, None

        firstEffective = purchaseDate +relativedelta(days=waitingDays)

        if expirationYears is None:
            return firstEffective, None

        lastEffective = firstEffective+relativedelta(years=expirationYears)

        return firstEffective, lastEffective

    def get_investments_amount(self, cursor, uid, member_id, emission_id=None):
        search_params = [('member_id', '=', member_id), ('emission_id.type', '=', 'apo')]
        if emission_id:
            search_params.append(('emission_id', '=', emission_id))
        investment_ids = self.search(cursor, uid, search_params)

        amount = 0
        #New investments
        for id in investment_ids:
            amount += self.read(cursor, uid, id, ['nshares'])['nshares'] * gkwh.shareValue

        if emission_id: #Avoid old investments amount
            return amount

        #START Old investments (remove when migrated)
        Member = self.pool.get('somenergia.soci')
        MoveLine = self.pool.get('account.move.line')
        Account = self.pool.get('account.account')
        aportacionsAccountPrefix = '163000'

        if member_id is None:
            accountDomain = [('code','ilike',aportacionsAccountPrefix+'%')]
        else:
            memberCodes = Member.read(cursor, uid, member_id, ['ref'])
            accountCodes = aportacionsAccountPrefix + memberCodes['ref'][1:]
            accountDomain = [ ('code','ilike',accountCodes)]
        accountId = Account.search(cursor, uid, accountDomain)

        if not accountId: #No Old investments
            return amount

        movelinefilter = [
            ('account_id', 'in', accountId),
            ('period_id.special', '=', False),
            ]

        movelinesids = MoveLine.search(
            cursor, uid, movelinefilter,
            order='date_created asc, id asc',
            )

        investment_ids = []

        contextWithInactives = dict({}, active_test=False)

        for line in MoveLine.browse(cursor, uid, movelinesids):
            # Filter out already converted move lines
            if self.search(cursor, uid,
                [('move_line_id','=',line.id)],
                context=dict({}, active_test=False),
            ):
                continue

            partnerid = line.partner_id.id
            if not partnerid:
                # Handle cases with no partner_id
                membercode = int(line.account_id.code[4:])
                domain = [('ref', 'ilike', '%'+str(membercode).zfill(6))]
            else:
                domain = [('partner_id', '=', partnerid)]

            members = Member.search(cursor, uid, domain, context=contextWithInactives)
            if not members:
                print (
                    "No existeix el soci de la linia comptable "
                    "id {l.id} {l.date_created} partner {l.partner_id.name} "
                    "ac {l.account_id.name}, {l.credit} -{l.debit}  {d}"
                    .format(l=line, d=domain))
                continue

            member_id = members[0]

            amount += line.credit-line.debit
        #END Old investments (remove when migrated)

        return amount

    def check_investment_creation(self, cursor, uid, partner_id, investment_code, investment_amount):
        return investment_amount <= self.get_max_investment(cursor, uid, partner_id, investment_code)

    def get_max_investment(self, cursor, uid, partner_id, investment_code):
        Member = self.pool.get('somenergia.soci')
        Emission = self.pool.get('generationkwh.emission')
        current_date = datetime.now()

        emission_id = Emission.search(cursor, uid, [('code', '=', investment_code), ('state', '=', 'open')])
        if not emission_id:
            raise InvestmentException("Emission closed or not exist")

        emission_data = Emission.read(cursor, uid, emission_id[0], ['amount_emission','limited_period_amount','limited_period_end_date','current_total_amount_invested', 'start_date', 'end_date'])

        if emission_data['start_date'] and datetime.strptime(emission_data['start_date'],'%Y-%m-%d') > current_date:
            raise InvestmentException("Emission not open yet")
        if emission_data['end_date'] and datetime.strptime(emission_data['end_date'],'%Y-%m-%d') < current_date:
            raise InvestmentException("Emission closed")
        if emission_data['amount_emission'] <= emission_data['current_total_amount_invested']:
            raise InvestmentException("Emission completed")

        member_id = Member.search(cursor, uid, [('partner_id','=',partner_id)])[0]
        amount_investments = self.get_investments_amount(cursor, uid, member_id)

        #Check legal limit 100.000
        max_amount = gkwh.maxAmountInvested - amount_investments

        #Check emission limit <= emission_data['amount_emission']
        max_amount_available = emission_data['amount_emission'] - emission_data['current_total_amount_invested']

        #Check emission first week limit
        limited_period_amount = max_amount
        amount_investments_of_emission = self.get_investments_amount(cursor, uid, member_id, emission_id)
        if emission_data['limited_period_amount'] and \
                current_date <= datetime.strptime(emission_data['limited_period_end_date'], '%Y-%m-%d'):
                limited_period_amount = emission_data['limited_period_amount'] - amount_investments_of_emission

        min_amount = min(max_amount, max_amount_available, limited_period_amount)
        return min_amount if min_amount >= 0 else 0

    def create_from_accounting(self, cursor, uid,
            member_id, start, stop, waitingDays, expirationYears,
            context=None):
        """
            Takes accounting information and generates GenkWh investments
            purchased among start and stop dates for the indicated member.
            If waitingDays is not None, activation date is set those
            days after the purchase date.
            If expirationYears is not None, expiration date is set, those
            years after the activation date.
        """

        Account = self.pool.get('account.account')
        MoveLine = self.pool.get('account.move.line')
        Member = self.pool.get('somenergia.soci')
        generationAccountPrefix = '163500'

        if member_id is None:
            accountDomain = [('code','ilike',generationAccountPrefix+'%')]
        else:
            member_ids = [member_id] if type(member_id) is int else member_id
            memberCodes = Member.read(cursor, uid, member_ids, ['ref'])
            accountCodes = [
                generationAccountPrefix + memberCode['ref'][1:]
                for memberCode in memberCodes
                ]

            accountDomain = [ ('code','in',accountCodes)]
        accountIds = Account.search(cursor, uid, accountDomain)

        movelinefilter = [
            ('account_id', 'in', accountIds),
            ('period_id.special', '=', False),
            ]
        if stop: movelinefilter.append(('date_created', '<=', str(stop)))
        if start: movelinefilter.append(('date_created', '>=', str(start)))

        movelinesids = MoveLine.search(
            cursor, uid, movelinefilter,
            order='date_created asc, id asc',
            context=context
            )

        investment_ids = []

        contextWithInactives = dict(context or {}, active_test=False)

        for line in MoveLine.browse(cursor, uid, movelinesids, context):
            # Filter out already converted move lines
            if self.search(cursor, uid,
                [('move_line_id','=',line.id)],
                context=dict(context or {}, active_test=False),
            ):
                continue

            partnerid = line.partner_id.id
            if not partnerid:
                # Handle cases with no partner_id
                membercode = int(line.account_id.code[4:])
                domain = [('ref', 'ilike', '%'+str(membercode).zfill(6))]
            else:
                domain = [('partner_id', '=', partnerid)]

            members = Member.search(cursor, uid, domain, context=contextWithInactives)
            if not members:
                print (
                    "No existeix el soci de la linia comptable "
                    "id {l.id} {l.date_created} partner {l.partner_id.name} "
                    "ac {l.account_id.name}, {l.credit} -{l.debit}  {d}"
                    .format(l=line, d=domain))
                continue

            member_id = members[0]

            activation, lastDateEffective = self._effectivePeriod(
                isodate(line.date_created),
                waitingDays, expirationYears)

            investment_id = self.create(cursor, uid, dict(
                member_id=member_id,
                nshares=(line.credit-line.debit)//gkwh.shareValue,
                purchase_date=line.date_created,
                first_effective_date=activation,
                last_effective_date=lastDateEffective,
                move_line_id=line.id,
                ))

            investment_ids.append(investment_id)

        return sorted(investment_ids)


    def set_effective(self, cursor, uid,
            start, stop, waitingDays, expirationYears, force,
            context=None):
        """
            Makes effective the investments purchased between start and stop
            included for the period waitingDays from the purchase date
            for expirationYears.
            If force is not active, already effective investments are
            ignored.
        """
        criteria = []
        if not force: criteria.append(('first_effective_date', '=', False))
        if stop: criteria.append(('purchase_date', '<=', str(stop)))
        if start: criteria.append(('purchase_date', '>=', str(start)))

        investments_id = self.search(cursor, uid, criteria, context=context)
        investments = self.read(
            cursor, uid, investments_id, ['purchase_date'], context=context
        )

        for investment in investments:

            first,last = self._effectivePeriod(
                isodate(investment['purchase_date']),
                waitingDays, expirationYears)

            self.write(
                cursor, uid, investment['id'], dict(
                    first_effective_date = first,
                    last_effective_date = last,
                ), context=context
            )

    def _set_active(self, cursor, uid, inv_id, value, context=None):
        """ Sets active in investement to (de)activate it
        :param inv_id: investment_id
        :param value: 1 to activate 0 to deactivate
        :param context:
        :return: setted value
        """
        actions = {
            0: 'Desactivat',
            1: 'Activat'
        }
        action_name = actions[value]
        current_value = self.read(
            cursor, uid, inv_id, ['active'], context
        )['active']

        if current_value != bool(value):
            self.write(
                cursor, uid, [inv_id], {'active': value}, context=context
            )
            txt = _(u"S'ha {0} la inversió {1}").format(action_name, inv_id)
            self.log_action(cursor, uid, inv_id, txt, context=context)

        return value

    def activate(self, cursor, uid, inv_id, context=None):
        return self._set_active(cursor, uid, inv_id, 1, context=None)

    def deactivate(self, cursor, uid, inv_id, context=None):
        return self._set_active(cursor, uid, inv_id, 0, context=None)

    def dropAll(self, cursor, uid, context=None):
        """
            Remove all investment. Use just for testing.
        """
        ids = self.search(cursor, uid, [],
            context=dict(context or {}, active_test=False))
        self.unlink(cursor,uid,ids,context)

    def log_action(self, cursor, uid, inv_id, text, context=None):
        """
        :param text: Text to log
        :return: added text
        """
        Member = self.pool.get('somenergia.soci')

        member_id = self.read(
            cursor, uid, inv_id, ['member_id']
        )['member_id'][0]
        return Member.add_gkwh_comment(cursor, uid, member_id, text)

    def pending_amortization_summary(self, cursor, uid, current_date, ids=None):

        inv_ids = ids or self.search(cursor, uid, [('emission_id.type','=','genkwh')], order='id')
        invs = self.read(cursor, uid, inv_ids, [
            'purchase_date',
            'amortized_amount',
            'nshares',
            ])
        result = []
        for inv in invs:
            invstate = InvestmentState('Ignored', datetime.now(),
                amortized_amount = inv['amortized_amount'],
                purchase_date = isodate(inv['purchase_date']),
                nominal_amount = gkwh.shareValue*inv['nshares'],
            )
            for pending in invstate.pendingAmortizations(isodate(current_date)):
                (
                    amortization_number,
                    amortization_total_number,
                    amortization_date,
                    to_be_amortized,
                ) = pending
                result.append(to_be_amortized)

        return len(result), sum(result)


    def get_dayshares_investmentyear(self, cursor, uid, inv_obj, start_date, end_date):
        start_datetime = datetime.strptime(start_date,'%Y-%m-%d')
        end_datetime = datetime.strptime(end_date,'%Y-%m-%d')
        first_effective_datetime = datetime.strptime(inv_obj['first_effective_date'],'%Y-%m-%d')
        last_effective_datetime = datetime.strptime(inv_obj['last_effective_date'],'%Y-%m-%d')

        if start_datetime < first_effective_datetime:
            start_datetime = first_effective_datetime
        if end_datetime > last_effective_datetime:
            end_datetime = last_effective_datetime
        dayShares = (end_datetime - start_datetime).days * inv_obj['nshares']
        return dayShares if dayShares > 0 else 0

    def get_total_saving_partner(self, cursor, uid, partner_id, start_date, end_date):
        """
        :param partner_id: In this function, partner_id is the partner of Investment, not the Parnter of Invoice.
        """
        GenerationkwhInvoiceLineOwner = self.pool.get('generationkwh.invoice.line.owner')
        q = OOQuery(GenerationkwhInvoiceLineOwner, cursor, uid)

        total_amount_saving = 0
        search_params = [('owner_id.id', '=', partner_id),
                         ('factura_id.invoice_id.date_invoice', '>=', start_date),
                         ('factura_id.invoice_id.date_invoice', '<=', end_date)]

        sql = q.select(['saving_gkw_amount','factura_line_id']).where(search_params)
        cursor.execute(*sql)
        total_amount_saving = 0
        result = cursor.dictfetchall()
        result = {d['factura_line_id']: d['saving_gkw_amount'] for d in result}

        if result:
            total_amount_saving = sum(result.values())

        return total_amount_saving


    def get_irpf_amounts(self, cursor, uid, investment_id, member_id, year=None):
        Invoice = self.pool.get('account.invoice')
        InvoiceLine = self.pool.get('account.invoice.line')
        GenerationkwhInvoiceLineOwner = self.pool.get('generationkwh.invoice.line.owner')
        Soci = self.pool.get('somenergia.soci')
        partner_id = Soci.read(cursor, uid, member_id, ['partner_id'])['partner_id'][0]

        #obtenir total factures Generation any anterior
        if not year:
            today = datetime.today()#Get date
            year = today.year - 1
        if year == 2018:
            return 0
        start_date = str(year) + '-01-01'
        end_date = str(year) + '-12-31'
        total_amount_saving = self.get_total_saving_partner(cursor, uid, partner_id, start_date, end_date)

        #obtenir total accions inverions
        total_dayshares_year = 1
        list_inv_id = self.search(cursor, uid, [('member_id','=',member_id), ('emission_id.type','=','genkwh')])
        for inv_id in list_inv_id:
            inv_obj = self.read(cursor, uid, inv_id, ['first_effective_date','last_effective_date','nshares', 'name'])
            if inv_obj['first_effective_date']:
                total_dayshares_year += self.get_dayshares_investmentyear(cursor, uid, inv_obj, start_date, end_date)

        #regla de tres amb accions inversió actual
        inv_actual = self.read(cursor, uid, investment_id, ['first_effective_date','last_effective_date','nshares'])
        daysharesactual = self.get_dayshares_investmentyear(cursor, uid, inv_actual, start_date, end_date)

        ret_values = {}
        ret_values['irpf_amount'] = round((daysharesactual * total_amount_saving / total_dayshares_year) * gkwh.irpfTaxValue,2)
        ret_values['irpf_saving'] = total_amount_saving

        return ret_values


    def amortize(self, cursor, uid, current_date, ids=None, context=None):
        User = self.pool.get('res.users')
        Soci = self.pool.get('somenergia.soci')
        username = User.read(cursor, uid, uid, ['name'])['name']
        amortization_ids = []
        amortization_errors = []

        investment_ids = ids or self.search(cursor, uid, [('emission_id.type','=','genkwh')], order='id')
        investments = self.read(cursor, uid, investment_ids, [
            'purchase_date',
            'amortized_amount',
            'nshares',
            'log',
            'actions_log',
            'member_id',
            ])
        for inv in investments:
            investment_id = inv['id']
            invstate = InvestmentState(username, datetime.now(),
                log = inv['log'],
                amortized_amount = inv['amortized_amount'],
                purchase_date = isodate(inv['purchase_date']),
                nominal_amount = gkwh.shareValue*inv['nshares'],
            )

            for pending in invstate.pendingAmortizations(isodate(current_date)):
                (
                    amortization_number,
                    amortization_total_number,
                    amortization_date,
                    to_be_amortized,
                ) = pending
                amortization_date = amortization_date or False
                irpf_amount = self.get_irpf_amounts(cursor, uid, investment_id, inv['member_id'][0])['irpf_amount']

                amortization_id, error = self.create_amortization_invoice(cursor, uid,
                        investment_id = investment_id,
                        amortization_date = amortization_date,
                        to_be_amortized = to_be_amortized,
                        amortization_number = amortization_number,
                        amortization_total_number = amortization_total_number,
                        irpf_amount = irpf_amount,
                        )

                if error:
                    amortization_errors.append(error)
                    continue
                amortization_ids.append(amortization_id)

                invstate.amortize(
                    date = amortization_date,
                    to_be_amortized = to_be_amortized,
                    )
                self.write(cursor, uid, investment_id, dict(
                    invstate.erpChanges(),
                ), context)

                self.open_invoices(cursor, uid, [amortization_id])
                self.invoices_to_payment_order(cursor, uid,
                    [amortization_id], gkwh.amortizationPaymentMode)
                self.send_mail(cursor, uid, amortization_id,
                    'account.invoice', '_mail_amortitzacio', investment_id)

        return amortization_ids, amortization_errors

    def create_amortization_invoice(self, cursor, uid,
            investment_id, amortization_date, to_be_amortized,
            amortization_number,amortization_total_number,
            irpf_amount, context=None):

        Partner = self.pool.get('res.partner')
        Product = self.pool.get('product.product')
        Invoice = self.pool.get('account.invoice')
        InvoiceLine = self.pool.get('account.invoice.line')
        PaymentType = self.pool.get('payment.type')
        Journal = self.pool.get('account.journal')

        investment = self.browse(cursor, uid, investment_id)

        date_invoice = str(date.today())
        year = amortization_date.split('-')[0]

        # The partner
        partner_id = investment.member_id.partner_id.id
        partner = Partner.browse(cursor, uid, partner_id)

        # Get or create partner specific accounts
        if not partner.property_account_liquidacio:
            partner.button_assign_acc_410()
        if not partner.property_account_gkwh:
            partner.button_assign_acc_1635()

        if (
            not partner.property_account_gkwh or
            not partner.property_account_liquidacio
            ):
            partner = partner.browse()[0]

        # The product
        product_id = Product.search(cursor, uid, [
            ('default_code','=', self.investment_actions(cursor, uid, investment_id).productCode),
            ])[0]

        product = Product.browse(cursor, uid, product_id)
        product_uom_id = product.uom_id.id

        # The journal
        journal_id = Journal.search(cursor, uid, [
            ('code','=',self.investment_actions(cursor, uid, investment_id).journalCode),
            ])[0]

        # The payment type
        payment_type_id = PaymentType.search(cursor, uid, [
            ('code', '=', 'TRANSFERENCIA_CSB'),
            ])[0]

        errors = []
        def error(message):
            errors.append(message)

        # Check if exist bank account
        if not partner.bank_inversions:
            return 0, u"Inversió {0}: El partner {1} no té informat un compte corrent\n".format(investment.id, partner.name)

        # Memento of mutable data
        investmentMemento = ns()
        investmentMemento.pendingCapital = investment.nshares * gkwh.shareValue - investment.amortized_amount - to_be_amortized
        investmentMemento.amortizationDate = amortization_date
        investmentMemento.amortizationNumber = amortization_number
        investmentMemento.amortizationTotalNumber = amortization_total_number
        investmentMemento.investmentId = investment_id
        investmentMemento.investmentName = investment.name
        investmentMemento.investmentPurchaseDate = investment.purchase_date
        investmentMemento.investmentLastEffectiveDate = investment.last_effective_date
        investmentMemento.investmentInitialAmount = investment.nshares * gkwh.shareValue

        invoice_name = '%s-AMOR%s' % (
            # TODO: Remove the GENKWHID stuff when fully migrated, error instead
            investment.name or 'GENKWHID{}'.format(investment.id),
            year,
            )
        # Ensure unique amortization
        existingInvoice = Invoice.search(cursor,uid,[
            ('name','=', invoice_name),
            ])

        if existingInvoice:
            return 0, u"Inversió {0}: L'amortització {1} ja existeix".format(investment.id, invoice_name)

        # Default invoice fields for given partne
        vals = {}
        vals.update(Invoice.onchange_partner_id(
            cursor, uid, [], 'in_invoice', partner_id,
        ).get('value', {}))

        vals.update({
            'partner_id': partner_id,
            'type': 'in_invoice',
            'name': invoice_name,
            'number': invoice_name,
            'journal_id': journal_id,
            'account_id': partner.property_account_liquidacio.id,
            'partner_bank': partner.bank_inversions.id,
            'payment_type': payment_type_id,
            #'check_total': to_be_amortized + (irpf_amount * -1),
            # TODO: Remove the GENKWHID stuff when fully migrated, error instead
            'origin': investment.name or 'GENKWHID{}'.format(investment.id),
            'reference': invoice_name,
            'date_invoice': date_invoice,
        })

        invoice_id = Invoice.create(cursor, uid, vals)
        Invoice.write(cursor,uid, invoice_id,{'sii_to_send':False})

        line = dict(
            InvoiceLine.product_id_change(cursor, uid, [],
                product=product_id,
                uom=product_uom_id,
                partner_id=partner_id,
                type='in_invoice',
                ).get('value', {}),
            invoice_id = invoice_id,
            name = _('Amortització fins a {amortization_date:%d/%m/%Y} de {investment} ').format(
                investment = investment.name,
                amortization_date = datetime.strptime(amortization_date,'%Y-%m-%d'),
                ),
            note = investmentMemento.dump(),
            quantity = 1,
            price_unit = to_be_amortized,
            product_id = product_id,
            # partner specific account, was generic from product
            account_id = partner.property_account_gkwh.id,
        )

        # no taxes apply
        line['invoice_line_tax_id'] = [
            (6, 0, line.get('invoice_line_tax_id', []))
        ]
        InvoiceLine.create(cursor, uid, line)

        retention_date = isodate(amortization_date) - relativedelta(years=1)
        self.irpfRetentionLine(cursor, uid, investment, irpf_amount, invoice_id, retention_date, investmentMemento)

        Invoice.write(cursor,uid, invoice_id, dict(
            check_total = to_be_amortized - irpf_amount,
            ))

        return invoice_id, errors

    def irpfRetentionLine(self, cursor, uid, investment, irpf_amount, invoice_id, retention_date, investmentMemento):
        if not irpf_amount: return

        Product = self.pool.get('product.product')
        InvoiceLine = self.pool.get('account.invoice.line')

        partner_id = investment.member_id.partner_id.id

        product_irpf_id = Product.search(cursor, uid, [
            ('default_code','=', gkwh.irpfProductCode),
            ])[0]
        product_irpf = Product.browse(cursor, uid, product_irpf_id)
        product_uom_irpf_id = product_irpf.uom_id.id

        line = dict(
            InvoiceLine.product_id_change(cursor, uid, [],
                product=product_irpf_id,
                uom=product_uom_irpf_id,
                partner_id=partner_id,
                type='in_invoice',
                ).get('value', {}),
            invoice_id = invoice_id,
            name = _('Retenció IRPF sobre l\'estalvi del Generationkwh de {retention_date:%Y} de {investment} ').format(
                investment = investment.name,
                retention_date = retention_date,
                ),
            note = investmentMemento.dump(),
            quantity = 1,
            price_unit = -irpf_amount,
            product_id = product_irpf_id,
        )

        # no taxes apply
        line['invoice_line_tax_id'] = [
            (6, 0, line.get('invoice_line_tax_id', []))
        ]
        InvoiceLine.create(cursor, uid, line)


    # TODO: Move to res.partner
    def get_default_country(self, cursor, uid):
        ResCountry = self.pool.get('res.country')
        return ResCountry.search(cursor, uid, [('code', '=', 'ES')])[0]

    # TODO: Move to res.partner
    def check_spanish_account(self, cursor, uid, account):
        spain = self.get_default_country(cursor, uid)
        ResPartnerBank = self.pool.get('res.partner.bank')
        ResBank = self.pool.get('res.bank')
        vals = ResPartnerBank.onchange_banco(cursor, uid, [], account, int(spain), {})
        if 'warning' in vals:
            # TODO: Use vals['warning']['message']
            # TODO: Would require use a context with locale
            return False

        if 'value' not in vals or not vals['value']:
            # TODO: Not string or country not ES... needed?
            return False

        result = {}

        if 'bank' in vals['value']:
            bank = ResBank.read(cursor, uid, vals['value']['bank'])
            result['bank_name'] = bank['name']
        if 'acc_number' in vals['value']:
            result['acc_number'] = vals['value']['acc_number']
        return result

    # TODO: Move to res.partner
    def clean_iban(self, cursor, uid, iban):
        '''This function removes all characters from given 'iban' that isn't a
        alpha numeric and converts it to upper case.'''
        return "".join(
            char.upper()
            for char in iban
            if char.isalnum()
            )

    # TODO: Move to res.partner
    # TODO: Foreign IBANs accepted? make CCC check conditional
    # TODO: Foreign IBANs not accepted? should start by ES
    # TODO: Consider using stdnum
    def check_iban(self, cursor, uid, iban):
        """
        Returns the clean iban if the iban is correct, or None otherwise.
        """
        iban = self.clean_iban(cursor, uid, iban)
        if not re.match('[A-Z]{2}[0-9]{2}', iban[:4]):
            return False

        ResPartnerBank = self.pool.get('res.partner.bank')
        generatedIban = ResPartnerBank.calculate_iban(cursor, uid,
            iban[4:], iban[:2])
        if generatedIban != iban:
            return False

        # TODO: Just if starts with ES!!
        bank = self.check_spanish_account(cursor, uid, iban[4:])
        if bank is False:
            return False

        return iban

    # TODO: Move to res.partner
    def get_or_create_partner_bank(self, cursor, uid,
            partner_id, iban):
        """
        If such an iban is alredy a bank account for the
        partner, it returns it.
        If not it creates it and returns the new one.
        """
        ResPartnerBank = self.pool.get('res.partner.bank')
        country_id = self.get_default_country(cursor, uid)

        bank_ids = ResPartnerBank.search(cursor, uid, [
            ('iban', '=', iban),
            ('partner_id','=', partner_id),
            ])
        if bank_ids: return bank_ids[0]
        vals = ResPartnerBank.onchange_banco(cursor, uid,
            [], iban[4:], country_id, {})
        vals = vals['value']
        vals.update({
            'name': '',
            'state': 'iban',
            'iban': iban,
            'partner_id': partner_id,
            'country_id': country_id,
            'acc_country_id': country_id,
        })
        return ResPartnerBank.create(cursor, uid, vals)

    def create_from_form(self, cursor, uid,
            partner_id, order_date, amount_in_euros, ip, iban, emission=None,
            context=None):
        investment_actions = GenerationkwhActions(self, cursor, uid, 1)
        #Compatibility 'emissio_apo'
        if emission == 'emissio_apo' or (emission and 'APO_' in emission) :
            investment_actions = AportacionsActions(self, cursor, uid, 1)
        investment_id = investment_actions.create_from_form(cursor, uid,
                partner_id, order_date, amount_in_euros, ip, iban, emission,
                context)
        return investment_id

    def create_from_transfer(self, cursor, uid,
            investment_id, new_partner_id, transfer_date, iban,
            context=None):

        #Obtenir dades inversio (total invertit, total amortiztzat/pendent, data original...)
        old_investment = self.read(cursor, uid, investment_id)
        if old_investment['draft'] :
            raise Exception("Investment in draft, so not transferible")
        if not old_investment['active']:
            raise Exception("Investment not active")
        if old_investment['amortized_amount'] >= old_investment['nshares']*gkwh.shareValue :
            raise Exception("Amount to return = 0, not transferible")

        #Comprovar dades del partner al qual es vol tranferir (existeix, soci, iban, compte inversions..)
        Soci = self.pool.get('somenergia.soci')
        member_ids = Soci.search(cursor, uid, [
                ('partner_id','=', new_partner_id)
                ])
        if not member_ids:
            raise Exception("Destination partner is not a member")

        ResPartner = self.pool.get('res.partner')
        new_partner = ResPartner.browse(cursor, uid, new_partner_id)
        if not new_partner.property_account_gkwh.id:
            new_partner.button_assign_acc_1635()
            new_partner = ResPartner.browse(cursor, uid, new_partner_id)
            print "Nou partner: Creat compte comptable de Generation: ", new_partner.property_account_gkwh
        if not new_partner.bank_inversions:
            print "Nou banc per aquest partner: Cal definir un IBAN de banc inversions"
            bank_id = self.get_or_create_partner_bank(cursor, uid,
                        new_partner_id, iban)
            ResPartner.write(cursor, uid, new_partner_id, dict(
                bank_inversions = bank_id,),context)

        #Crear inversio
        ResUser = self.pool.get('res.users')
        user = ResUser.read(cursor, uid, uid, ['name'])
        IrSequence = self.pool.get('ir.sequence')
        name = IrSequence.get_next(cursor,uid,'som.inversions.gkwh')

        inv = InvestmentState(user['name'], datetime.now(),
                name = old_investment['name'],
                purchase_date = old_investment['purchase_date'],
                first_effective_date = old_investment['first_effective_date'],
                last_effective_date = old_investment['last_effective_date'],
                order_date = old_investment['order_date'],
                log = old_investment['log'],
        )
        inv_old = InvestmentState(user['name'], datetime.now(),
                name = old_investment['name'],
                purchase_date = isodate(old_investment['purchase_date']),
                first_effective_date = isodate(old_investment['first_effective_date']),
                paid_amount = old_investment['nshares']*gkwh.shareValue,
                nominal_amount = old_investment['nshares']*gkwh.shareValue,
                amortized_amount = old_investment['amortized_amount'],
                last_effective_date = old_investment['last_effective_date'],
                order_date = old_investment['order_date'],
                log = old_investment['log'],
        )
        amount = old_investment['nshares']*gkwh.shareValue - old_investment['amortized_amount']
        to_partner_name = new_partner_id #TODO Get partner name from id
        move_line_id = 1
        origin = self.browse(cursor, uid, investment_id)
        origin_partner_name = origin.member_id.name

        transferred = inv.receiveTransfer(
            name = name,
            date = isodate(transfer_date),
            amount = amount,
            origin = inv_old,
            origin_partner_name = origin_partner_name,
            move_line_id = move_line_id
        )
        new_investment_id = self.create(cursor, uid, dict(
            inv.erpChanges(),
            member_id = member_ids[0],
            nshares = old_investment['nshares'],
            emission_id = old_investment['emission_id'][0]
        ), context)

        new_investment = self.browse(cursor, uid, new_investment_id)

        emited = inv_old.emitTransfer(
            date = isodate(transfer_date),
            amount = amount,
            to_name = new_investment.name,
            to_partner_name = new_investment.member_id.name,
            move_line_id = move_line_id,
        )
        self.write(cursor, uid, investment_id, inv_old.erpChanges())

        #Modificar dates
        self.mark_as_invoiced(cursor, uid, new_investment_id)
        #Crear moviment 1635old 1635new
        old_partner = Soci.read(cursor, uid, old_investment['member_id'][0])
        self.move_line_when_tranfer(cursor, uid, old_partner['id'], new_partner_id, old_partner['property_account_gkwh'][0], new_partner.property_account_gkwh.id, amount)

        #Enviar correu cofirmació?
        return new_investment_id

    def mark_as_signed(self, cursor, uid, id, signed_date=None):
        """
        The investment after ordered is kept in 'draft' state,
        until the customer sign the contract.
        """

        Soci = self.pool.get('somenergia.soci')
        User = self.pool.get('res.users')
        user = User.read(cursor, uid, uid, ['name'])
        inversio = self.read(cursor, uid, id, [
            'log',
            'draft',
            'actions_log',
            'signed_date',
            ])
        ResUser = self.pool.get('res.users')
        user = ResUser.read(cursor, uid, uid, ['name'])

        if not signed_date:
            signed_date = str(datetime.today().date())

        inv = InvestmentState(user['name'], datetime.now(),
            log = inversio['log'],
            signed_date = inversio['signed_date'],
        )
        inv.sign(signed_date)
        self.write(cursor, uid, id, inv.erpChanges())

    def move_line_when_tranfer(self, cursor, uid, partner_id_from, partner_id_to,
            account_id_from, account_id_to, amount):
        ResPartner = self.pool.get('res.partner')
        AccountMove = self.pool.get('account.move')
        AccountMoveLine = self.pool.get('account.move.line')
        Journal = self.pool.get('account.journal')
        Period = self.pool.get('account.period')

        # The journal
        journal_id = Journal.search(cursor, uid, [
            ('code','=', gkwh.journalCode),
            ])[0]

        today = datetime.today()#Get date

        # The period
        period_name = today.strftime('%m/%Y')
        period_id = Period.search(cursor, uid, [
            ('name', '=', period_name),
            ])[0]

        id_move = AccountMove.create(cursor, uid, {
            'journal_id': journal_id,
            'date': today,
            'amount': amount,
            'name': 'Transfer',
            'period_id': period_id,
            'ref': '0000',
            'to_check': False,
            'type': 'journal_voucher',
        })
        id_moveline_debit = AccountMoveLine.create(cursor, uid, {
            'journal_id': journal_id,
            'period_id': period_id,
            'account_id': account_id_from,
            'name': 'Emet transfer inversió',
            'ref': '',
            'debit': amount,
            'state': 'valid',
            'amount_currency': 0,
            'parnter_id': partner_id_from,
            'tax_amount': 0,
            'credit': 0,
            'quantity': 0,
            'move_id': id_move,
        })
        id_moveline_credit = AccountMoveLine.create(cursor, uid, {
            'journal_id': journal_id,
            'period_id': period_id,
            'account_id': account_id_to,
            'name': 'Rep transfer inversió',
            'ref': '',
            'debit': 0,
            'state': 'valid',
            'amount_currency': 0,
            'parnter_id': partner_id_to,
            'tax_amount': 0,
            'credit': amount,
            'quantity': 0,
            'move_id': id_move,
        })

        return id_move, id_moveline_debit, id_moveline_credit

    def get_or_create_payment_mandate(self, cursor, uid, partner_id, iban, purpose, creditor_code):
        """
        Searches an active payment (SEPA) mandate for
        the partner, iban and purpose (communication).
        If none is found, a new one is created.
        """
        ResPartner = self.pool.get("res.partner")
        PaymentMandate = self.pool.get("payment.mandate")
        ResPartnerAddress = self.pool.get("res.partner.address")
        partner = ResPartner.read(cursor, uid, partner_id, ['address', 'name', 'vat'])
        search_params = [
            ('debtor_iban', '=', iban),
            ('debtor_vat', '=', partner['vat']),
            ('date_end', '=', False),
            ('reference', '=', 'res.partner,{}'.format(partner_id)),
            ('notes', '=', purpose),
        ]

        mandate_ids = PaymentMandate.search(cursor, uid, search_params)
        if mandate_ids: return mandate_ids[0]

        adr = ResPartnerAddress.read(cursor, uid, partner['address'][0], ['nv', 'state_id'])
        mandate_name = uuid4().hex
        mandate_date = datetime.now()
        vals = {
            'debtor_name': partner['name'],
            'debtor_vat': partner['vat'],
            'debtor_address': adr['nv'],
            # TODO: No test covers case having no state
            'debtor_state': adr['state_id'] and adr['state_id'][1] or '',
            'debtor_country': self.get_default_country(cursor, uid),
            'debtor_iban': iban,
            'reference': 'res.partner,{}'.format(partner_id),
            'notes': purpose,
            'name': mandate_name,
            'creditor_code': creditor_code,
            'date': mandate_date.strftime('%Y-%m-%d')
        }
        return PaymentMandate.create(cursor, uid, vals)

    def get_or_create_open_payment_order(self, cursor, uid,  mode_name, use_invoice = False):
        """
        Searches an existing payment order (remesa)
        with the proper payment mode and still in draft.
        If none is found, a new one gets created.
        """
        PaymentMode = self.pool.get('payment.mode')
        payment_mode_ids = PaymentMode.search(cursor, uid, [
            ('name', '=', mode_name),
            ])

        if not payment_mode_ids: return False

        PaymentOrder = self.pool.get('payment.order')
        payment_orders = PaymentOrder.search(cursor, uid, [
            ('mode', '=', payment_mode_ids[0]),
            ('state', '=', 'draft'),
            ])
        if payment_orders:
            return payment_orders[0]

        PaymentType = self.pool.get('payment.type')
        payable_type_id = PaymentType.search(cursor, uid, [
            ('code', '=', 'TRANSFERENCIA_CSB'),
            ])[0]

        paymentmode = PaymentMode.read(cursor, uid, payment_mode_ids[0])
        order_moves = 'bank-statement' if use_invoice else 'direct-payment'
        order_type = 'payable' if paymentmode['type'][0] == payable_type_id else 'receivable'

        return PaymentOrder.create(cursor, uid, dict(
            date_prefered = 'fixed',
            user_id = uid,
            state = 'draft',
            mode = payment_mode_ids[0],
            type = order_type,
            create_account_moves = order_moves,
        ))

    def mark_as_invoiced(self, cursor, uid, id):
        """
        The investment after ordered is kept in 'draft' state,
        until we create the payment invoice and include the invoice
        in a payment order, when it becomes unpaid.
        This method finishes de draft state.
        NOT INTENDED TO BE CALLED DIRECTLY, as it does not
        create the invoice itself.
        """

        Soci = self.pool.get('somenergia.soci')
        User = self.pool.get('res.users')
        user = User.read(cursor, uid, uid, ['name'])
        inversio = self.read(cursor, uid, id, [
            'log',
            'draft',
            'actions_log',
            ])
        ResUser = self.pool.get('res.users')
        user = ResUser.read(cursor, uid, uid, ['name'])

        inv = InvestmentState(user['name'], datetime.now(),
            log = inversio['log'],
            draft = inversio['draft'],
        )
        inv.invoice()
        self.write(cursor, uid, id, inv.erpChanges())

    def mark_as_paid(self, cursor, uid, ids, purchase_date, movementline_id=None):
        Soci = self.pool.get('somenergia.soci')
        ResUser = self.pool.get('res.users')
        Emission = self.pool.get('generationkwh.emission')
        user = ResUser.read(cursor, uid, uid, ['name'])
        for id in ids:
            inversio = self.read(cursor, uid, id, [
                'log',
                'actions_log',
                'nshares',
                'member_id',
                'purchase_date',
                'draft',
                'emission_id',
                ])
            user = ResUser.read(cursor, uid, uid, ['name'])
            nominal_amount = inversio['nshares']*gkwh.shareValue
            if movementline_id:
                MoveLine = self.pool.get('account.move.line')
                moveline = ns(MoveLine.read(cursor, uid, movementline_id, []))
                amount = moveline.credit - moveline.debit
            else:
                amount = nominal_amount

            inv = self.state_actions(cursor, uid, id, user['name'], datetime.now(),
                log = inversio['log'],
                nominal_amount = nominal_amount,
                purchase_date = inversio['purchase_date'],
                draft = inversio['draft'],
            )
            emission_data = Emission.read(cursor, uid, inversio['emission_id'][0], ['waiting_days', 'expiration_years'])
            waitDays = emission_data['waiting_days']
            expirationYears = emission_data['expiration_years']
            inv.pay(
                date = isodate(purchase_date),
                amount = amount,
                move_line_id = movementline_id,
                waitDays = waitDays,
                expirationYears = expirationYears,
            )
            self.write(cursor, uid, id, inv.erpChanges())

    def mark_as_unpaid(self, cursor, uid, ids, movementline_id=None):
        Soci = self.pool.get('somenergia.soci')
        ResUser = self.pool.get('res.users')
        AccountInvoice = self.pool.get('account.invoice')
        user = ResUser.read(cursor, uid, uid, ['name'])
        for id in ids:
            inversio = self.read(cursor, uid, id, [
                'log',
                'actions_log',
                'nshares',
                'purchase_date',
                'draft',
                'name',
            ])
            user = ResUser.read(cursor, uid, uid, ['name'])
            nominal_amount = inversio['nshares']*gkwh.shareValue
            if movementline_id:
                MoveLine = self.pool.get('account.move.line')
                moveline = ns(MoveLine.read(cursor, uid, movementline_id, []))
                amount = moveline.debit - moveline.credit
            else:
                amount = nominal_amount

            inv = InvestmentState(user['name'], datetime.now(),
                log = inversio['log'],
                nominal_amount = nominal_amount,
                purchase_date = inversio['purchase_date'],
                draft = inversio['draft'],
            )

            inv.unpay(
                amount = amount,
                move_line_id = movementline_id,
            )

            self.write(cursor, uid, id, inv.erpChanges())

            name_invoice = inversio['name'] + '-JUST'
            invoice_ids = AccountInvoice.search(cursor, uid, [
                ('name', '=', name_invoice)
            ])
            if invoice_ids: # Some tests do not generate invoice
                self.send_mail(cursor, uid, invoice_ids[0],
                    'account.invoice', '_mail_impagament',  id)

    def create_initial_invoices(self,cursor,uid, investment_ids):

        Partner = self.pool.get('res.partner')
        Product = self.pool.get('product.product')
        Invoice = self.pool.get('account.invoice')
        InvoiceLine = self.pool.get('account.invoice.line')
        PaymentType = self.pool.get('payment.type')
        Journal = self.pool.get('account.journal')

        invoice_ids = []

        date_invoice = str(date.today())

        # The payment type
        payment_type_id = PaymentType.search(cursor, uid, [
            ('code', '=', 'RECIBO_CSB'),
            ])[0]

        errors = []
        def error(message):
            errors.append(message)

        for investment in self.browse(cursor, uid, investment_ids):
            if not investment.active:
                error("Investment {} is inactive"
                    .format(investment.name))
                continue

            if investment.purchase_date:
                error("Investment {} was already paid"
                    .format(investment.name))
                continue

            # The product
            product = investment.emission_id.investment_product_id

            # TODO: Remove the GENKWHID stuff when fully migrated, error instead
            invoice_name = '%s-JUST' % '{}'.format(investment.id)
            if investment.name:
                 invoice_name = '%s-JUST' % investment.name
            elif investment.emission_id.type == 'genkwh':
                 invoice_name = '%s-JUST' % 'GENKWHID{}'.format(investment.id)
            elif investment.emission_id.type == 'apo':
                 invoice_name = '%s-JUST' % 'APOID{}'.format(investment.id)

            # Ensure unique invoice
            existingInvoice = Invoice.search(cursor,uid,[
                ('name','=', invoice_name),
                ])
            if existingInvoice:
                error("Initial Invoice {} already exists"
                    .format(invoice_name))
                continue

            if not investment.draft:
                error("Investment {} already invoiced"
                    .format(investment.name))
                continue

            # The partner
            partner_id = investment.member_id.partner_id.id

            account_inv_id = self.investment_actions(cursor, uid, investment.id).get_or_create_investment_account(cursor, uid, partner_id)
            partner = Partner.browse(cursor, uid, partner_id)

            # Check if exist bank account
            if not partner.bank_inversions:
                error(u"Partner '{}' has no investment bank account"
                    .format(partner.name))
                continue

            amount_total = gkwh.shareValue * investment.nshares

            mandate_id = self.get_or_create_payment_mandate(cursor, uid,
                partner_id, partner.bank_inversions.iban,
                investment.emission_id.mandate_name, gkwh.creditorCode)

            # Default invoice fields for given partner
            vals = {}
            vals.update(Invoice.onchange_partner_id(
                cursor, uid, [], 'in_invoice', partner_id,
            ).get('value', {}))

            vals.update({
                'partner_id': partner_id,
                'type': 'out_invoice',
                'name': invoice_name,
                'number': invoice_name,
                'journal_id': investment.emission_id.journal_id.id,
                'account_id': partner.property_account_liquidacio.id,
                'partner_bank': partner.bank_inversions.id,
                'payment_type': payment_type_id,
                'check_total': amount_total,
                'origin': investment.name,
                'mandate_id': mandate_id,
                'date_invoice': date_invoice,
            })

            invoice_id = Invoice.create(cursor, uid, vals)
            Invoice.write(cursor,uid, invoice_id,{'sii_to_send':False})

            # Memento of mutable data
            investmentMemento = ns()
            investmentMemento.pendingCapital = investment.nshares * gkwh.shareValue
            investmentMemento.investmentId = investment.id
            investmentMemento.investmentName = investment.name
            investmentMemento.investmentPurchaseDate = investment.purchase_date
            investmentMemento.investmentLastEffectiveDate = investment.last_effective_date
            investmentMemento.investmentInitialAmount = investment.nshares * gkwh.shareValue

            line = dict(
                InvoiceLine.product_id_change(cursor, uid, [],
                    product=product.id,
                    uom=product.uom_id.id,
                    partner_id=partner_id,
                    type='in_invoice',
                    ).get('value', {}),
                invoice_id = invoice_id,
                name = _('Inversió {investment} ').format(
                    investment = investment.name,
                ),
                quantity = investment.nshares,
                price_unit = gkwh.shareValue,
                product_id = product.id,
                # partner specific account, was generic from product
                account_id = account_inv_id,
                note = investmentMemento.dump(),
            )
            # rewrite relation
            line['invoice_line_tax_id'] = [
                (6, 0, line.get('invoice_line_tax_id', []))
            ]

            InvoiceLine.create(cursor, uid, line)

            invoice_ids.append(invoice_id)
            self.mark_as_invoiced(cursor, uid, investment.id)

        return invoice_ids, errors

    def open_invoices(self, cursor, uid, ids):
        openOK = True
        wf_service = netsvc.LocalService('workflow')
        for inv_id in ids:
            openOK += wf_service.trg_validate(uid, 'account.invoice', #OpenInvoice
                    inv_id, 'invoice_open', cursor)
        return openOK

    def invoices_to_payment_order(self,cursor,uid,invoice_ids, model_name):
        """
        Add the invoices to the currently open payment order having the
        specified model name. If none is open, then creates a new one.
        """
        Invoice = self.pool.get('account.invoice')
        order_id = self.get_or_create_open_payment_order(cursor, uid, model_name,
                    True)
        Invoice.afegeix_a_remesa(cursor,uid,invoice_ids, order_id)

    def investment_payment(self,cursor,uid,investment_ids):
        """
        Creates the invoices, open them and add the current payment order.
        Called from the investment_payment_wizard.
        """
        Invoice = self.pool.get('account.invoice')

        invoice_ids, errors = self.create_initial_invoices(cursor,uid, investment_ids)
        if invoice_ids:
            self.open_invoices(cursor, uid, invoice_ids)
            payment_mode = self.investment_actions(cursor, uid, investment_ids[0]).get_payment_mode_name(cursor, uid)
            self.invoices_to_payment_order(cursor, uid,
                invoice_ids, payment_mode)
            for invoice_id in invoice_ids:
                invoice_data = Invoice.read(cursor, uid, invoice_id, ['origin'])
                investment_ids = self.search(cursor, uid,[
                    ('name','=',invoice_data['origin'])])
                self.send_mail(cursor, uid, invoice_id,
                    'account.invoice', '_mail_pagament', investment_ids[0])
        return invoice_ids, errors

    def send_mail(self, cursor, uid, id, model, template, investment_id=None):

        PEAccounts = self.pool.get('poweremail.core_accounts')
        WizardInvoiceOpenAndSend = self.pool.get('wizard.invoice.open.and.send')
        MailMockup = self.pool.get('generationkwh.mailmockup')
        IrModelData = self.pool.get('ir.model.data')
        if not investment_id:
            investment_id = id
        prefix = self.investment_actions(cursor, uid, investment_id).get_prefix_semantic_id()
        template_id = IrModelData.get_object_reference(
                cursor, uid, 'som_generationkwh', prefix + template
        )[1]
        PETemplate = self.pool.get('poweremail.templates')

        from_id = PETemplate.read(cursor, uid, template_id)['enforce_from_account']
        if not from_id:
            from_id = PEAccounts.search(cursor, uid,[
               ('name','=','Generation kWh')
                ])
        else:
            from_id = from_id[:1]
        ctx = {
            'active_ids': [id],
            'active_id': id,
            'src_rec_ids': [id],
            'src_model': model,
            'from': from_id,
            'state': 'single',
            'priority': '0',
            }
        with AsyncMode('sync') as asmode:
            if MailMockup.isActive(cursor, uid):
                MailMockup.send_mail(cursor, uid, ns(
                                template = prefix + template,
                                model = model,
                                id = id,
                                from_id = from_id,
                            ).dump())
            else:
                WizardInvoiceOpenAndSend.envia_mail_a_client(
                    cursor, uid, id, model, prefix + template, ctx)

    def cancel(self,cursor,uid, ids, context=None):
        User = self.pool.get('res.users')
        user = User.read(cursor, uid, uid, ['name'])
        for id in ids:
            inversio = self.read(cursor, uid, id, [
                'log',
                'actions_log',
                'purchase_date',
                'draft',
                'active',
                ])

            inv = InvestmentState(user['name'], datetime.now(),
                log = inversio['log'],
                purchase_date = inversio['purchase_date'],
                draft = inversio['draft'],
                active = inversio['active']
            )
            inv.cancel()
            self.write(cursor, uid, id, inv.erpChanges())

    def resign(self,cursor,uid, ids, context=None):
        Invoice = self.pool.get('account.invoice')
        User = self.pool.get('res.users')
        user = User.read(cursor, uid, uid, ['name'])
        invoice_ids = []
        invoice_errors = []
        for id in ids:
            inversio = self.read(cursor, uid, id, [
                'name',
                'id',
                'log',
                'actions_log',
                'purchase_date',
                'draft',
                'active',
                ])

            # recover the investment's initial payment invoice
            invoice_name = '%s-JUST' % (
                # TODO: Remove the GENKWHID stuff when fully migrated, error instead
                inversio['name'] or 'GENKWHID{}'.format(inversio['id']),
            )

            inversion_invoice_ids = Invoice.search(cursor,uid,[
                ('name','=', invoice_name),
                ])
            if not inversion_invoice_ids or not inversion_invoice_ids[0]:
                 raise Exception("Inversion without initial invoice, cannot resign")
            inversion_invoice_id = inversion_invoice_ids[0]
            invoice_ids.append(inversion_invoice_id)

            # mark investment as canceled
            inv = InvestmentState(user['name'], datetime.now(),
                log = inversio['log'],
                purchase_date = inversio['purchase_date'],
                draft = inversio['draft'],
                active = inversio['active']
            )
            inv.cancel()

            # create a investment's resign invoice
            resign_invoice_id, error = self.create_resign_invoice(cursor, uid, id)
            if not resign_invoice_id:
                raise Exception(error)
            invoice_ids.append(resign_invoice_id)
            if error:
                invoice_errors.append(error)

            # pay the investment invoice
            self.pay_resign_invoice(cursor,uid,inversion_invoice_id,context)

            # open and pay the investment resign invoice
            self.open_invoices(cursor,uid,[resign_invoice_id])
            self.pay_resign_invoice(cursor,uid,resign_invoice_id,context)

            # store the cancel action over investment
            self.write(cursor, uid, id, inv.erpChanges())

        return invoice_ids,invoice_errors

    # TODO: move this function to account invoice
    def pay_resign_invoice(self, cursor, uid,invoice_id,context=None):
        from addons.account.wizard.wizard_pay_invoice import _pay_and_reconcile as wizard_pay
        from addons.account.wizard.wizard_pay_invoice import _get_period as wizard_period

        IrModelData = self.pool.get('ir.model.data')
        model, journal_id = IrModelData.get_object_reference(
            cursor, uid,
            'som_generationkwh', 'genkwh_journal',
        )

        period_data = wizard_period(self, cursor, uid,
            data=dict(id = invoice_id,),
            context={}
        )

        wizard_pay(self, cursor, uid, data=dict(
            id = invoice_id,
            ids = [invoice_id],
            form = dict(
                name='Compensació factures',
                date=period_data['date'],
                journal_id=journal_id,
                amount=period_data['amount'],
                period_id=period_data['period_id'],
            ),
        ), context={})

    def create_resign_invoice(self, cursor, uid,investment_id,context=None):
        Invoice = self.pool.get('account.invoice')
        investment = self.browse(cursor, uid, investment_id)    # resigning this

        # TODO: Remove the GENKWHID stuff when fully migrated, error instead
        investement_name = investment['name'] or 'GENKWHID{}'.format(investment['id'])

        inversion_invoice_name = '%s-JUST' % (investement_name)
        inversion_invoice_ids = Invoice.search(cursor,uid,[
            ('name','=', inversion_invoice_name),
            ])
        if not inversion_invoice_ids:
            return 0, u"Inversió {0}: no te factura inicial!".format(investment.id)
        inversion_invoice_id = inversion_invoice_ids[0]

        refund_invoice_name = '%s-RES' % (investement_name)
        refund_invoice_ids = Invoice.search(cursor,uid,[
            ('name','=', refund_invoice_name),
            ])
        if refund_invoice_ids:
            return 0, u"Inversió {0}: La renúncia {1} ja existeix".format(investment.id, refund_invoice_name)

        refund_invoice_id = Invoice.refund(cursor,uid,
            [inversion_invoice_id],
            description=refund_invoice_name
        )[0]

        Invoice.write(cursor,uid, refund_invoice_id,{
            'sii_to_send':False ,
            'origin': investement_name ,
            'number': refund_invoice_name ,
            })
        return refund_invoice_id,[]

    def is_last_year_amortized(self, cursor, uid, investment_name, current_year):
        Invoice = self.pool.get('account.invoice')
        invoice_number = investment_name + "-AMOR" + str(int(current_year)-1)
        amortized = Invoice.search(cursor, uid, [('number','=', invoice_number)])
        return amortized

    def divest(self, cursor, uid, ids, divestment_date=None):
        invoice_ids = []
        errors = []
        date_invoice = divestment_date or str(datetime.today().date())

        for id in ids:
            inv = self.browse(cursor, uid, id)
            investment_actions = GenerationkwhActions(self, cursor, uid, 1)
            if str(inv.emission_id.type) == 'apo':
                investment_actions = AportacionsActions(self, cursor, uid, 1)
            investment_actions.divest(cursor, uid, id, invoice_ids, errors, date_invoice)

        return invoice_ids, errors
        
    def create_divestment_invoice(self, cursor, uid,
        investment_id, date_invoice, to_be_divested,
        irpf_amount_current_year=0, irpf_amount=0, context=None):

        return self.investment_actions(cursor, uid, investment_id).\
            create_divestment_invoice(cursor, uid, investment_id, date_invoice, to_be_divested, irpf_amount_current_year, irpf_amount)

    def get_stats_investment_generation(self, cursor, uid, context=None):
        """
        Returns a list of dict with investment GenerationKwh statistics:
            res: {'socis': Number of 'socis' with Generation
                  'amount': Total investment in Generation without amortizations}
            params: No params
        """

        result = []

        if not context:
            context = {}

        if 'today' in context:
            today = context['today']
        else:
            today = date.today().strftime('%Y-%m-%d')

        active_inv_ids = self.search(cursor, uid, [
            ('emission_id.type', '=', 'genkwh'),
            ('last_effective_date', '>', today)
            ])

        standby_inv_ids = self.search(cursor, uid, [
            ('emission_id.type', '=', 'genkwh'),
            ('last_effective_date', '=', None)
            ])

        inv_ids = active_inv_ids + standby_inv_ids

        shares_data = self.read(cursor, uid, inv_ids,[
            'nshares',
            'member_id',
            ])

        socis_ids = [share_data['member_id'] for share_data in shares_data]
        n_socis = len(set(socis_ids))

        shares = sum([share_data['nshares'] for share_data in shares_data])

        result.append({'amount': shares * 100,
                       'socis': n_socis})
        return result

class InvestmentProvider(ErpWrapper):

    def items(self, member=None, start=None, end=None):
        Investment = self.erp.pool.get('generationkwh.investment')
        return Investment.effective_investments( self.cursor, self.uid,
                member, start, end, context=self.context)

    def effectiveForMember(self, member, first_date, last_date, emission_type=None, emission_code=None):
        Investment = self.erp.pool.get('generationkwh.investment')
        return Investment.member_has_effective(self.cursor, self.uid,
            member, first_date, last_date, emission_type, emission_code, self.context)


GenerationkwhInvestment()

# vim: et ts=4 sw=4
