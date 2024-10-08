from osv import osv
from math import radians, cos, sin, asin, sqrt


def compute_haversine_distance(lat_gurb, long_gurb, lat_address, long_address):
    # Convert degrees to radians.
    long_address = radians(float(long_address))
    lat_address = radians(float(lat_address))

    long_gurb = radians(float(long_gurb))
    lat_gurb = radians(float(lat_gurb))

    # Haversine formula
    delta_long = long_address - long_gurb
    delta_lat = lat_address - lat_gurb
    hav = sin(delta_lat / 2)**2 + cos(lat_gurb) * cos(lat_address) * sin(delta_long / 2)**2

    # 6371 es el radi de la tierra en km
    return 2 * asin(sqrt(hav)) * 6371


class SomGurbWWW(osv.osv_memory):
    _name = "som.gurb.www"

    def get_open_gurbs(self, cursor, uid, context=None):
        if context is None:
            context = {}

        result = []

        gurb_obj = self.pool.get('som.gurb')

        search_params = [
            ('state', 'in', ['first_opening', 'reopened'])
        ]

        gurb_ids = gurb_obj.search(cursor, uid, search_params, context=context)

        if gurb_ids:
            read_params = [
                'id',
                'name',
                'state',
                'assigned_betas_kw',
                'assigned_betas_percentage',
                'available_betas_kw',
                'available_betas_percentage',
                'generation_power'
                'min_power',
                'max_power'
            ]

            result = gurb_obj.read(cursor, uid, gurb_ids, read_params, context=context)

        return result

    def check_cups_2km_validation(self, cursor, uid, cups, gurb_id, context=None):
        if context is None:
            context = {}

        cups_obj = self.pool.get('giscedata.cups.ps')
        som_gurb_obj = self.pool.get('som.gurb')

        search_params = [
            ('name', '=', cups),
        ]

        cups_id = cups_obj.search(cursor, uid, search_params, context=context)

        if not cups_id:
            raise Exception("No tenim el CUPS")

        cups_br = cups_obj.browse(cursor, uid, cups_id[0], context=context)
        gurb_br = som_gurb_obj.browse(cursor, uid, gurb_id, context=context)

        lat_gurb = gurb_br.coordenada_latitud
        long_gurb = gurb_br.coordenada_longitud
        lat_address = cups_br.coordenada_latitud
        long_address = cups_br.coordenada_longitud

        if not lat_address or long_address:
            raise Exception("No tenim les coordenades del CUPS")

        distance_from_gurb = compute_haversine_distance(
            lat_gurb, long_gurb, lat_address, long_address
        )

        return distance_from_gurb < 2.1

    def check_coordinates_2km_validation(
        self, cursor, uid, lat_address, long_address, gurb_id, context=None
    ):
        if context is None:
            context = {}

        som_gurb_obj = self.pool.get('som.gurb')

        gurb_br = som_gurb_obj.browse(cursor, uid, gurb_id, context=context)

        lat_gurb = gurb_br.coordenada_latitud
        long_gurb = gurb_br.coordenada_longitud

        distance_from_gurb = compute_haversine_distance(
            lat_gurb, long_gurb, lat_address, long_address
        )

        return distance_from_gurb < 2.1


SomGurbWWW()
