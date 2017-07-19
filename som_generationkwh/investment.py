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
            required=True,
            help="Història d'esdeveniments relacionats amb la inversió",
            )
        )

    _defaults = dict(
        active=lambda *a: True,
        amortized_amount=lambda *a: 0,
        log=lambda *a:'',
    )

    def migrate_created_from_accounting(self, cursor, uid,
            investment_ids=None,
            context=None):
        """
            Migrate legacy investments created from accounting, not from form.
            Sets new fields with retrieved or guessed info.
            Processes any investment with empty log unless specific ids are provided.
        """
        MoveLine = self.pool.get('account.move.line')

        if investment_ids is None:
            investment_ids = self.search(cursor, uid, [
                ('log','=',''),
                ], context)

        investments = self.read(cursor, uid, investment_ids, [
            'move_line_id',
            ])
        for investment in investments:
            movementline_ids = [investment['move_line_id'][0]]
            moveline_perms = MoveLine.perm_read(cursor, uid, movementline_ids )[0]
            investment_perms = self.perm_read(cursor, uid, [investment['id']])[0]
            # TODO: Take it from PaymentLine instead
            order_date = moveline_perms['create_date']
            order_user = 'Webforms'
            purchase_date = moveline_perms['create_date']
            purchase_user = moveline_perms['create_uid'][1] if moveline_perms['create_uid'] else 'Nobody'

            self.write(cursor, uid, investment['id'], dict(
                log=
                    u'[{} {}] PAYMENT: Remesa efectuada\n'
                    u'[{} {}] ORDER: Formulari emplenat\n'
                    .format(
                        purchase_date, purchase_user,
                        order_date, order_user,
                    ),
                order_date=order_date,
                ), context)


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

            investment_id = self.create(cursor, uid, dict(
                member_id=member_id,
                nshares=(line.credit-line.debit)//100,
                purchase_date=line.date_created,
                first_effective_date=activation,
                last_effective_date=lastDateEffective,
                move_line_id=line.id,
                ))

            investment_ids.append(investment_id)

        self.migrate_created_from_accounting(cursor, uid, investment_ids, context)

        return sorted(investment_ids)


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
        inv_ids = self.search(cursor, uid, [], order='id')
        invs = self.read(cursor, uid, inv_ids, [
            'member_id',
            'purchase_date',
            'amortized_amount',
            'nshares',
            'log',
            ])
        for inv in invs:
            inv.update(
                to_be_amortized=pendingAmortization(
                    inv['purchase_date'],
                    current_date,
                    100*inv['nshares'],
                    inv['amortized_amount'],
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
            inv['to_be_amortized'],
            inv['log'],
            )
            for inv in invs
            if inv['to_be_amortized']
        ]

    def amortize(self, cursor, uid, current_date, context=None):
        pending = self.pending_amortizations(cursor, uid, current_date)
        amortization_ids = []
        for investment_tuple in pending:
            (
                investment_id,
                member_id,
                amortization_date,
                amortized_amount,
                to_be_amortized,
                log,
            ) = investment_tuple

            #amortization_id = self.create_amortization_invoice(cursor, uid,
                #investment_id, amortization_date, to_be_amortized)

            #amortization_ids.append(amortization_id)

            self.write(cursor, uid, investment_id, dict(
                amortized_amount=amortized_amount+to_be_amortized,
                log = u"[{} {}] AMORTIZATION: "
                    u"Generada amortització de {:.02f} € pel {}\n"
                    .format(
                        # TODO: Take this from now and uid
                        '2015-07-29 09:39:07.70812',
                        u'David García Garzón',
                        to_be_amortized,
                        amortization_date,
                    )+log,
                ), context)

        return amortization_ids


    def create_amortization_invoice(self, cursor, uid,
            investment_id, amortization_date, to_be_amortized,
            context=None):

        Partner = self.pool.get('res.partner')
        Product = self.pool.get('product.product')
        Invoice = self.pool.get('account.invoice')
        InvoiceLine = self.pool.get('account.invoice.line')
        PaymentType = self.pool.get('payment.type')
        Journal = self.pool.get('account.journal')

        investment = self.browse(cursor, uid, investment_id)

        date_invoice = str(datetime.datetime.today().date())
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
            ('default_code','=', 'GENKWH_AMOR'),
            ])[0]

        product = Product.browse(cursor, uid, product_id)
        product_uom_id = product.uom_id.id

        # The journal
        journal_id = Journal.search(cursor, uid, [
            ('code','=','GENKWH_AMOR'),
            ])[0]
        journal = Journal.browse(cursor, uid, journal_id)

        # The payment type
        payment_type_id = PaymentType.search(cursor, uid, [
            ('code', '=', 'TRANSFERENCIA_CSB'),
            ])[0]

        # Memento of mutable data
        investmentMemento = ns()
        # TODO: add here your stuff
        investmentMemento.pendingCapital = investment.nshares * 100.0 - investment.amortized_amount - to_be_amortized

        # Ensure unique amortization
        invoice_name = '%s-AMOR%s' % (
                investment.name,
                year,
                )
        existingInvoice = Invoice.search(cursor,uid,[
            ('name','=', invoice_name),
            ])
        if existingInvoice:
            raise Exception(
                "Amortization notification {} already exists"
                .format(invoice_name))


        # Default invoice fields for given partner
        vals = {}
        vals.update(Invoice.onchange_partner_id(
            cursor, uid, [], 'in_invoice', partner_id,
        ).get('value', {}))

        vals.update({
            'partner_id': partner_id,
            'type': 'in_invoice',
            'name': invoice_name,
            'journal_id': journal_id,
            'account_id': partner.property_account_liquidacio.id,
            'partner_bank': partner.bank_inversions.id, # TODO: si es False fer algo
            'payment_type': payment_type_id,
        })
        if date_invoice:
            vals['date_invoice'] = date_invoice

        invoice_id = Invoice.create(cursor, uid, vals)

        amortization_per_share = 4

        vals = {
            'invoice_id': invoice_id,
            'name': _('Amortització fins a {amortization_date:%d/%m/%Y} de {investment} ').format(
                investment = investment.name,
                amortization_date = datetime.datetime.strptime(amortization_date,'%Y-%m-%d'),
            ),
#            'note': _('Sense notes'),
            'quantity': 1,
            'price_unit': to_be_amortized,
            'product_id': product_id,
        }

        line = dict(InvoiceLine.product_id_change(cursor, uid, [],
            product=product_id,
            uom=product_uom_id,
            partner_id=partner_id,
            type='in_invoice',
            ).get('value', {})
        )
        line['invoice_line_tax_id'] = [
            (6, 0, line.get('invoice_line_tax_id', []))
        ]
        line['account_id']=partner.property_account_gkwh.id
        line['note'] = investmentMemento.dump()
        line.update(vals)
        InvoiceLine.create(cursor, uid, line)

        return invoice_id

#def get_default_country(self):
#        ResCountry = self.pool.get('res.country')         
#        return ResCountry.search(cursor, uid, [('code', '=', 'ES')])[0]
#
#    def check_spanish_account(self, account):
#        spain = get_default_country()
#        ResPartnerBank = self.pool.get('res.partner.bank')
#        ResBank = self.pool.get('res.bank')
#        vals = ResPartnerBank.onchange_banco([], account, spain, {})
#        if 'warning' in vals:
#            # TODO: Use vals['warning']['message']
#            # TODO: Would require use a context with locale
#            return None
#
#        if 'value' not in vals or not vals['value']:
#            # TODO: Not string or country not ES... needed?
#            return None
#
#        result = {}
#
#        if 'bank' in vals['value']:
#            bank = ResBank.get(vals['value']['bank'])
#            result['bank_name'] = bank.name
#        if 'acc_number' in vals['value']:
#            result['acc_number'] = vals['value']['acc_number']
#
#        return result
#   
    def clean_iban(self, cursor, uid, iban):
        '''This function removes all characters from given 'iban' that isn't a
        alpha numeric and converts it to upper case.'''
        return "".join(
            char.upper()
            for char in iban
            if char.isalnum()
            )

    # TODO: Foreign IBANs accepted? make CCC check conditional
    # TODO: Foreign IBANs not accepted? should start by ES
    # TODO: Consider using stdnum
    def check_iban(self, cursor, uid, iban):
        """
        Returns the clean iban if the iban is correct, or None otherwise.
        """
        iban = self.clean_iban(cursor, uid, iban)
        #if not re.match('[A-Z]{2}[0-9]{2}', iban[:4]):
        #    return None

        ResPartnerBank = self.pool.get('res.partner.bank')
        generatedIban = ResPartnerBank.calculate_iban(cursor, uid,
            iban[4:], iban[:2])
        if generatedIban != iban:
            return None

        # TODO: Just if starts with ES!!
        #bank = check_spanish_account(iban[4:])
        #if bank is None:
        #    return None 

        return iban

    def get_or_create_partner_bank(self, cursor, uid,
            partner_id, iban):
        """
        If such an iban is alredy a bank account for the
        partner, it returns it.
        If not it creates it and returns the new one.
        """
        ResPartnerBank = self.pool.get('res.partner.bank')
        ResCountry = self.pool.get('res.country')
        country_id = ResCountry.search(cursor, uid, [('code', '=', 'ES')])[0]

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

        # TODO: IBAN should come from the form

        Soci = self.pool.get('somenergia.soci')
        IrSequence = self.pool.get('ir.sequence')
        member_id = Soci.search(cursor, uid, [
                ('partner_id','=',partner_id)
                ])[0]
        Partner = self.pool.get('res.partner')
        Partner.write(cursor, uid, partner_id, dict(
                bank_inversions = 2,),context)

        name = IrSequence.get_next(cursor,uid,'som.inversions.gkwh')
        id = self.create(cursor, uid, dict(
            name = name,
            nshares = amount_in_euros/100, # TODO: error if remainder
            member_id = member_id,
            order_date = order_date,
            ), context)
        creationInfo = self.perm_read(cursor, uid, [id])[0]
        self.write(cursor, uid, id, dict(
            log = u'[{create_date} {create_uid[1]}] '
                'ORDER: Formulari emplenat des de {ip}\n'
                .format(ip=ip,**creationInfo)
            ))
        return id


    def charge(self, cursor, uid, ids, purchase_date):
        for id in ids:
            inversio = self.read(cursor, uid, id, ['log'])
            creationInfo = self.perm_read(cursor, uid, [id])[0]
            self.write(cursor, uid, id, dict(
                log = u'[{create_date} {create_uid[1]}] PAYED: Remesada al compte\n'
                    .format(**creationInfo)
                    + inversio['log'],
                purchase_date = purchase_date,
                ))
        

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
