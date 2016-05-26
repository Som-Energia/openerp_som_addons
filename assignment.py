# -*- coding: utf-8 -*-

from osv import osv, fields
from .erpwrapper import ErpWrapper
import datetime
from yamlns import namespace as ns
from generationkwh.isodates import isodate

# TODO: sort rights sources if many members assigned the same contract
# TODO: Filter out inactive contracts

FF_CONTRACT_FIELDS = [
    ('contract_state', 'state'),
    ('contract_last_invoiced', 'data_ultima_lectura'),
    ('cups_direction', 'cups_direccio'),
]


# TODO: This function is duplicated in other sources
def _sqlfromfile(sqlname):
    from tools import config
    import os
    sqlfile = os.path.join(
        config['addons_path'], 'som_generationkwh',
            'sql', sqlname+'.sql')
    with open(sqlfile) as f:
        return f.read()


class GenerationkWhAssignment(osv.osv):

    _name = 'generationkwh.assignment'
    _order = 'member_id, priority, contract_id'

    def _ff_contract(self, cursor, uid, ids, field_names, args, context=None):
        """  Function to read contract values from function fields"""
        contract_obj = self.pool.get('giscedata.polissa')
        cups_obj = self.pool.get('giscedata.cups.ps')

        if not isinstance(ids, (tuple, list)):
            ids = [ids]

        init_dict = dict([(f, False) for f in field_names])
        res = {}.fromkeys(ids, {})
        for k in res.keys():
            res[k] = init_dict.copy()

        for assigment_vals in self.read(cursor, uid, ids, ['contract_id']):
            assignment_id = assigment_vals['id']
            contract_id = assigment_vals['contract_id'][0]
            contract_fields = ['cups', 'state', 'data_ultima_lectura',
                               'cups_direccio']
            contract_vals = contract_obj.read(
                cursor, uid, contract_id, contract_fields
            )
            if 'cups_anual_use' in field_names:
                cups_id = contract_vals['cups'][0]
                cups_vals = cups_obj.read(cursor, uid, cups_id, ['conany_kwh'])
                res[assignment_id]['cups_anual_use'] = cups_vals['conany_kwh']

            for field, contract_field in FF_CONTRACT_FIELDS:
                if field in field_names:
                    res[assignment_id][field] = contract_vals[contract_field]

        return res

    _columns = dict(
        contract_id=fields.many2one(
            'giscedata.polissa',
            'Contracte',
            required=True,
            help="Contracte que te els drets per utilitzar els kWh generats",
            ),
        member_id=fields.many2one(
            'somenergia.soci',
            'Soci',
            required=True,
            help="Soci que va comprar accions Generation kWh i els assigna",
            ),
        priority=fields.integer(
            'Prioritat',
            required=True,
            help="Ordre d'assignacions. "
                 "Aquesta assignació no usara drets generats en els dates que"
                 "encara no han estat facturades a assignacions del mateix soci"
                 " que tinguin una prioritat mes alta."
                 "(a valor més petit, més prioritat",
            ),
        end_date=fields.date(
            "Data d'Expiració",
            help="Data a partir de la qual l'assignació ja no serà activa",
            ),
        # Contract fields
        contract_state=fields.function(
            _ff_contract, string='Contract State', readonly=True, type='char',
            method=True, multi='contract',
            help="Estat del contracte seleccionat",
            ),
        contract_last_invoiced=fields.function(
            _ff_contract, string='Data última factura', readonly=True,
            type='date', method=True, multi='contract',
            help="Data Última lectura facturada",
            ),
        cups_direction=fields.function(
            _ff_contract, string='Direcció CUPS', readonly=True, type='char',
            method=True, multi='contract',
            help="Direcció del CUPS",
            ),
        # Contract fields
        cups_anual_use=fields.function(
            _ff_contract, string='Consum anual', readonly=True, type='integer',
            method=True, multi='contract',
            help="Consum anyal del CUPS. Pot ser estimat.",
            ),
        )

    def create(self, cr, uid, values, context=None):
        self.expire(cr, uid,
            values.get('contract_id',None),
            values.get('member_id',None),
            context=context)
        return super(GenerationkWhAssignment, self).create(cr, uid, values, context=context)

    def expire(self, cr, uid, contract_id, member_id, context=None):
        if contract_id is None: return
        if member_id is None: return
        same_polissa_member = self.search(cr, uid, [
            #'|', ('end_date', '<', str(datetime.date.today())),
                ('end_date','=',False),
            ('contract_id', '=', contract_id),
            ('member_id', '=', member_id),
        ], context = context)
        if same_polissa_member:
            self.write(cr,uid,
                same_polissa_member,
                dict(
                    end_date=str(datetime.date.today()),
                ),
                context=context,
            )

    def createDefaultForMembers(self, cr, uid, member_ids, context=None):
        """ Creates default contract assignments for the given members.
        """
        contracts = self.sortedDefaultContractsForMember(cr, uid, member_ids, context)
        self.createOnePrioritaryAndManySecondaries(cr, uid, contracts, context)

    def sortedDefaultContractsForMember(self, cr, uid, member_ids, context=None):
        """ PRIVATE.
            Gets default contract to assign for a given member ids
            Criteria are:
            - Contracts the member being the payer first,
              then the ones the member is owner but not payer.
            - Within both groups the ones with more anual use first.
            - If all criteria match, use contract creation order
        """
        if not member_ids: return []
        sql = _sqlfromfile('default_contracts_to_assign')
        cr.execute(sql, dict(socis=tuple(member_ids)))
        return [
            (contract,member)
            for contract,member,_,_ in cr.fetchall()
            if contract
            ]

    def createOnePrioritaryAndManySecondaries(self, cr, uid, assignments, context=None):
        """ PRIVATE.
            Creates assignments from a list of pairs of contract_id, member_id.
            The first pair of a member is the priority 0 and the 
            remaining contracts of the same member are inserted as priority zero.
            @pre contracts of the same member are together
            """
        formerMember=None
        members = list(set(member for contract,member in assignments))
        ids = self.search(cr, uid, [
            ('member_id','in',members),
            ],context=context)
        self.unlink(cr, uid, ids, context=context)
        for contract, member in assignments:
            self.create(cr, uid, dict(
                contract_id = contract,
                member_id = member,
                priority = 0 if member!=formerMember else 1,
                ), context=context)
            formerMember=member
    
    def dropAll(self, cr, uid, context=None):
        """Remove all records"""
        ids = self.search(cr, uid, [
            ],context=context)
        for a in self.browse(cr, uid, ids, context=context):
            a.unlink()

    def anyForContract(self, cursor, uid, contract_id, context=None):
        return len(self.search(
            cursor,
            uid,
            [
                ('contract_id','=',contract_id),
                ('end_date','=',False),
            ], context=context
            ))>=1

    def contractSources(self, cursor, uid, contract_id, context=None):
        sql = _sqlfromfile('right_sources_for_contract')
        cursor.execute(sql, dict(contract_id=contract_id))
        return [
            (member_id, last_usable_date)
            for member_id, last_usable_date, _
            in cursor.fetchall()
            ]
        


    def unassignedInvestors(self, cursor, uid, context=None):
        """Returns all the members that have investments but no assignment"""
        cursor.execute("""
            SELECT
                investment.member_id AS id
            FROM
                generationkwh_investment AS investment
            LEFT JOIN
                generationkwh_assignment AS assignment
                ON assignment.member_id = investment.member_id
            WHERE
                assignment.id IS NULL
            GROUP BY
                investment.member_id
            ORDER BY
                investment.member_id
            """)
        result = [ id for id, in cursor.fetchall() ]
        return result


GenerationkWhAssignment()


class AssignmentProvider(ErpWrapper):

    def contractSources(self, contract_id):
        """
            Returns the sources available GenkWh rights sources for a contract
            and the earliest date you can use rights from it.
        """
        Assignment = self.erp.pool.get('generationkwh.assignment')
        return [
            ns(
                member_id=member_id,
                last_usable_date=isodate(last_usable_date),
            )
            for member_id, last_usable_date
            in Assignment.contractSources(
                self.cursor, self.uid,
                contract_id,
                context=self.context)
            ]

    def anyForContract(self, contract_id):
        Assignment = self.erp.pool.get('generationkwh.assignment')
        return Assignment.anyForContract(
            self.cursor, self.uid,
            contract_id,
            context=self.context,
            )

class Generationkwh_Assignment_TestHelper(osv.osv):
    _name = 'generationkwh.assignment.testhelper'
    _auto = False
    
    def contractSources(self, cursor, uid, contract_id, context=None):
        provider = AssignmentProvider(self, cursor, uid, context)
        return [
            dict(
                member_id=val.member_id,
                last_usable_date=val.last_usable_date.isoformat(),
                )
            for val in provider.contractSources(contract_id)
            ]

Generationkwh_Assignment_TestHelper()





