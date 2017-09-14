# -*- coding: utf-8 -*-

from osv import osv, fields
from .erpwrapper import ErpWrapper
from dateutil.relativedelta import relativedelta
from datetime import datetime, date
from yamlns import namespace as ns
from generationkwh.isodates import isodate
from tools.translate import _
from tools import config
import re
import generationkwh.investmentmodel as gkwh
from generationkwh.investmentstate import InvestmentState
from uuid import uuid4
import netsvc

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

class GenerationkWhInvestment(osv.osv):

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
            "Amortització Realitzada",
            digits=(16, int(config['price_accuracy'])),
            required=True,
            ),
        order_date=fields.date(
            "Data de comanda",
            # required=True, # TODO: activate it after migration
            help="Quin dia es varen demanar les accions",
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
        log=fields.text(
            'Història',
            # TODO to be required, after develop
            #required=true,
            help="Història d'esdeveniments relacionats amb la inversió",
            ),
        )

    _defaults = dict(
        active=lambda *a: True,
        amortized_amount=lambda *a: 0,
        log=lambda *a:'',
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
                    "No existeix el soci de la linia comptable id {l.id} {l.date_created} partner {l.partner_id.name} ac {l.account_id.name}, {l.credit} -{l.debit}  {d}"
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

        inv_ids = ids or self.search(cursor, uid, [], order='id')
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

    def amortize(self, cursor, uid, current_date, ids=None, context=None):
        User = self.pool.get('res.users')
        username = User.read(cursor, uid, uid, ['name'])['name']
        amortization_ids = []
        amortization_errors = []

        investment_ids = ids or self.search(cursor, uid, [], order='id')
        investments = self.read(cursor, uid, investment_ids, [
            'purchase_date',
            'amortized_amount',
            'nshares',
            'log',
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

                amortization_id, error = self.create_amortization_invoice(cursor, uid,
                        investment_id = investment_id,
                        amortization_date = amortization_date,
                        to_be_amortized = to_be_amortized,
                        amortization_number = amortization_number,
                        amortization_total_number = amortization_total_number,
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
                    'account.invoice', 'generationkwh_mail_amortitzacio')


        return amortization_ids, amortization_errors

    def create_amortization_invoice(self, cursor, uid,
            investment_id, amortization_date, to_be_amortized,
            amortization_number,amortization_total_number,
            context=None):

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
            ('default_code','=', gkwh.amortizationProductCode),
            ])[0]

        product = Product.browse(cursor, uid, product_id)
        product_uom_id = product.uom_id.id

        # The journal
        journal_id = Journal.search(cursor, uid, [
            ('code','=',gkwh.journalCode),
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
            'check_total': to_be_amortized,
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

        return invoice_id, errors

    # TODO: Move to res.partner
    def get_default_country(self, cursor, uid):
        ResCountry = self.pool.get('res.country')
        return ResCountry.search(cursor, uid, [('code', '=', 'ES')])[0]

    # TODO: Move to res.partner
    def check_spanish_account(self, cursor, uid, account):
        spain = self.get_default_country(cursor, uid)
        ResPartnerBank = self.pool.get('res.partner.bank')
        ResBank = self.pool.get('res.bank')
        vals = ResPartnerBank.onchange_banco(cursor, uid, [], account, spain, {})
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
            partner_id, order_date, amount_in_euros, ip, iban,
            context=None):

        if amount_in_euros % gkwh.shareValue > 0:
            return False

        ResPartner = self.pool.get('res.partner')

        iban = self.check_iban(cursor, uid, iban)
        bank_id = self.get_or_create_partner_bank(cursor, uid,
                    partner_id, iban)
        ResPartner.write(cursor, uid, partner_id, dict(
            bank_inversions = bank_id,),context)

        Soci = self.pool.get('somenergia.soci')
        IrSequence = self.pool.get('ir.sequence')
        member_id = Soci.search(cursor, uid, [
                ('partner_id','=',partner_id)
                ])[0]

        ResUser = self.pool.get('res.users')
        user = ResUser.read(cursor, uid, uid, ['name'])
        name = IrSequence.get_next(cursor,uid,'som.inversions.gkwh')

        inv = InvestmentState(user['name'], datetime.now())
        inv.order(
            name = name,
            date = order_date,
            amount = amount_in_euros,
            iban = iban,
            ip = ip,
            )
        investment_id = self.create(cursor, uid, dict(
            inv.erpChanges(),
            member_id = member_id,
        ), context)

        self.get_or_create_payment_mandate(cursor, uid,
            partner_id, iban, gkwh.mandateName, gkwh.creditorCode)

        self.send_mail(cursor, uid, investment_id,
            'generationkwh.investment', 'generationkwh_mail_creacio')

        return investment_id

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

    def mark_as_paid(self, cursor, uid, ids, purchase_date, movementline_id=None):
        Soci = self.pool.get('somenergia.soci')
        User = self.pool.get('res.users')
        user = User.read(cursor, uid, uid, ['name'])
        for id in ids:
            inversio = self.read(cursor, uid, id, [
                'log',
                'nshares',
                'member_id',
                'purchase_date',
                ])
            ResUser = self.pool.get('res.users')
            user = ResUser.read(cursor, uid, uid, ['name'])
            nominal_amount = inversio['nshares']*gkwh.shareValue
            if movementline_id:
                MoveLine = self.pool.get('account.move.line')
                moveline = ns(MoveLine.read(cursor, uid, movementline_id, []))
                amount = moveline.credit - moveline.debit
            else:
                amount = nominal_amount

            inv = InvestmentState(user['name'], datetime.now(),
                log = inversio['log'],
                nominal_amount = nominal_amount,
                paid_amount = nominal_amount if inversio['purchase_date'] else 0,
                draft = False, # TODO: Db or has invoice?
            )

            inv.pay(
                date = isodate(purchase_date),
                amount = amount, # TODO: Take it from moveline
                move_line_id = movementline_id,
            )
            self.write(cursor, uid, id, inv.erpChanges())

    def mark_as_unpaid(self, cursor, uid, ids, movementline_id=None):
        Soci = self.pool.get('somenergia.soci')
        User = self.pool.get('res.users')
        user = User.read(cursor, uid, uid, ['name'])
        for id in ids:
            inversio = self.read(cursor, uid, id, [
                'log',
                'nshares',
                'purchase_date',
            ])
            ResUser = self.pool.get('res.users')
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
                paid_amount = nominal_amount if inversio['purchase_date'] else 0,
                draft = False, # TODO: Db or has invoice?
            )

            inv.unpay(
                amount = amount, # TODO: Take it from moveline
                move_line_id = movementline_id,
            )

            self.write(cursor, uid, id, inv.erpChanges())

            self.send_mail(cursor, uid, id,
                'account.invoice', 'generationkwh_mail_impagament')

    def create_initial_invoices(self,cursor,uid, investment_ids):

        Partner = self.pool.get('res.partner')
        Product = self.pool.get('product.product')
        Invoice = self.pool.get('account.invoice')
        InvoiceLine = self.pool.get('account.invoice.line')
        PaymentType = self.pool.get('payment.type')
        Journal = self.pool.get('account.journal')

        invoice_ids = []

        date_invoice = str(date.today())

        # The product
        product_id = Product.search(cursor, uid, [
            ('default_code','=', gkwh.investmentProductCode),
            ])[0]

        product = Product.browse(cursor, uid, product_id)
        product_uom_id = product.uom_id.id

        # The journal
        journal_id = Journal.search(cursor, uid, [
            ('code','=',gkwh.journalCode),
            ])[0]

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

            # Check if exist bank account
            if not partner.bank_inversions:
                error(u"Partner '{}' has no investment bank account"
                    .format(partner.name))
                continue

            invoice_name = '%s-FACT' % (
                # TODO: Remove the GENKWHID stuff when fully migrated, error instead
                investment.name or 'GENKWHID{}'.format(investment.id),
            )

            # Ensure unique invoice
            existingInvoice = Invoice.search(cursor,uid,[
                ('name','=', invoice_name),
                ])
            if existingInvoice:
                error("Initial Invoice {} already exists"
                    .format(invoice_name))
                continue

            amount_total = gkwh.shareValue * investment.nshares

            mandate_id = self.get_or_create_payment_mandate(cursor, uid,
                partner_id, partner.bank_inversions.iban,
                gkwh.mandateName, gkwh.creditorCode)

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
                'journal_id': journal_id,
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

            line = dict(
                InvoiceLine.product_id_change(cursor, uid, [],
                    product=product_id,
                    uom=product_uom_id,
                    partner_id=partner_id,
                    type='in_invoice',
                    ).get('value', {}),
                invoice_id = invoice_id,
                name = _('Inversió {investment} ').format(
                    investment = investment.name,
                ),
                quantity = investment.nshares,
                price_unit = gkwh.shareValue,
                product_id = product_id,
                # partner specific account, was generic from product
                account_id = partner.property_account_gkwh.id,
            )
            # rewrite relation
            line['invoice_line_tax_id'] = [
                (6, 0, line.get('invoice_line_tax_id', []))
            ]

            InvoiceLine.create(cursor, uid, line)

            invoice_ids.append(invoice_id)

        return invoice_ids, errors

    def open_invoices(self, cursor, uid, ids):
        openOK = True
        wf_service = netsvc.LocalService('workflow')
        for inv_id in ids:
            openOK += wf_service.trg_validate(uid, 'account.invoice', #OpenInvoice
                    inv_id, 'invoice_open', cursor)
        return openOK

    def invoices_to_payment_order(self,cursor,uid,invoice_ids, model_name):
        Invoice = self.pool.get('account.invoice')

        order_id = self.get_or_create_open_payment_order(cursor, uid, model_name, 
                    True)
        Invoice.afegeix_a_remesa(cursor,uid,invoice_ids, order_id)

    def investment_payment(self,cursor,uid,investment_ids):
        Investment = self.pool.get('generationkwh.investment')

        invoice_ids, errors = Investment.create_initial_invoices(cursor,uid, investment_ids)
        if invoice_ids:
            Investment.open_invoices(cursor, uid, invoice_ids)
            Investment.invoices_to_payment_order(cursor, uid,
                invoice_ids, gkwh.investmentPaymentMode)
            for invoice_id in invoice_ids:
                self.send_mail(cursor, uid, invoice_id,
                    'account.invoice', 'generationkwh_mail_pagament')
        return invoice_ids, errors

    def send_mail(self, cursor, uid, id, model, template):
        PEAccounts = self.pool.get('poweremail.core_accounts')
        WizardInvoiceOpenAndSend = self.pool.get('wizard.invoice.open.and.send')
        MailMockup = self.pool.get('generationkwh.mailmockup')

        from_id = PEAccounts.search(cursor, uid,[
           ('name','=','Generation kWh')
            ])

        ctx = {
            'active_ids': [id],
            'active_id': id,
            'src_rec_ids': [id],
            'src_model': model,
            'from': from_id,
            'state': 'single',
            'priority': '0',
            }

        if MailMockup.isActive(cursor, uid):
            MailMockup.send_mail(cursor, uid, ns(
                            template = template,
                            model = model,
                            id = id,
                            from_id = from_id,
                        ).dump())
        else:
            WizardInvoiceOpenAndSend.envia_mail_a_client(
                cursor, uid, id,model,template, ctx)

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

# vim: et ts=4 sw=4
