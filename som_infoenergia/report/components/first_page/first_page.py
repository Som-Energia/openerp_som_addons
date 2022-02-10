class first_page():

    def get_data(self, cursor, uid, object, extra_text, context):
        return {'nom_titular': object.partner_id.name}