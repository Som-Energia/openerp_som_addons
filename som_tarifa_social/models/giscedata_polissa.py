# -*- coding: utf-8 -*-
from som_polissa.exceptions import exceptions

from osv import osv


class GiscedataPolissa(osv.osv):

    def get_pricelist_from_tariff_and_location_no_social(
            self, cursor, uid, mode_facturacio, id_municipi, context=None):
        imd_obj = self.pool.get("ir.model.data")

        # Tarifes normals
        pp_periodes_peninsula_id = imd_obj.get_object_reference(
            cursor, uid, "som_indexada", "pricelist_periodes_20td_peninsula"
        )[1]
        pp_periodes_insular_id = imd_obj.get_object_reference(
            cursor, uid, "som_indexada", "pricelist_periodes_20td_insular"
        )[1]
        pp_indexada_peninsula_id = imd_obj.get_object_reference(
            cursor, uid, "som_indexada", "pricelist_indexada_20td_peninsula"
        )[1]
        pp_indexada_balears_id = imd_obj.get_object_reference(
            cursor, uid, "som_indexada", "pricelist_indexada_20td_balears"
        )[1]
        pp_indexada_canaries_id = imd_obj.get_object_reference(
            cursor, uid, "som_indexada", "pricelist_indexada_20td_canaries"
        )[1]

        location = self._get_tariff_zone_from_location(cursor, uid, id_municipi)

        new_pricelist_id = 0
        if mode_facturacio == 'index':
            if location == 'peninsula':
                new_pricelist_id = pp_indexada_peninsula_id
            elif location == 'balears':
                new_pricelist_id = pp_indexada_balears_id
            elif location == 'canaries':
                new_pricelist_id = pp_indexada_canaries_id
        elif mode_facturacio == 'atr':
            if location == 'peninsula':
                new_pricelist_id = pp_periodes_peninsula_id
            elif location == 'insular':
                new_pricelist_id = pp_periodes_insular_id

        return new_pricelist_id

    def mapping_tarifa_social(self, cursor, uid, context=None):
        imd_obj = self.pool.get("ir.model.data")

        # Tarifes normals
        pp_periodes_peninsula_id = imd_obj.get_object_reference(
            cursor, uid, "som_indexada", "pricelist_periodes_20td_peninsula"
        )[1]
        pp_periodes_insular_id = imd_obj.get_object_reference(
            cursor, uid, "som_indexada", "pricelist_periodes_20td_insular"
        )[1]
        pp_indexada_peninsula_id = imd_obj.get_object_reference(
            cursor, uid, "som_indexada", "pricelist_indexada_20td_peninsula"
        )[1]
        pp_indexada_balears_id = imd_obj.get_object_reference(
            cursor, uid, "som_indexada", "pricelist_indexada_20td_balears"
        )[1]
        pp_indexada_canaries_id = imd_obj.get_object_reference(
            cursor, uid, "som_indexada", "pricelist_indexada_20td_canaries"
        )[1]
        # Tarifes socials
        pp_social_periodes_id = imd_obj.get_object_reference(
            cursor, uid, "www_som", "tarifa_20TD_SOM_SOCIAL"
        )[1]
        pp_social_periodes_insular_id = imd_obj.get_object_reference(
            cursor, uid, "www_som", "tarifa_20TD_SOM_INSULAR_SOCIAL"
        )[1]
        pp_social_indexada_id = imd_obj.get_object_reference(
            cursor, uid, "www_som", "tarifa_indexada_20TD_peninsula_social"
        )[1]
        pp_social_indexada_balears_id = imd_obj.get_object_reference(
            cursor, uid, "www_som", "tarifa_indexada_20TD_balears_social"
        )[1]
        pp_social_indexada_canaries_id = imd_obj.get_object_reference(
            cursor, uid, "www_som", "tarifa_indexada_20TD_canaries_social"
        )[1]

        return {
            pp_periodes_peninsula_id: pp_social_periodes_id,
            pp_periodes_insular_id: pp_social_periodes_insular_id,
            pp_indexada_peninsula_id: pp_social_indexada_id,
            pp_indexada_balears_id: pp_social_indexada_balears_id,
            pp_indexada_canaries_id: pp_social_indexada_canaries_id,
        }

    def mapping_tarifa_no_social(self, cursor, uid, polissa_id, context=None):

        polissa = self.browse(cursor, uid, polissa_id, context=context)
        new_pricelist_id = self.get_pricelist_from_tariff_and_location_no_social(
            cursor, uid, polissa.mode_facturacio,
            polissa.cups.id_municipi.id, context)

        return new_pricelist_id

    def get_new_tariff_change_social_or_regular(self, cursor, uid, polissa_id, change_type, context):  # noqa E501
        """Donada una pòlissa i un tipus de canvi, retorna la nova tarifa a assignar.
        """
        polissa = self.browse(cursor, uid, polissa_id, context=context)

        if change_type == "to_social":
            new_pricelist_dict = self.mapping_tarifa_social(cursor, uid, context=context)
            if not new_pricelist_dict.get(polissa.llista_preu.id, False):
                raise exceptions.PolissaCannotChangeSocialTariff(polissa.name, change_type)
            new_pricelist_id = new_pricelist_dict[polissa.llista_preu.id]
        elif change_type == "to_regular":
            new_pricelist_id = self.mapping_tarifa_no_social(
                cursor, uid, polissa_id, context=context)
            if not new_pricelist_id:
                raise exceptions.PolissaCannotChangeSocialTariff(polissa.name, change_type)
        else:
            raise exceptions.PolissaCannotChangeSocialTariff(polissa.name, change_type)
        return new_pricelist_id


GiscedataPolissa()
