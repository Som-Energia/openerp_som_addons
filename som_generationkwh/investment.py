# -*- coding: utf-8 -*-

from osv import osv, fields
from .erpwrapper import ErpWrapper
from dateutil.relativedelta import relativedelta
import datetime
from yamlns import namespace as ns
from generationkwh.isodates import isodate
from tools.translate import _
from tools import config


# TODO: This function is duplicated in other sources
def _sqlfromfile(sqlname):
    from tools import config
    import os
    sqlfile = os.path.join(
        config['addons_path'], 'som_generationkwh',
            'sql', sqlname+'.sql')
    with open(sqlfile) as f:
        return f.read()

class GenerationkWhInvestment(osv.osv):


    _name = 'generationkwh.investment'
    _order = 'purchase_date DESC'

    _columns = dict(
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
        purchase_date=fields.date(
            "Data de compra",
            required=True,
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
            required=True,
            select=True,
            help="Línia del moviment contable corresponent a la inversió",
            ),
        active=fields.boolean(
            "Activa",
            required=True,
            help="Permet activar o desactivar la inversió",
            )
        )

    _defaults = dict(
        active=lambda *a: True,
    )

    def effective_investments_tuple(self, cursor, uid,
            member=None, start=None, end=None,
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
        filters = []
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
            member, start, end,
            context=None):

        return [
            ns(
                member=member,
                firstEffectiveDate=first and isodate(first),
                lastEffectiveDate=last and isodate(last),
                shares=shares,
            )
            for member, first, last, shares
            in self.effective_investments_tuple(cursor, uid, member, start, end, context)
        ]

    def member_has_effective(self, cursor, uid,
            member_id, first_date, last_date,
            context=None):

        return len(self.effective_investments_tuple(cursor, uid,
            member_id, first_date, last_date, context))>0

    def _effectivePeriod(self, purchaseDate, waitingDays, expirationYears):
        if waitingDays is None:
            return None, None

        firstEffective = purchaseDate +relativedelta(days=waitingDays)

        if expirationYears is None:
            return firstEffective, None

        lastEffective = firstEffective+relativedelta(years=expirationYears)

        return firstEffective, lastEffective

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

        criteria = [
			('account_id', 'in', accountIds),
			('period_id.special', '=', False),
			]
        if stop: criteria.append(('date_created', '<=', str(stop)))
        if start: criteria.append(('date_created', '>=', str(start)))

        movelinesids = MoveLine.search(
            cursor, uid, criteria,
            order='date_created asc, id asc',
            context=context
            )

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

            # partner to member conversion
            # ctx = dict(context)
            # ctx.update({'active_test': False})
            
            members = Member.search(cursor, uid, domain, context)
            if not members:
                print (
                    "No existeix el soci de la linia comptable {}, {}"
                    .format(line, domain))
                continue

            member_id = members[0]

            activation, lastDateEffective = self._effectivePeriod(
                isodate(line.date_created),
                waitingDays, expirationYears)

            self.create(cursor, uid, dict(
                member_id=member_id,
                nshares=(line.credit-line.debit)//100,
                purchase_date=line.date_created,
                first_effective_date=activation,
                last_effective_date=lastDateEffective,
                move_line_id=line.id,
                ))


    def _disabled_create_from_accounting(self, cursor, uid,
            # TODO: member
            start, stop, waitingDays, expirationYears,
            context=None):
        """
            Takes accounting information and generates GenkWh investments
            purchased among start and stop dates.
            If waitingDays is not None, activation date is set those
            days after the purchase date.
            If expirationYears is not None, expiration date is set, those
            years after the activation date.
            TODO: Confirm that the expiration is relative to the activation
            instead the purchase.
        """

        query = _sqlfromfile('investment_from_accounting')
        cursor.execute(query, dict(
            start = start,
            stop = stop,
            waitingDays = waitingDays,
            expirationYears = expirationYears,
            generationAccountPrefix = '163500%',
            ))

        for (
                member_id,
                nshares,
                purchase_date,
                move_line_id,
                first_effective_date,
                last_effective_date, 
            ) in cursor.fetchall():

            self.create(cursor, uid, dict(
                member_id=member_id,
                nshares=nshares,
                purchase_date=purchase_date,
                first_effective_date=first_effective_date,
                last_effective_date=last_effective_date,
                move_line_id=move_line_id,
                ))

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

    def pending_amortizations(self, cursor, uid, current_date):
        from generationkwh.amortizations import (
            pendingAmortization,
            previousAmortizationDate,
            )
        inv_ids = self.search(cursor, uid, [])
        invs = self.read(cursor, uid, inv_ids, [
            'member_id',
            'purchase_date',
            'nshares',
            ])
        for inv in invs:
            inv.update(
                amortized_amount=pendingAmortization(
                    inv['purchase_date'],
                    current_date,
                    100*inv['nshares'],
                    0, # TODO: THIS SHOULD BE THE ACTUAL AMORTIZATION!!
                    ),
                amortization_date=previousAmortizationDate(
                    inv['purchase_date'],
                    current_date,
                    ),
                )
        return [(
            inv['id'],
            inv['member_id'][0],
            inv['amortization_date'] or False,
            inv['amortized_amount'],
            )
            for inv in invs
            if inv['amortized_amount']
        ]


class InvestmentProvider(ErpWrapper):

    def effectiveInvestments(self, member=None, start=None, end=None):
        Investment = self.erp.pool.get('generationkwh.investment')
        return Investment.effective_investments( self.cursor, self.uid,
                member, start, end, self.context)

    def effectiveForMember(self, member, first_date, last_date):
        Investment = self.erp.pool.get('generationkwh.investment')
        return Investment.member_has_effective(self.cursor, self.uid,
            member, first_date, last_date, self.context)


GenerationkWhInvestment()

