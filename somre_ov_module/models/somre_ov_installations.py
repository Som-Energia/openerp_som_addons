# -*- coding: utf-8 -*-
from osv import osv
import logging

from decorators import www_entry_point

from exceptions import (
    ContractWithoutInstallation,
    ContractNotExists,
    UnauthorizedAccess,
    NoSuchUser,
)

logger = logging.getLogger(__name__)


class SomreOvInstallations(osv.osv_memory):

    _name = 'somre.ov.installations'

    @www_entry_point(
        expected_exceptions=(
            NoSuchUser,
        )
    )
    def get_installations(self, cursor, uid, vat, context=None):
        contracts = self.get_user_contracts(cursor, uid, vat, context)

        return [
            dict(
                contract_number=contract.name,
                installation_name=installation_name,
            )
            for contract, installation_name in (
                (contract, self._get_installation_name_by_cil(cursor, uid, contract.cil.id))
                for contract in contracts
            )
            if installation_name
        ]

    def get_user_contracts(self, cursor, uid, vat, context):
        if context is None:
            context = {}

        users_obj = self.pool.get('somre.ov.users')
        partner = users_obj.get_customer(cursor, uid, vat)
        polissa_obj = self.pool.get('giscere.polissa')
        search_params = [
            ('titular', '=', partner.id),
            ('state', '=', 'activa'),
        ]

        contract_ids = polissa_obj.search(cursor, uid, search_params)
        if not contract_ids:
            return []

        return polissa_obj.browse(cursor, uid, contract_ids)

    @www_entry_point(
        expected_exceptions=(
            ContractWithoutInstallation,
            ContractNotExists,
            UnauthorizedAccess,
        )
    )
    def get_installation_details(self, cursor, uid, vat, contract_number, context=None):
        polissa_obj = self.pool.get('giscere.polissa')
        contract_search_params = [
            ('name', '=', contract_number),
            ('state', '=', 'activa'),
        ]
        contract_id = polissa_obj.search(cursor, uid, contract_search_params)
        if not contract_id:
            raise ContractNotExists()

        contract = polissa_obj.browse(cursor, uid, contract_id)[0]

        users_obj = self.pool.get('somre.ov.users')
        partner = users_obj.get_customer(cursor, uid, vat)
        if partner.id != contract.titular.id:
            raise UnauthorizedAccess(
                username=vat,
                resource_type='Contract',
                resource_name=contract_number,
            )

        contract_details = dict(
            billing_mode=contract.mode_facturacio,
            proxy_fee=contract.representant_fee,
            cost_deviation=contract.desvios,
            reduction_deviation=contract.efecte_cartera,
            representation_type=contract.representation_type,
            iban=self._format_iban(contract.bank.printable_iban),
            discharge_date=contract.data_alta,
            status=contract.state,
        )

        installation_obj = self.pool.get('giscere.instalacio')
        installation_search_params = [
            ('cil', '=', contract.cil.id),
        ]
        installation_id = installation_obj.search(cursor, uid, installation_search_params)
        if not installation_id:
            raise ContractWithoutInstallation(contract_number)

        installation = installation_obj.browse(cursor, uid, installation_id)[0]
        installation_details = dict(
            contract_number=contract_number,
            name=installation.name,
            address=installation.cil.direccio,
            city=installation.cil.id_municipi.name,
            postal_code=installation.cil.dp,
            province=installation.cil.id_provincia.name,
            coordinates=self._format_coordinates(installation),
            technology=installation.subgrup,
            cil=installation.cil.name,
            rated_power=installation.potencia_nominal,
            type=installation.tipo,
            ministry_code=installation.codigo_ministerio,
        )

        return dict(
            installation_details=installation_details,
            contract_details=contract_details
        )

    def _format_coordinates(self, installation):
        coordinates = None
        if installation.utm_x and installation.utm_y:
            coordinates = installation.utm_x.replace(
                ',', '.') + ',' + installation.utm_y.replace(',', '.')
        return coordinates

    def _format_iban(self, iban):
        """Hide all but the last 4 digits of an IBAN number"""
        return '**** **** **** **** **** {}'.format(iban[-4:])

    def _get_contract_number(self, cursor, uid, partner_id, context=None):
        if context is None:
            context = {}

        polissa_obj = self.pool.get('giscere.polissa')
        search_params = [
            ('titular', '=', partner_id),
        ]
        contract_id = polissa_obj.search(cursor, uid, search_params)
        if not contract_id:
            raise ContractNotExists()
        contract = polissa_obj.browse(cursor, uid, contract_id)[0]
        return contract.name

    def _get_installation_name_by_cil(self, cursor, uid, cil_id):
        installation_obj = self.pool.get('giscere.instalacio')
        search_params = [
            ('cil', '=', cil_id),
        ]
        installation_ids = installation_obj.search(cursor, uid, search_params)
        installations = installation_obj.read(cursor, uid, installation_ids, ['name'])
        if not installations:
            logger.error('No installation with this cil {}'.format(cil_id))
            return None
        return installations[0]['name']


SomreOvInstallations()
