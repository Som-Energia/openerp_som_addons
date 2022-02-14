class power_prices():

    def get_data(self, cursor, uid, object, extra_text, context):
        tariff = 'error'
        if object.polissa_id:
            if object.polissa_id.tarifa.codi_ocsum in ('020', '021', '022', '023', '025'):
                tariff = '6xTD'
            elif object.polissa_id.tarifa.codi_ocsum in ('019', '024'):
                tariff = '3xTD'

        #return {'tariff': '3xTD'}
        return {'tariff': tariff}
