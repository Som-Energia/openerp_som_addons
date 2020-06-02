# -*- coding: utf-8 -*-
from erpwrapper import ErpWrapper
from generationkwh.isodates import isodate
import generationkwh.investmentmodel as gkwh
from generationkwh.investmentstate import InvestmentState
from datetime import datetime, date
from yamlns import namespace as ns
from tools.translate import _
from dateutil.relativedelta import relativedelta


class PartnerException(Exception):
    pass
class InvestmentException(Exception):
    pass

class InvestmentActions(ErpWrapper):

    @property
    def journalCode(self):
        pass
    
    @property
    def productCode(self):
        pass

    def create_from_form(self, cursor, uid, partner_id, order_date, amount_in_euros, ip, iban,
            emission=None, context=None):
        GenerationkwhInvestment = self.erp.pool.get('generationkwh.investment')
        Emission = self.erp.pool.get('generationkwh.emission')

        if amount_in_euros <= 0 or amount_in_euros % gkwh.shareValue > 0:
                raise InvestmentException("Invalid amount")
        iban = GenerationkwhInvestment.check_iban(cursor, uid, iban)

        if not iban:
                raise PartnerException("Wrong iban")
        if not emission:
            emission = 'emissio_genkwh'

        #Compatibility 'emission_apo'
        imd_model = self.erp.pool.get('ir.model.data')
        imd_emission_id = imd_model.search(cursor, uid, [('module','=', 'som_generationkwh'),('name','=',emission)])
        if imd_emission_id:
            emission_id = imd_model.read(cursor, uid, imd_emission_id[0], ['res_id'])['res_id']
        else:
            emission_id = Emission.search(cursor, uid, [('code','=',emission)])[0]

        Soci = self.erp.pool.get('somenergia.soci')
        member_ids = Soci.search(cursor, uid, [
                ('partner_id','=',partner_id)
                ])
        if not member_ids:
            raise PartnerException("Not a member")

        bank_id = GenerationkwhInvestment.get_or_create_partner_bank(cursor, uid,
                    partner_id, iban)
        ResPartner = self.erp.pool.get('res.partner')
        ResPartner.write(cursor, uid, partner_id, dict(
            bank_inversions = bank_id,),context)

        return member_ids, emission_id

    def divest(self, cursor, uid, id, invoice_ids, errors, date_invoice):
        pass
    
    def get_or_create_investment_account(self, cursor, uid, partner_id):
        pass

    def create_divestment_invoice(self, cursor, uid,
            investment_id, date_invoice, to_be_divested,
            irpf_amount_current_year=0, irpf_amount=0, context=None):
        
        Partner = self.erp.pool.get('res.partner')
        Product = self.erp.pool.get('product.product')
        Invoice = self.erp.pool.get('account.invoice')
        InvoiceLine = self.erp.pool.get('account.invoice.line')
        PaymentType = self.erp.pool.get('payment.type')
        Journal = self.erp.pool.get('account.journal')
        Investment =  self.erp.pool.get('generationkwh.investment')

        investment = Investment.browse(cursor, uid, investment_id)

        # The partner
        partner_id = investment.member_id.partner_id.id
        partner = Partner.browse(cursor, uid, partner_id)

        # Get or create partner specific accounts
        account_inv_id = self.get_or_create_investment_account(cursor, uid, partner_id)
        # The product
        product_id = Product.search(cursor, uid, [
            ('default_code','=', self.productCode),
            ])[0]

        product = Product.browse(cursor, uid, product_id)
        product_uom_id = product.uom_id.id

        # The journal
        journal_id = Journal.search(cursor, uid, [
            ('code','=',self.journalCode),
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
        investmentMemento.pendingCapital = investment.nshares * gkwh.shareValue - investment.amortized_amount - to_be_divested
        investmentMemento.divestmentDate = date_invoice
        investmentMemento.investmentId = investment_id
        investmentMemento.investmentName = investment.name
        investmentMemento.investmentPurchaseDate = investment.purchase_date
        investmentMemento.investmentLastEffectiveDate = investment.last_effective_date
        investmentMemento.investmentInitialAmount = investment.nshares * gkwh.shareValue

        invoice_name = '%s-DES' % (
            # TODO: Remove the GENKWHID stuff when fully migrated, error instead
            investment.name or 'GENKWHID{}'.format(investment.id),
            )
        # Ensure unique amortization
        existingInvoice = Invoice.search(cursor,uid,[
            ('name','=', invoice_name),
            ])

        if existingInvoice:
            return 0, u"Inversió {0}: La desinversió {1} ja existeix".format(investment.id, invoice_name)

        # Default invoice fields for given partner
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
            #'check_total': to_be_divested,
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
            name = _('Desinversió total de {investment} a {date} ').format(
                investment = investment.name,
                date = str(date_invoice),
                ),
            note = investmentMemento.dump(),
            quantity = 1,
            price_unit = to_be_divested,
            product_id = product_id,
            # partner specific account, was generic from product
            account_id = account_inv_id,
        )

        # no taxes apply
        line['invoice_line_tax_id'] = [
            (6, 0, line.get('invoice_line_tax_id', []))
        ]

        InvoiceLine.create(cursor, uid, line)
        if irpf_amount_current_year:
            irpf_amount_current_year = round(irpf_amount_current_year,2)
            Investment.irpfRetentionLine(cursor, uid, investment, irpf_amount_current_year, invoice_id, isodate(date_invoice), investmentMemento)
        if irpf_amount:
            irpf_amount = round(irpf_amount, 2)
            Investment.irpfRetentionLine(cursor, uid, investment, irpf_amount, invoice_id, isodate(date_invoice)-relativedelta(years=1), investmentMemento)

        Invoice.write(cursor, uid, invoice_id, dict(
            check_total=to_be_divested - irpf_amount_current_year - irpf_amount,
            ))
        return invoice_id, errors

class GenerationkwhActions(InvestmentActions):

    @property
    def journalCode(self):
        return 'GENKWH'

    @property
    def productCode(self):
        return 'GENKWH_AMOR'

    def create_from_form(self, cursor, uid, partner_id, order_date, amount_in_euros, ip, iban,
            emission=None, context=None):
        member_ids, emission_id = super(GenerationkwhActions, self).create_from_form(cursor, uid, partner_id, order_date, amount_in_euros, ip, iban,emission, context)

        GenerationkwhInvestment = self.erp.pool.get('generationkwh.investment')
        ResUser = self.erp.pool.get('res.users')                            
        user = ResUser.read(cursor, uid, uid, ['name'])                 
        IrSequence = self.erp.pool.get('ir.sequence')                       
        name = IrSequence.get_next(cursor,uid,'som.inversions.gkwh')    
                                                                        
        inv = InvestmentState(user['name'], datetime.now())             
        inv.order(                                                      
            name = name,                                                
            date = order_date,                                          
            amount = amount_in_euros,                                   
            iban = iban,                                                
            ip = ip,                                                    
            )                                                           
        investment_id = GenerationkwhInvestment.create(cursor, uid, dict(                  
            inv.erpChanges(),                                           
            member_id = member_ids[0],                                  
            emission_id = emission_id,                                  
        ), context)                                                     
                                                                        
        GenerationkwhInvestment.get_or_create_payment_mandate(cursor, uid,                 
            partner_id, iban, gkwh.mandateName, gkwh.creditorCode)      
                                                                        
        GenerationkwhInvestment.send_mail(cursor, uid, investment_id,                      
            'generationkwh.investment', '_mail_creacio')

        return investment_id

    def get_prefix_semantic_id(self):
        return 'generationkwh'

    def get_payment_mode_name(self, cursor, uid):
        IrModelData = self.erp.pool.get('ir.model.data')
        payment_mode_id = IrModelData.get_object_reference(
            cursor, uid, 'som_generationkwh', 'genkwh_investment_payment_mode'
        )[1]
        PaymentMode = self.erp.pool.get('payment.mode')
        return PaymentMode.read(cursor, uid, payment_mode_id, ['name'])['name']

    def get_or_create_investment_account(self, cursor, uid, partner_id):
        Partner = self.erp.pool.get('res.partner')
        partner = Partner.browse(cursor, uid, partner_id)

        if not partner.property_account_liquidacio:
            partner.button_assign_acc_410()
            partner = partner.browse()[0]
        if not partner.property_account_gkwh:
            partner.button_assign_acc_1635()
            partner = partner.browse()[0]
        return partner.property_account_gkwh.id

    def divest(self, cursor, uid, id, invoice_ids, errors, date_invoice):
        User = self.erp.pool.get('res.users')
        user = User.read(cursor, uid, uid, ['name'])
        Invoice = self.erp.pool.get('account.invoice')
        MoveLine = self.erp.pool.get('account.move.line')
        Investment = self.erp.pool.get('generationkwh.investment')
        
        inversio = Investment.read(cursor, uid, id, [
            'log',
            'nshares',
            'purchase_date',
            'amortized_amount',
            'first_effective_date',
            'name',
            'move_line_id',
            'member_id'
        ])
        nominal_amount = inversio['nshares']*gkwh.shareValue
        pending_amount = nominal_amount-inversio['amortized_amount']
        daysFromPayment = (isodate(date_invoice) - isodate(inversio['purchase_date'])).days

        if daysFromPayment < gkwh.waitDaysBeforeDivest:
            errors.append("%s: Too early to divest (< 30 days from purchase)" % inversio['name'])
            return

        irpf_amount_last_year = 0
        if not Investment.is_last_year_amortized(cursor, uid, inversio['name'], datetime.now().year):
            irpf_amount_last_year = Investment.get_irpf_amounts(cursor, uid, id, inversio['member_id'][0])['irpf_amount']
        irpf_amount_current_year = Investment.get_irpf_amounts(cursor, uid, id, inversio['member_id'][0], datetime.now().year)['irpf_amount']

        invoice_id, error = self.create_divestment_invoice(cursor, uid, id,
            date_invoice, pending_amount, irpf_amount_current_year, irpf_amount_last_year)

        if error:
            errors.append(error)
            return

        Investment.open_invoices(cursor, uid, [invoice_id])
        Investment.invoices_to_payment_order(cursor, uid,
                [invoice_id], gkwh.amortizationPaymentMode)
        invoice_ids.append(invoice_id)

        #Get moveline id
        invoice_obj = Invoice.read(cursor, uid, invoice_id, [
            'move_id',
        ])
        ml_invoice = invoice_obj['move_id'][0]
        movementline_id = MoveLine.search(cursor, uid,
            [('move_id','=',invoice_obj['move_id'][0])])[0]

        inv = InvestmentState(user['name'], datetime.now(),
            log = inversio['log'],
            nominal_amount = nominal_amount,
            purchase_date = inversio['purchase_date'],
            amortized_amount = inversio['amortized_amount'],
            first_effective_date = inversio['first_effective_date'],
        )
        inv.divest(
            date = str(date_invoice),
            amount = pending_amount,
            move_line_id = movementline_id,
        )
        Investment.write(cursor, uid, id, inv.erpChanges())


class AportacionsActions(InvestmentActions):

    @property
    def journalCode(self):
        return 'APO_FACT'

    @property
    def productCode(self):
        return 'APO_AE'

    def create_from_form(self, cursor, uid, partner_id, order_date, amount_in_euros, ip, iban, emission=None, context=None):
        member_ids, emission_id = super(AportacionsActions, self).create_from_form(cursor, uid, partner_id, order_date, amount_in_euros, ip, iban,emission, context)
        GenerationkwhInvestment = self.erp.pool.get('generationkwh.investment')

        Emission = self.erp.pool.get('generationkwh.emission')
        emi_obj = Emission.read(cursor, uid, emission_id, ['mandate_name','code'])

        if not GenerationkwhInvestment.check_investment_creation(cursor, uid, partner_id, emi_obj['code'], amount_in_euros):
            raise InvestmentException("Impossible to create investment")

        Soci = self.erp.pool.get('somenergia.soci')
        member_ids = Soci.search(cursor, uid, [
                ('partner_id','=',partner_id)
                ])
        ResUser = self.erp.pool.get('res.users')
        user = ResUser.read(cursor, uid, uid, ['name'])
        IrSequence = self.erp.pool.get('ir.sequence')
        name = IrSequence.get_next(cursor,uid,'seq.som.aportacions')

        inv = InvestmentState(user['name'], datetime.now())
        inv.order(
            name = name,
            date = order_date,
            amount = amount_in_euros,
            iban = iban,
            ip = ip,
            )
        investment_id = GenerationkwhInvestment.create(cursor, uid, dict(
            inv.erpChanges(),
            member_id = member_ids[0],
            emission_id = emission_id,
        ), context)


        GenerationkwhInvestment.get_or_create_payment_mandate(cursor, uid,
            partner_id, iban, emi_obj['mandate_name'], gkwh.creditorCode)

        GenerationkwhInvestment.send_mail(cursor, uid, investment_id,
            'generationkwh.investment', '_mail_creacio')

        return investment_id

    def get_prefix_semantic_id(self):
        return 'aportacio'

    def get_payment_mode_name(self, cursor, uid):
        imd_model = self.erp.pool.get('ir.model.data')
        payment_mode_id = imd_model.get_object_reference(
            cursor, uid, 'som_generationkwh', 'apo_investment_payment_mode'
        )[1]
        PaymentMode = self.erp.pool.get('payment.mode')
        return PaymentMode.read(cursor, uid, payment_mode_id, ['name'])['name']

    def get_or_create_investment_account(self, cursor, uid, partner_id):
        Partner = self.erp.pool.get('res.partner')
        partner = Partner.browse(cursor, uid, partner_id)
        
        if not partner.property_account_liquidacio:
            partner.button_assign_acc_410()
            partner = partner.browse()[0]
        if not partner.property_account_aportacions:
            partner.button_assign_acc_163()
            partner = partner.browse()[0]
        return partner.property_account_aportacions.id

    def divest(self, cursor, uid, id, invoice_ids, errors, date_invoice):
        User = self.erp.pool.get('res.users')
        user = User.read(cursor, uid, uid, ['name'])
        Invoice = self.erp.pool.get('account.invoice')
        MoveLine = self.erp.pool.get('account.move.line')
        Investment = self.erp.pool.get('generationkwh.investment')

        inversio = Investment.read(cursor, uid, id, [
            'log',
            'nshares',
            'purchase_date',
            'amortized_amount',
            'first_effective_date',
            'name',
            'move_line_id',
            'member_id'
        ])
        nominal_amount = inversio['nshares']*gkwh.shareValue
        daysFromPayment = (isodate(date_invoice) - isodate(inversio['purchase_date'])).days

        if daysFromPayment < gkwh.waitDaysBeforeDivest:
            errors.append("%s: Too early to divest (< 30 days from purchase)" % inversio['name'])
            return

        invoice_id, error = Investment.create_divestment_invoice(cursor, uid, id,
            date_invoice, nominal_amount, 0, 0, 0)

        if error:
            errors.append(error)
            return

        Investment.open_invoices(cursor, uid, [invoice_id])
        Investment.invoices_to_payment_order(cursor, uid,
                [invoice_id], gkwh.amortizationPaymentMode)
        invoice_ids.append(invoice_id)

        #Get moveline id
        invoice_obj = Invoice.read(cursor, uid, invoice_id, [
            'move_id',
        ])
        ml_invoice = invoice_obj['move_id'][0]
        movementline_id = MoveLine.search(cursor, uid,
            [('move_id','=',invoice_obj['move_id'][0])])[0]

        inv = InvestmentState(user['name'], datetime.now(),
            log = inversio['log'],
            nominal_amount = nominal_amount,
            purchase_date = inversio['purchase_date'],
            amortized_amount = inversio['amortized_amount'],
            first_effective_date = inversio['first_effective_date'],
        )
        inv.divest(
            date = str(date_invoice),
            amount = nominal_amount,
            move_line_id = movementline_id,
        )
        Investment.write(cursor, uid, id, inv.erpChanges())

# vim: et ts=4 sw=4
