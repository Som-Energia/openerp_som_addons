# -*- coding: utf-8 -*-
from erpwrapper import ErpWrapper
from generationkwh.isodates import isodate
import generationkwh.investmentmodel as gkwh
from generationkwh.investmentstate import InvestmentState
from datetime import datetime, date

class PartnerException(Exception):
    pass
class InvestmentException(Exception):
    pass

class InvestmentActions(ErpWrapper):

    def create_from_form(self, cursor, uid, partner_id, order_date, amount_in_euros, ip, iban,
            emission=None, context=None):
        GenerationkwhInvestment = self.erp.pool.get('generationkwh.investment')

        if amount_in_euros <= 0 or amount_in_euros % gkwh.shareValue > 0:
                raise InvestmentException("Invalid amount")
        iban = GenerationkwhInvestment.check_iban(cursor, uid, iban)

        if not iban:
                raise PartnerException("Wrong iban")
        if not emission:
            emission = 'emissio_genkwh'

        imd_model = self.erp.pool.get('ir.model.data')
        emission_id = imd_model.get_object_reference(
            cursor, uid, 'som_generationkwh', emission
        )[1]
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

class GenerationkwhActions(InvestmentActions):

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


class AportacionsActions(InvestmentActions):

    def create_from_form(self, cursor, uid, partner_id, order_date, amount_in_euros, ip, iban, emission=None, context=None):
        member_ids, emission_id = super(AportacionsActions, self).create_from_form(cursor, uid, partner_id, order_date, amount_in_euros, ip, iban,emission, context)

        GenerationkwhInvestment = self.erp.pool.get('generationkwh.investment')

        if not emission:
            emission = 'emissio_apo'
        IrModelData = self.erp.pool.get('ir.model.data')
        Emission = self.erp.pool.get('generationkwh.emission')
        emission_id = IrModelData.get_object_reference(
            cursor, uid, 'som_generationkwh', emission
        )[1]
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

# vim: et ts=4 sw=4
