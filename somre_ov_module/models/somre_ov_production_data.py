# -*- coding: utf-8 -*-
from osv import osv


from .decorators import www_entry_point
from .exceptions import (
    NoSuchUser,
    UnauthorizedAccess,
    ContractNotExists,
)
from addons import get_module_resource


class SomreOvProductionData(osv.osv_memory):

    _name = "somre.ov.production.data"

    @www_entry_point((
        NoSuchUser,
    ))
    def measures(
        self, cursor, uid,
        username,
        first_timestamp_utc,
        last_timestamp_utc,
        context=None
    ):

        if context is None:
            context = {}

        contracts = self._get_user_contracts(cursor, uid, username, context)

        measures = {'data': []}
        for contract in contracts:
            contract_data = self._get_production_measures(
                cursor, contract, first_timestamp_utc, last_timestamp_utc)[0][0]
            contract_data['foreseen_kwh'] = self._get_forecast_measures(
                cursor, uid, contract.cil.id, first_timestamp_utc, last_timestamp_utc, context)
            measures['data'].append(contract_data)

        return measures

    @www_entry_point((
        NoSuchUser,
        UnauthorizedAccess,
        ContractNotExists,
    ))
    def measures_single_installation(
        self, cursor, uid,
        username,
        contract_number,
        first_timestamp_utc,
        last_timestamp_utc,
        context=None
    ):

        if context is None:
            context = {}

        contract = self._get_user_contract(cursor, uid, username, contract_number)

        measures = {'data': []}
        contract_data = self._get_production_measures(
            cursor, contract, first_timestamp_utc, last_timestamp_utc)[0][0]
        contract_data['foreseen_kwh'] = self._get_forecast_measures(
            cursor, uid, contract.cil.id, first_timestamp_utc, last_timestamp_utc, context)
        measures['data'].append(contract_data)

        return measures

    def _get_user_contract(self, cursor, uid, username, contract_number):
        polissa_obj = self.pool.get('giscere.polissa')
        contract_id = polissa_obj.search(cursor, uid, [('name', '=', contract_number)])
        if not contract_id:
            raise ContractNotExists()
        contract = polissa_obj.browse(cursor, uid, contract_id[0])

        if contract.titular_nif != username:
            raise UnauthorizedAccess(
                username=username,
                resource_type='Contract',
                resource_name=contract_number,
            )
        return contract

    def _get_user_contracts(self, cursor, uid, username, context):
        installation_obj = self.pool.get('somre.ov.installations')
        return installation_obj.get_user_contracts(cursor, uid, username, context)

    def _get_forecast_measures(self, cursor, uid, cil_id, first_timestamp_utc, last_timestamp_utc, context):  # noqa: E501
        installation_obj = self.pool.get('giscere.instalacio')
        installation_id = installation_obj.search(cursor, uid, [('cil', '=', cil_id)])
        installation = installation_obj.browse(cursor, uid, installation_id)[0]
        forecast_code = installation.codi_previsio or "NOT_EXISTING_PLANT"
        query_file = get_module_resource(
            'somre_ov_module', 'sql', "get_forecast_measures.sql")
        query = open(query_file).read()
        cursor.execute(
            query,
            {
                'forecast_code': forecast_code,
                'first_timestamp_utc': first_timestamp_utc,
                'last_timestamp_utc': last_timestamp_utc
            }
        )
        return cursor.fetchone()[0]

    def _get_production_measures(self, cursor, contract, first_timestamp_utc, last_timestamp_utc, quartihour=False):  # noqa: E501
        if quartihour:
            sql_file = "get_production_measures_qh.sql"
        else:
            sql_file = "get_production_measures.sql"
        query_file = get_module_resource('somre_ov_module', 'sql', sql_file)
        query = open(query_file).read()

        cursor.execute(
            query,
            {
                'cil': contract.cil.name,
                'contract_name': contract.name,
                'first_timestamp_utc': first_timestamp_utc,
                'last_timestamp_utc': last_timestamp_utc
            }
        )
        return cursor.fetchall()


SomreOvProductionData()
